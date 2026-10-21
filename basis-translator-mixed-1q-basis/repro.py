"""Translation of a two-qubit gate ignores a qubit-specific one-qubit basis."""
import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit.circuit.library import ECRGate, RZGate, SXGate, UGate, XGate
from qiskit.transpiler import Target

t = Target(num_qubits=2)
t.add_instruction(RZGate(Parameter("t")), {(0,): None}); t.add_instruction(SXGate(), {(0,): None})
t.add_instruction(XGate(), {(0,): None}); t.add_instruction(UGate(Parameter("a"), Parameter("b"), Parameter("c")), {(1,): None})
t.add_instruction(ECRGate(), {(0, 1): None})
for label, op in [("cx", lambda c: c.cx(0, 1)), ("rzz", lambda c: c.rzz(1.4, 0, 1))]:
    qc = QuantumCircuit(2); op(qc)
    out = transpile(qc, target=t, optimization_level=0, initial_layout=[0, 1], seed_transpiler=1)
    bad = []
    for x in out.data:
        qargs = tuple(out.find_bit(q).index for q in x.qubits)
        if not t.instruction_supported(x.operation.name, qargs): bad.append((x.operation.name, qargs))
    print(label, "unsupported:", bad)
print("qiskit", qiskit.__version__)
