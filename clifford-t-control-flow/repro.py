"""Clifford+T translation fails for any circuit containing control flow.

Run from the repository root with: python clifford-t-control-flow/repro.py
The equivalent static circuit compiles, but an if_else circuit raises
TranspilerError on the same Clifford+T basis.
"""
import qiskit
from qiskit import QuantumCircuit
from qiskit.quantum_info import get_clifford_gate_names
from qiskit.transpiler import generate_preset_pass_manager


print("Python", __import__("sys").version.split()[0])
print("qiskit", qiskit.__version__)
basis = get_clifford_gate_names() + ["t", "tdg"]
pm = generate_preset_pass_manager(optimization_level=2, basis_gates=basis)


def circuit(with_control_flow):
    qc = QuantumCircuit(2, 1)
    qc.h(0)
    qc.measure(0, 0)
    if with_control_flow:
        with qc.if_test((qc.clbits[0], 1)):
            qc.x(1)
    else:
        qc.x(1)
    return qc


for label, has_control_flow in (("static", False), ("if_else", True)):
    try:
        output = pm.run(circuit(has_control_flow))
        print(label, "COMPILED", dict(output.count_ops()))
    except Exception as exc:
        print(label, "FAILED", type(exc).__name__, str(exc).split(". ")[0])
