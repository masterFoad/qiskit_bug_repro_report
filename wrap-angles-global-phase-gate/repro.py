"""An out-of-range RZZ leaves a zero-qubit operation outside the target ISA."""
import math
import qiskit
import qiskit_ibm_runtime
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Parameter
from qiskit.circuit.library import RZZGate
from qiskit.transpiler import InstructionProperties
from qiskit_ibm_runtime.fake_provider import FakeFez

t = FakeFez().target
props = {q: InstructionProperties(error=p.error, duration=p.duration) for q, p in t["cz"].items()}
t.add_instruction(RZZGate(Parameter("theta")), props, angle_bounds=[(0, math.pi / 2)])
a, b = next(iter(t["cz"]))
qc = QuantumCircuit(2); qc.rzz(2.0, 0, 1)
out = transpile(qc, target=t, initial_layout=[a, b], optimization_level=0, seed_transpiler=1)
print("qiskit", qiskit.__version__, "runtime", qiskit_ibm_runtime.__version__)
print("operations:", [i.operation.name for i in out.data])
print("outside target:", [i.operation.name for i in out.data if i.operation.name not in t.operation_names])
try:
    transpile(qc, target=t, initial_layout=[a, b], optimization_level=0, scheduling_method="alap")
    print("scheduling: ok")
except Exception as exc:
    print("scheduling:", type(exc).__name__, str(exc))
