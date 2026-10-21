"""A pulse-aligned gate remains off-grid when pulse and acquire alignment differ."""
import qiskit
from qiskit import QuantumCircuit
from qiskit.circuit import Delay, Parameter
from qiskit.circuit.library import XGate
from qiskit.transpiler import InstructionProperties, PassManager, Target
from qiskit.transpiler.passes import ALAPScheduleAnalysis, ConstrainedReschedule, TimeUnitConversion

dt = 1e-9
target = Target(num_qubits=1, dt=dt, pulse_alignment=16, acquire_alignment=1)
target.add_instruction(XGate(), {(0,): InstructionProperties(duration=160 * dt)})
target.add_instruction(Delay(Parameter("d")), {(0,): None})
circuit = QuantumCircuit(1)
circuit.x(0); circuit.delay(100, 0, "dt"); circuit.x(0)
manager = PassManager([TimeUnitConversion(target=target), ALAPScheduleAnalysis(target=target),
                       ConstrainedReschedule(target=target)])
manager.run(circuit)
starts = manager.property_set["node_start_time"]
second_x = max(time for node, time in starts.items() if node.name == "x")
print("qiskit", qiskit.__version__)
print("pulse_alignment", target.pulse_alignment, "acquire_alignment", target.acquire_alignment)
print("second_x_start", second_x, "mod_pulse", second_x % target.pulse_alignment)
