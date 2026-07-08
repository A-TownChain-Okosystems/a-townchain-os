"""
ShivaCore Kernel — Beschleuniger-Abstraktion (Hardware-Interface)
Milestone 08.07.2026

Design-Ziel: Der DA-HEFT-Scheduler (siehe scheduler.py) kennt NUR dieses
Interface, nie eine konkrete Implementierung. Damit funktioniert er
unveraendert mit:
  - SimulatedAccelerator (heute, in dieser Sandbox -- kein echtes Silizium)
  - einer spaeteren echten Implementierung (z.B. ONNXRuntimeAccelerator,
    CudaAccelerator, NpuVendorSdkAccelerator) -- muss nur dieses Interface
    implementieren, KEINE Aenderung am Scheduler-Code noetig.

Das ist der uebliche Weg, "spaeter echte Hardware" zu ermoeglichen ohne
heute etwas vorzutaeuschen: sauberer Interface-Schnitt statt Behauptung.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Set, Optional


class OperatorType(Enum):
    MATMUL = auto()
    CONV2D = auto()
    RELU = auto()
    GENERIC = auto()


@dataclass(frozen=True)
class OperatorNode:
    """Ein Knoten im Task-Graph. shape_hint ist optional und dient
    Implementierungen zur Laufzeit-/Energieschaetzung."""
    node_id: str
    op_type: OperatorType
    shape_hint: tuple = field(default_factory=tuple)


@dataclass(frozen=True)
class ExecutionResult:
    node_id: str
    accel_id: str
    exec_time_s: float
    energy_j: float
    success: bool = True
    error: Optional[str] = None


class AcceleratorError(Exception):
    pass


class Accelerator(ABC):
    """Hardware-agnostisches Interface. JEDE Implementierung (simuliert
    oder real) MUSS diese Methoden bereitstellen. Der Scheduler ruft
    ausschliesslich diese Methoden auf -- nie hardwarespezifischen Code."""

    @property
    @abstractmethod
    def accel_id(self) -> str:
        ...

    @abstractmethod
    def supported_ops(self) -> Set[OperatorType]:
        """Welche Operator-Typen kann dieser Beschleuniger ausfuehren?"""

    @abstractmethod
    def estimated_exec_time(self, op: OperatorNode) -> float:
        """Geschaetzte/gemessene Ausfuehrungszeit in Sekunden."""

    @abstractmethod
    def estimated_energy(self, op: OperatorNode) -> float:
        """Geschaetzter/gemessener Energieverbrauch in Joule."""

    @abstractmethod
    def current_temperature_c(self) -> float:
        """Aktuelle Temperatur in Grad Celsius (aus echtem Sensor bei
        realer Hardware, aus einem Modell bei der Simulation)."""

    @abstractmethod
    def thermal_limit_c(self) -> float:
        """Temperatur-Schwelle, ab der dieser Beschleuniger fuer neue
        Aufgaben gesperrt wird."""

    @abstractmethod
    def queue_free_time(self) -> float:
        """Relative Zeit (Sekunden ab jetzt), ab der dieser Beschleuniger
        wieder frei fuer neue Operatoren ist."""

    @abstractmethod
    def run_operator(self, op: OperatorNode) -> ExecutionResult:
        """Fuehrt den Operator aus. Bei SimulatedAccelerator: reine
        Berechnung/Zeitmodell. Bei einer echten Implementierung: der
        tatsaechliche Hardware-Aufruf (z.B. CUDA-Kernel-Launch, ONNX-
        Runtime-Session.run(), Vendor-SDK-Call)."""

    def is_thermally_available(self) -> bool:
        return self.current_temperature_c() < self.thermal_limit_c()


class SimulatedAccelerator(Accelerator):
    """Referenz-Implementierung fuer diese Sandbox: KEINE echte Hardware,
    reines Zeit-/Energie-/Temperatur-Modell. Ehrlich als Simulation
    gekennzeichnet -- macht keine Behauptung, echtes Silizium anzusprechen."""

    def __init__(self, accel_id: str,
                 op_profiles: Dict[OperatorType, tuple],  # (exec_s, energy_j)
                 thermal_limit_c: float = 85.0,
                 start_temp_c: float = 45.0,
                 heat_per_op_c: float = 2.0,
                 cool_rate_c_per_s: float = 0.5):
        self._accel_id = accel_id
        self._profiles = op_profiles
        self._thermal_limit = thermal_limit_c
        self._temp = start_temp_c
        self._heat_per_op = heat_per_op_c
        self._cool_rate = cool_rate_c_per_s
        self._busy_until = 0.0
        self._clock = 0.0

    @property
    def accel_id(self) -> str:
        return self._accel_id

    def supported_ops(self) -> Set[OperatorType]:
        return set(self._profiles.keys())

    def estimated_exec_time(self, op: OperatorNode) -> float:
        if op.op_type not in self._profiles:
            raise AcceleratorError(f"{self._accel_id} unterstuetzt {op.op_type} nicht")
        return self._profiles[op.op_type][0]

    def estimated_energy(self, op: OperatorNode) -> float:
        if op.op_type not in self._profiles:
            raise AcceleratorError(f"{self._accel_id} unterstuetzt {op.op_type} nicht")
        return self._profiles[op.op_type][1]

    def current_temperature_c(self) -> float:
        return self._temp

    def thermal_limit_c(self) -> float:
        return self._thermal_limit

    def queue_free_time(self) -> float:
        return max(0.0, self._busy_until - self._clock)

    def run_operator(self, op: OperatorNode) -> ExecutionResult:
        if op.op_type not in self._profiles:
            return ExecutionResult(op.node_id, self._accel_id, 0.0, 0.0,
                                   success=False,
                                   error=f"{self._accel_id} unterstuetzt {op.op_type} nicht")
        if not self.is_thermally_available():
            return ExecutionResult(op.node_id, self._accel_id, 0.0, 0.0,
                                   success=False,
                                   error=f"{self._accel_id} ueber Temperatur-Limit")
        exec_t = self._profiles[op.op_type][0]
        energy = self._profiles[op.op_type][1]
        self._clock += exec_t
        self._busy_until = self._clock
        self._temp += self._heat_per_op
        return ExecutionResult(op.node_id, self._accel_id, exec_t, energy, success=True)

    def tick_cooldown(self, seconds: float):
        """Simuliert passives Abkuehlen -- nur fuer Tests/Modell relevant."""
        self._temp = max(45.0, self._temp - self._cool_rate * seconds)
