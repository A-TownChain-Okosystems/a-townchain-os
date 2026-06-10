"""
Federated Learning — Issue #29 (Kap. 41)
On-Chain koordiniertes Federated Learning für AI-Agents (L3).
"""
import hashlib, time, json
from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class FLModel:
    id:          str
    name:        str
    version:     str
    creator:     str
    architecture: dict     # Model-Config (Schichten, Hyperparameter)
    cid:         str = ""  # IPFS CID der Gewichte
    accuracy:    float = 0.0
    created:     float = field(default_factory=time.time)

@dataclass
class FLRound:
    round_id:    int
    model_id:    str
    participants: List[str] = field(default_factory=list)
    updates:     Dict[str, str] = field(default_factory=dict)  # node → weight_cid
    aggregated:  Optional[str] = None  # Aggregiertes Modell CID
    started:     float = field(default_factory=time.time)
    completed:   Optional[float] = None

class FederatedLearningCoordinator:
    """
    On-Chain Federated Learning Coordinator (ATAI-FED-1000).
    - Koordiniert verteiltes Training über mehrere Nodes
    - Gewichte werden nie zentralisiert (nur CIDs)
    - FedAvg Aggregation (Simulation)
    - Reward-System für Teilnehmer
    """
    MIN_PARTICIPANTS = 3
    REWARD_PER_ROUND = 10.0  # ATC pro Teilnehmer

    def __init__(self):
        self._models:    Dict[str, FLModel] = {}
        self._rounds:    List[FLRound]      = []
        self._balances:  Dict[str, float]   = {}
        self._round_ctr = 0

    def register_model(self, model: FLModel) -> str:
        cid = hashlib.sha256(f"{model.name}{model.version}{time.time()}".encode()).hexdigest()[:32]
        model.cid = cid
        self._models[model.id] = model
        return cid

    def start_round(self, model_id: str) -> FLRound:
        if model_id not in self._models:
            raise ValueError(f"Modell {model_id} nicht gefunden")
        self._round_ctr += 1
        rnd = FLRound(round_id=self._round_ctr, model_id=model_id)
        self._rounds.append(rnd)
        return rnd

    def submit_update(self, round_id: int, node_id: str, weight_cid: str) -> bool:
        rnd = next((r for r in self._rounds if r.round_id == round_id), None)
        if not rnd: raise ValueError("Runde nicht gefunden")
        if node_id not in rnd.participants:
            rnd.participants.append(node_id)
        rnd.updates[node_id] = weight_cid
        return True

    def aggregate(self, round_id: int) -> Optional[str]:
        rnd = next((r for r in self._rounds if r.round_id == round_id), None)
        if not rnd: return None
        if len(rnd.participants) < self.MIN_PARTICIPANTS:
            return None
        # FedAvg Simulation: CID aus allen Updates ableiten
        combined = "".join(sorted(rnd.updates.values()))
        agg_cid  = hashlib.sha256(combined.encode()).hexdigest()[:32]
        rnd.aggregated = agg_cid
        rnd.completed  = time.time()
        # Rewards auszahlen
        for participant in rnd.participants:
            self._balances[participant] =                 self._balances.get(participant, 0.0) + self.REWARD_PER_ROUND
        return agg_cid

    def stats(self) -> dict:
        return {
            "models":       len(self._models),
            "rounds":       len(self._rounds),
            "completed":    sum(1 for r in self._rounds if r.completed),
            "total_rewards": sum(self._balances.values()),
            "min_participants": self.MIN_PARTICIPANTS,
        }
