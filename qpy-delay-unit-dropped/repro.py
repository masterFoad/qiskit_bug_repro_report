"""QPY version 17 changes a delay's unit during a round trip."""
import io
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
import qiskit
import qiskit_ibm_runtime
from qiskit import QuantumCircuit, qpy
from qiskit_ibm_runtime.utils.json import RuntimeDecoder, RuntimeEncoder

circuit = QuantumCircuit(1)
circuit.delay(100, 0, "us")
payload = io.BytesIO()
qpy.dump(circuit, payload, version=17)
loaded = qpy.load(io.BytesIO(payload.getvalue()))[0]
encoded = RuntimeEncoder().encode(circuit)
decoded = RuntimeDecoder().decode(encoded)
print("qiskit", qiskit.__version__, "runtime", qiskit_ibm_runtime.__version__)
print("qpy_v17", loaded.data[0].operation.duration, loaded.data[0].operation.unit)
print("runtime", decoded.data[0].operation.duration, decoded.data[0].operation.unit)
print("expected", "100 us")
