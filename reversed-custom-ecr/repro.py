"""A reversed user-defined ECR raises GateDirection TranspilerError.

Run from the repository root with: python reversed-custom-ecr/repro.py
A standard ECR can be reversed for this directed target. The same operation
inside a user-defined Gate("ecr") instead fails during transpilation.
"""
import sys
import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Gate
from qiskit.circuit.library import ECRGate, RZGate, SXGate, XGate
from qiskit.transpiler import Target


print("Python", sys.version.split()[0])
print("qiskit", qiskit.__version__)
target = Target(num_qubits=2)
for operation in (RZGate(0), SXGate(), XGate()):
    target.add_instruction(operation, {(0,): None, (1,): None})
target.add_instruction(ECRGate(), {(1, 0): None})
custom = Gate("ecr", 2, [])
custom.definition = QuantumCircuit(2)
custom.definition.ecr(0, 1)

for label, operation in (("standard_ecr", ECRGate()), ("custom_ecr", custom)):
    circuit = QuantumCircuit(2)
    circuit.append(operation, (0, 1))
    try:
        output = transpile(circuit, target=target, initial_layout=[0, 1],
                           routing_method="none", optimization_level=2)
        print(label, "COMPILED", dict(output.count_ops()))
    except Exception as exc:
        print(label, "FAILED", type(exc).__name__, str(exc))
