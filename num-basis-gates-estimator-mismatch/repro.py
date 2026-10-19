"""Compare num_basis_gates with the decomposition actually produced for CX."""
import importlib.metadata
import platform
import sys
from qiskit import QuantumCircuit
from qiskit.circuit.library import CXGate
from qiskit.quantum_info import Operator
from qiskit.synthesis import TwoQubitBasisDecomposer


decomposer = TwoQubitBasisDecomposer(CXGate(), basis_fidelity=1.0)


def report(name, circuit):
    unitary = Operator(circuit).data
    predicted = decomposer.num_basis_gates(unitary)
    synthesized = decomposer(unitary)
    actual = len(synthesized.get_instructions("cx"))
    mismatch = predicted != actual
    print(name, "predicted", predicted, "actual", actual, "equiv", Operator(circuit).equiv(Operator(synthesized)), "MISMATCH" if mismatch else "MATCH")


print("qiskit", importlib.metadata.version("qiskit"))
print("python", platform.python_version(), "platform", sys.platform)
q = QuantumCircuit(2)
q.h(0)
q.swap(0, 1)
report("h_then_swap", q)
q = QuantumCircuit(2)
q.swap(0, 1)
report("swap", q)
q = QuantumCircuit(2)
for index in range(4):
    q.cx(0, 1) if index % 2 == 0 else q.cx(1, 0)
report("four_alternating_cx", q)
