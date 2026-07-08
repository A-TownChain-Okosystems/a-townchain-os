"""Tests fuer den DA-HEFT-Scheduler. Alle Beschleuniger sind
SimulatedAccelerator -- ehrlich als Simulation, kein Anspruch auf
echte Hardware. Der Scheduler-Code selbst ist hardware-agnostisch
(siehe accelerator.py Docstring)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
from shivaos.scheduler.accelerator import (
    SimulatedAccelerator, OperatorNode, OperatorType
)
from shivaos.scheduler.daheft import DAHEFTScheduler, Task, SchedulingError


def make_cpu():
    return SimulatedAccelerator(
        "cpu0",
        op_profiles={
            OperatorType.CONV2D: (0.008, 2.0),
            OperatorType.RELU:   (0.001, 0.5),
            OperatorType.MATMUL: (0.003, 1.5),
        },
        thermal_limit_c=95.0, start_temp_c=50.0,
    )


def make_gpu(start_temp=60.0):
    return SimulatedAccelerator(
        "gpu0",
        op_profiles={
            OperatorType.CONV2D: (0.001, 15.0),
            OperatorType.RELU:   (0.0003, 3.0),
            OperatorType.MATMUL: (0.0008, 10.0),
        },
        thermal_limit_c=80.0, start_temp_c=start_temp,
    )


def make_npu():
    return SimulatedAccelerator(
        "npu0",
        op_profiles={
            OperatorType.CONV2D: (0.0008, 3.0),
            OperatorType.RELU:   (0.0002, 0.8),
            OperatorType.MATMUL: (0.0005, 2.0),
        },
        thermal_limit_c=90.0, start_temp_c=55.0,
    )


def test_single_node_picks_lowest_eft_energy_product():
    """Ohne Deadline/Hitze sollte die NPU gewinnen -- schnell UND sparsam."""
    cpu, gpu, npu = make_cpu(), make_gpu(), make_npu()
    sched = DAHEFTScheduler([cpu, gpu, npu])
    task = Task(task_id="t1", nodes=[
        OperatorNode("n1", OperatorType.MATMUL)
    ])
    plan = sched.plan([task])
    assert len(plan) == 1
    assert plan[0].accel_id == "npu0"


def test_dependency_order_respected():
    """Conv2D -> ReLU -> MatMul: ReLU darf erst nach Conv2D starten."""
    sched = DAHEFTScheduler([make_cpu(), make_gpu(), make_npu()])
    task = Task(
        task_id="chain",
        nodes=[
            OperatorNode("conv", OperatorType.CONV2D),
            OperatorNode("relu", OperatorType.RELU),
            OperatorNode("mm", OperatorType.MATMUL),
        ],
        edges={"relu": ["conv"], "mm": ["relu"]},
    )
    plan = sched.plan([task])
    by_id = {e.node_id: e for e in plan}
    assert by_id["relu"].predicted_start_s >= by_id["conv"].predicted_end_s
    assert by_id["mm"].predicted_start_s >= by_id["relu"].predicted_end_s


def test_overheated_accelerator_is_skipped():
    """Das Beispiel aus der Spezifikation: GPU zu heiss (80C Limit, 82C aktuell)
    -> Scheduler muss sie ignorieren, auch wenn sie schneller waere."""
    cpu = make_cpu()
    hot_gpu = make_gpu(start_temp=82.0)   # ueber ihrem eigenen Limit von 80C
    npu = make_npu()
    sched = DAHEFTScheduler([cpu, hot_gpu, npu])

    task = Task(task_id="realtime", nodes=[OperatorNode("op", OperatorType.CONV2D)])
    plan = sched.plan([task])
    assert plan[0].accel_id != "gpu0"
    assert not hot_gpu.is_thermally_available()


def test_deadline_admission_control_flags_miss():
    """Deadline so eng, dass sie niemand einhalten kann -> deadline_met=False,
    aber trotzdem bester Kompromiss statt Exception."""
    cpu = make_cpu()  # 8ms fuer Conv2D
    sched = DAHEFTScheduler([cpu])
    task = Task(task_id="impossible",
               nodes=[OperatorNode("op", OperatorType.CONV2D)],
               deadline_s=0.0001)  # 0.1ms -- unmoeglich
    plan = sched.plan([task])
    assert plan[0].deadline_met is False


def test_deadline_met_when_achievable():
    sched = DAHEFTScheduler([make_npu()])
    task = Task(task_id="ok",
               nodes=[OperatorNode("op", OperatorType.MATMUL)],
               deadline_s=0.01)  # 10ms -- NPU braucht nur 0.5ms
    plan = sched.plan([task])
    assert plan[0].deadline_met is True


def test_no_supporting_accelerator_raises():
    npu_no_conv = SimulatedAccelerator("npu_limited",
        op_profiles={OperatorType.MATMUL: (0.001, 1.0)})
    sched = DAHEFTScheduler([npu_no_conv])
    task = Task(task_id="fail", nodes=[OperatorNode("op", OperatorType.CONV2D)])
    with pytest.raises(SchedulingError):
        sched.plan([task])


def test_execute_actually_runs_via_accelerator_interface():
    """execute() ruft echte run_operator()-Aufrufe auf dem Interface --
    das ist der Punkt, an dem spaeter echte Hardware andocken wuerde."""
    npu = make_npu()
    sched = DAHEFTScheduler([npu])
    task = Task(task_id="run", nodes=[OperatorNode("op", OperatorType.MATMUL)])
    results = sched.execute([task])
    assert len(results) == 1
    assert results[0].success
    assert results[0].accel_id == "npu0"
    # Beschleuniger-Zustand hat sich durch echte Ausfuehrung veraendert:
    assert npu.current_temperature_c() > 55.0


def test_realistic_autonomous_driving_example():
    """Nachbau des Beispiels: Conv2D(heavy)->ReLU->MatMul, 5ms Deadline,
    GPU ueberhitzt -> NPU muss die gesamte Kette uebernehmen."""
    cpu = make_cpu()
    hot_gpu = make_gpu(start_temp=85.0)
    npu = make_npu()
    sched = DAHEFTScheduler([cpu, hot_gpu, npu])

    task = Task(
        task_id="autonomous_perception",
        nodes=[
            OperatorNode("conv", OperatorType.CONV2D),
            OperatorNode("relu", OperatorType.RELU),
            OperatorNode("mm", OperatorType.MATMUL),
        ],
        edges={"relu": ["conv"], "mm": ["relu"]},
        deadline_s=0.005,  # 5ms
    )
    plan = sched.plan([task])
    assert all(e.accel_id == "npu0" for e in plan)
    assert all(e.deadline_met for e in plan)
    assert plan[-1].predicted_end_s < 0.005
