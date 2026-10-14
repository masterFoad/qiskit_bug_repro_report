"""A user-defined gate named "rz" is kept as the target's native rz.

The gate is defined as ry(theta) but named "rz". Because "rz" is in the target basis, the BasisTranslator does
not expand it, so the output contains a native RZ that a device would execute as RZ, a different operation.

Usage: python repro.py            (1-qubit case)
       python repro.py --gadget   (also the 2-qubit case over 40 seeds; on qiskit 2.5.0-2.5.2 this case can
                                   hang in CommutativeCancellation, see Qiskit/qiskit#16937, fixed for 2.6)
"""
import sys
import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Gate
from qiskit.circuit.library import RZGate
from qiskit.quantum_info import Operator
from qiskit.providers.fake_provider import GenericBackendV2

print("qiskit", qiskit.__version__)
theta = 0.9


def lookalike():
    gate = Gate("rz", 1, [theta])
    definition = QuantumCircuit(1)
    definition.ry(theta, 0)
    gate.definition = definition
    return gate


def lookalikes_left(circuit):
    return sum(1 for inst in circuit.data
               if inst.operation.name == "rz" and not isinstance(inst.operation, RZGate))


qc1 = QuantumCircuit(1)
qc1.append(lookalike(), [0])
backend = GenericBackendV2(num_qubits=5, basis_gates=["cz", "rz", "sx", "x"], seed=1)
for level in range(4):
    out = transpile(qc1, backend, optimization_level=level, seed_transpiler=0)
    print(f"1-qubit circuit, O{level}: ops={dict(out.count_ops())} lookalike rz left={lookalikes_left(out)}")
print("operator of the user gate equals RZ(theta)?", Operator(qc1).equiv(Operator(RZGate(theta))))

if "--gadget" in sys.argv:
    qc = QuantumCircuit(2)
    qc.append(lookalike(), [0])
    qc.cz(0, 1)
    backend27 = GenericBackendV2(num_qubits=27, basis_gates=["ecr", "rz", "sx", "x"], seed=1234)
    for level in (2, 3):
        left = [s for s in range(40)
                if lookalikes_left(transpile(qc, backend27, optimization_level=level, seed_transpiler=s))]
        print(f"2-qubit circuit on a 27-qubit ECR backend, O{level}: {len(left)}/40 seeds keep the lookalike rz")
