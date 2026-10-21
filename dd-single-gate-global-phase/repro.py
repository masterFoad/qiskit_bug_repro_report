"""A one-gate DD sequence changes global phase."""
import numpy as np
import qiskit
from qiskit import QuantumCircuit
from qiskit.circuit import Delay, Parameter
from qiskit.circuit.library import CXGate, UGate, XGate
from qiskit.quantum_info import Operator
from qiskit.transpiler import InstructionProperties, PassManager, Target
from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDynamicalDecoupling

dt = 1e-9; t = Target(num_qubits=2, dt=dt)
t.add_instruction(UGate(Parameter("a"), Parameter("b"), Parameter("c")), {(q,): InstructionProperties(duration=50*dt) for q in range(2)})
t.add_instruction(XGate(), {(q,): InstructionProperties(duration=50*dt) for q in range(2)})
t.add_instruction(CXGate(), {(0, 1): InstructionProperties(duration=300*dt)})
t.add_instruction(Delay(Parameter("d")), {(q,): None for q in range(2)})
qc = QuantumCircuit(2); qc.cx(0, 1)
for _ in range(6): qc.u(.3, .2, .1, 1)
qc.u(.4, -.6, 1.3, 0); qc.cx(0, 1)
dd = PassManager([ALAPScheduleAnalysis(target=t), PadDynamicalDecoupling(target=t, dd_sequence=[XGate()])]).run(qc)
a, b = Operator(dd).data, Operator(qc).data; pos = np.unravel_index(np.argmax(abs(b)), b.shape)
print("qiskit", qiskit.__version__)
print("equal up to global phase:", Operator(dd).equiv(Operator(qc)))
print("exactly equal:", np.allclose(a, b))
print("global phase error (rad):", round(float(np.angle(a[pos] / b[pos])), 6))
