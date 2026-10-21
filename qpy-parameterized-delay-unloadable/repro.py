"""QPY-loaded parameterized delays raise when their operation is accessed."""
import io
import qiskit
from qiskit import QuantumCircuit, qpy
from qiskit.circuit import Parameter

t = Parameter("t")
circuit = QuantumCircuit(1)
circuit.delay(t, 0, "dt")
for version in (None, 17):
    payload = io.BytesIO()
    qpy.dump(circuit, payload, **({} if version is None else {"version": version}))
    loaded = qpy.load(io.BytesIO(payload.getvalue()))[0]
    try:
        operation = loaded.data[0].operation
        result = f"OK {operation.duration} {operation.unit}"
    except Exception as exc:
        result = f"{type(exc).__name__}: {exc}"
    print("version", version or qpy.QPY_VERSION, result)
print("qiskit", qiskit.__version__)
