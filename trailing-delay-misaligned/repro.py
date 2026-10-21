"""A trailing delay can leave the scheduled circuit off the target alignment grid."""
import warnings
import qiskit
import qiskit_ibm_runtime
from qiskit import QuantumCircuit, transpile
from qiskit.circuit.library import XGate
from qiskit.transpiler import PassManager
from qiskit.transpiler.passes import ALAPScheduleAnalysis, PadDynamicalDecoupling
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke

warnings.filterwarnings("ignore")
t = FakeSherbrooke().target; qc = QuantumCircuit(2); qc.delay(100, 1, unit="dt")
out = transpile(qc, target=t, scheduling_method="alap", optimization_level=0, initial_layout=[0, 1])
print("qiskit", qiskit.__version__, "runtime", qiskit_ibm_runtime.__version__)
print("duration:", out.duration, "mod alignment:", out.duration % t.acquire_alignment)
try:
    PassManager([ALAPScheduleAnalysis(target=t), PadDynamicalDecoupling(target=t, dd_sequence=[XGate(), XGate()])]).run(out)
    print("DD: ok")
except Exception as exc:
    print("DD:", type(exc).__name__, str(exc))
