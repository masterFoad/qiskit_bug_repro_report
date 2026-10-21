"""A mixed alignment target leaves a measurement outside its acquire grid."""
import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import InstructionDurationCheck
from qiskit_ibm_runtime.fake_provider import FakePrague

target = FakePrague().target
circuit = QuantumCircuit(1, 1)
circuit.x(0); circuit.delay(100, 0, "dt"); circuit.measure(0, 0)
manager = PassManager([InstructionDurationCheck(target=target)])
manager.run(circuit)
out = transpile(circuit, target=target, scheduling_method="alap", optimization_level=0,
                initial_layout=[0])
measure_start = next(start for item, start in zip(out.data, out.op_start_times)
                     if item.operation.name == "measure")
print("qiskit", qiskit.__version__)
print("alignments", target.pulse_alignment, target.acquire_alignment)
print("reschedule_required", manager.property_set["reschedule_required"], "expected True")
print("measure_start", measure_start, "mod_acquire", measure_start % target.acquire_alignment)
