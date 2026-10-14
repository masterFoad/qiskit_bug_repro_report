"""Show invalid intermediate RZZ angles and repeated translation in a finite O3 run.
Run: python o3-rzz-retranslation/repro.py
"""
import math
import platform
import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter, Qubit
from qiskit.circuit.library import RZZGate, RZGate, SXGate, XGate
from qiskit.dagcircuit import DAGCircuit
from qiskit.transpiler import Target
from qiskit.transpiler.passes import WrapAngles
print("python", platform.python_version())
print("qiskit", qiskit.__version__)
def fold_rzz(angles, _):
    dag = DAGCircuit()
    q = [Qubit(), Qubit()]
    dag.add_qubits(q)
    angle = math.remainder(float(angles[0]), 2 * math.pi)
    dag.global_phase = (float(angles[0]) - angle) / 2
    if abs(angle) > math.pi / 2:
        for qubit in q:
            dag.apply_operation_back(RZGate(math.pi), [qubit])
        dag.global_phase += math.copysign(math.pi / 2, angle)
        angle -= math.copysign(math.pi, angle)
    if angle < 0:
        dag.apply_operation_back(XGate(), [q[0]])
    dag.apply_operation_back(RZZGate(abs(angle)), q)
    if angle < 0:
        dag.apply_operation_back(XGate(), [q[0]])
    return dag
WrapAngles.DEFAULT_REGISTRY.add_wrapper("rzz", fold_rzz)
target = Target(num_qubits=8)
for op in (RZGate(Parameter("theta")), SXGate(), XGate()):
    target.add_instruction(op, {(q,): None for q in range(8)})
target.add_instruction(RZZGate(Parameter("theta")),
    {(a, b): None for a in range(8) for b in range(a + 1, 8)},
    angle_bounds=[(0, math.pi / 2)])
qc = QuantumCircuit(8)
for a in range(8):
    qc.h(a)
    for b in range(a + 1, 8):
        qc.cp(math.pi / 2, b, a)
def callback(**kw):
    name = kw["pass_"].name()
    if name in ("TwoQubitPeepholeOptimization", "WrapAngles", "GatesInBasis"):
        bad = sum(n.name == "rzz" and not 0 <= float(n.op.params[0]) <= math.pi / 2 for n in kw["dag"].op_nodes())
        print(name, "out_of_bounds_rzz", bad, "in_basis", kw["property_set"].get("all_gates_in_basis"))
out = transpile(qc, target=target, optimization_level=3, seed_transpiler=11, callback=callback)
print("compile_terminated", True, "depth", out.depth(), "size", out.size())
print("final_out_of_bounds_rzz", sum(i.operation.name == "rzz" and not 0 <= float(i.operation.params[0]) <= math.pi / 2 for i in out.data))
