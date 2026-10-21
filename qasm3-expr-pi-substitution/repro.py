"""The QASM 3 exporter rewrites a parameter expression into invalid syntax."""
import math
import qiskit
import openqasm3
from qiskit import QuantumCircuit, qasm3
from qiskit.circuit import Parameter

th = Parameter("th"); qc = QuantumCircuit(1)
qc.rz(th * math.pi + 23.141592653589793, 0)
line = next(x for x in qasm3.dumps(qc).splitlines() if x.startswith("rz"))
safe = next(x for x in qasm3.dumps(qc, disable_constants=True).splitlines() if x.startswith("rz"))
expr = line[3:line.rindex(")")]
print("qiskit", qiskit.__version__, "openqasm3", openqasm3.__version__)
print("default:", line); print("disable_constants:", safe)
try:
    openqasm3.parse(f"OPENQASM 3.0;\ninput float th;\nfloat x = {expr};")
    print("reference parse: ok")
except Exception as exc:
    print("reference parse:", type(exc).__name__)
