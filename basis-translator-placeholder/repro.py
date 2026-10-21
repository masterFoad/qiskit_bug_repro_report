"""A heterogeneous two-qubit basis can leave an unreadable operation."""
import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit.circuit.library import CZGate, ECRGate, RZGate, SXGate, XGate
from qiskit.transpiler import Target

target = Target(num_qubits=3)
for gate in (RZGate(Parameter("t")), SXGate(), XGate()):
    target.add_instruction(gate, {(qubit,): None for qubit in range(3)})
target.add_instruction(CZGate(), {(0, 1): None, (1, 0): None})
target.add_instruction(ECRGate(), {(1, 2): None})
circuit = QuantumCircuit(3)
circuit.ecr(2, 1)
print("qiskit", qiskit.__version__)
for level in range(4):
    try:
        out = transpile(circuit, target=target, optimization_level=level,
                        initial_layout=[0, 1, 2], seed_transpiler=1)
        print("O" + str(level), "OK", dict(out.count_ops()))
    except Exception as exc:
        print("O" + str(level), type(exc).__name__ + ":", str(exc)[:160])
