"""A scheduler can overlap two instructions on one qubit after alignment."""
import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Delay, Parameter
from qiskit.circuit.library import SXGate, XGate
from qiskit.transpiler import InstructionProperties, Target

dt = 1e-9
target = Target(num_qubits=1, dt=dt, pulse_alignment=16, acquire_alignment=16)
for gate, duration in ((XGate(), 160), (SXGate(), 36)):
    target.add_instruction(gate, {(0,): InstructionProperties(duration=duration * dt)})
target.add_instruction(Delay(Parameter("d")), {(0,): None})
circuit = QuantumCircuit(1)
circuit.x(0); circuit.delay(100, 0, "dt"); circuit.sx(0); circuit.sx(0)
out = transpile(circuit, target=target, scheduling_method="alap", optimization_level=0)
times = []
for item, start in zip(out.data, out.op_start_times):
    op = item.operation
    duration = op.duration if op.name == "delay" else {"x": 160, "sx": 36}[op.name]
    times.append((op.name, start, start + duration))
print("qiskit", qiskit.__version__)
print(" ".join(f"{name}[{start},{end})" for name, start, end in times))
print("overlap", times[-1][1] < times[-2][2], "expected False")
