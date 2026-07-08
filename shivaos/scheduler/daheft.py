"""
ShivaCore Kernel — DA-HEFT Scheduler (Deadline-Aware Heterogeneous
Earliest-Finish-Time). Milestone 08.07.2026.

WICHTIG: Dieser Scheduler kennt NUR das Accelerator-Interface aus
accelerator.py. Ob dahinter eine SimulatedAccelerator (heute, diese
Sandbox) oder eine echte Hardware-Implementierung steckt, ist fuer den
Algorithmus unsichtbar. Wird spaeter eine echte GPU/NPU-Anbindung
geschrieben, funktioniert dieser Code unveraendert weiter.

Algorithmus (vereinfachte, aber echte Umsetzung von HEFT + Deadline-
Admission-Control + Energie-Optimierung, wie skizziert):
  1. Priorisierung: upward rank (kritischer Pfad) je Knoten im Task-Graph,
     geschaetzt ueber den Durchschnitt der Ausfuehrungszeiten aller
     unterstuetzenden Beschleuniger.
  2. Reihenfolge: absteigend nach Prioritaet, aber nur wenn alle
     Vorgaenger im Graph bereits eingeplant sind (topologische Ordnung).
  3. Fuer jeden Knoten: EFT je in Frage kommendem (thermisch verfuegbarem,
     Operator-unterstuetzendem) Beschleuniger berechnen.
  4. Deadline-Admission-Control: wenn eine Deadline existiert, werden nur
     Beschleuniger zugelassen, die sie einhalten -- sonst bester Kompromiss
     (Degradation, klar markiert).
  5. Unter den zulaessigen: minimales EFT * Energie waehlen.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from shivaos.scheduler.accelerator import Accelerator, OperatorNode, ExecutionResult


class SchedulingError(Exception):
    pass


@dataclass
class Task:
    task_id: str
    nodes: List[OperatorNode]
    edges: Dict[str, List[str]] = field(default_factory=dict)  # node_id -> [predecessor_node_ids]
    deadline_s: Optional[float] = None


@dataclass
class ScheduleEntry:
    task_id: str
    node_id: str
    accel_id: str
    predicted_start_s: float
    predicted_end_s: float
    deadline_met: Optional[bool]  # None = keine Deadline gesetzt


class DAHEFTScheduler:
    def __init__(self, accelerators: List[Accelerator]):
        if not accelerators:
            raise SchedulingError("Mindestens ein Beschleuniger noetig")
        self.accelerators = {a.accel_id: a for a in accelerators}

    def _upward_rank(self, task: Task) -> Dict[str, float]:
        """Kritischer-Pfad-Prioritaet: Knoten mit vielen/teuren Nachfolgern
        zuerst. Rueckwaerts durch den Graph (von Senken zu Quellen)."""
        node_by_id = {n.node_id: n for n in task.nodes}
        successors: Dict[str, List[str]] = {n.node_id: [] for n in task.nodes}
        for node_id, preds in task.edges.items():
            for p in preds:
                successors.setdefault(p, []).append(node_id)

        avg_cost: Dict[str, float] = {}
        for n in task.nodes:
            times = []
            for acc in self.accelerators.values():
                if n.op_type in acc.supported_ops():
                    try:
                        times.append(acc.estimated_exec_time(n))
                    except Exception:
                        pass
            avg_cost[n.node_id] = sum(times) / len(times) if times else 0.0

        rank: Dict[str, float] = {}

        def compute(node_id: str) -> float:
            if node_id in rank:
                return rank[node_id]
            succ = successors.get(node_id, [])
            max_succ_rank = max((compute(s) for s in succ), default=0.0)
            rank[node_id] = avg_cost[node_id] + max_succ_rank
            return rank[node_id]

        for n in task.nodes:
            compute(n.node_id)
        return rank

    def plan(self, tasks: List[Task]) -> List[ScheduleEntry]:
        """Berechnet einen Schedule-Plan OHNE etwas auszufuehren --
        reine Entscheidung, wer wann auf welchem Beschleuniger laeuft."""
        entries: List[ScheduleEntry] = []
        virtual_busy_until: Dict[str, float] = {
            aid: acc.queue_free_time() for aid, acc in self.accelerators.items()
        }
        node_end_time: Dict[str, float] = {}

        for task in tasks:
            rank = self._upward_rank(task)
            node_by_id = {n.node_id: n for n in task.nodes}
            ordered = sorted(task.nodes, key=lambda n: rank[n.node_id], reverse=True)
            scheduled = set()

            remaining = list(ordered)
            while remaining:
                progressed = False
                for n in list(remaining):
                    preds = task.edges.get(n.node_id, [])
                    if not all(p in scheduled for p in preds):
                        continue  # Vorgaenger noch nicht eingeplant

                    ready_time = max((node_end_time[p] for p in preds), default=0.0)
                    candidates = []
                    for aid, acc in self.accelerators.items():
                        if n.op_type not in acc.supported_ops():
                            continue
                        if not acc.is_thermally_available():
                            continue
                        exec_t = acc.estimated_exec_time(n)
                        energy = acc.estimated_energy(n)
                        eft = max(ready_time, virtual_busy_until[aid]) + exec_t
                        candidates.append((aid, eft, energy, exec_t))

                    if not candidates:
                        raise SchedulingError(
                            f"Kein verfuegbarer Beschleuniger fuer Knoten {n.node_id} "
                            f"({n.op_type}) -- alle ungeeignet oder ueberhitzt"
                        )

                    deadline_met = None
                    pool = candidates
                    if task.deadline_s is not None:
                        deadline_met = True
                        admissible = [c for c in candidates if c[1] <= task.deadline_s]
                        if admissible:
                            pool = admissible
                        else:
                            deadline_met = False  # Degradation: bester Kompromiss

                    best = min(pool, key=lambda c: c[1] * max(c[2], 1e-9))
                    aid, eft, energy, exec_t = best
                    start = eft - exec_t

                    entries.append(ScheduleEntry(
                        task_id=task.task_id, node_id=n.node_id, accel_id=aid,
                        predicted_start_s=start, predicted_end_s=eft,
                        deadline_met=deadline_met,
                    ))
                    virtual_busy_until[aid] = eft
                    node_end_time[n.node_id] = eft
                    scheduled.add(n.node_id)
                    remaining.remove(n)
                    progressed = True

                if not progressed:
                    raise SchedulingError(
                        f"Zyklische oder unerfuellbare Abhaengigkeit in Task {task.task_id}"
                    )
        return entries

    def execute(self, tasks: List[Task]) -> List[ExecutionResult]:
        """Plant UND fuehrt tatsaechlich aus (ruft accel.run_operator auf,
        respektiert Abhaengigkeitsreihenfolge). Funktioniert identisch mit
        SimulatedAccelerator heute und einer echten Hardware-Implementierung
        spaeter -- ohne Aenderung an dieser Methode."""
        plan = self.plan(tasks)
        # In der von plan() bestimmten Reihenfolge tatsaechlich ausfuehren:
        plan_sorted = sorted(plan, key=lambda e: e.predicted_start_s)
        node_lookup = {(t.task_id, n.node_id): n for t in tasks for n in t.nodes}
        results = []
        for entry in plan_sorted:
            node = node_lookup[(entry.task_id, entry.node_id)]
            acc = self.accelerators[entry.accel_id]
            result = acc.run_operator(node)
            results.append(result)
        return results
