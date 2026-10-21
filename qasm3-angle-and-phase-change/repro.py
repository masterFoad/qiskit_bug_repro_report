"""Check whether a QASM 3 round trip preserves angles and circuit phase."""
import math

import qiskit
from qiskit import QuantumCircuit, qasm3
from qiskit.quantum_info import Operator

near_pi = math.pi / 2 - 9e-10
circuit = QuantumCircuit(2, global_phase=0.75)
circuit.rzz(near_pi, 0, 1)
exported = qasm3.dumps(circuit)
loaded = qasm3.loads(exported)
angle = float(loaded.data[0].operation.params[0])
print("qiskit", qiskit.__version__)
print("input angle", repr(near_pi), "loaded angle", repr(angle))
print("angle change", angle - near_pi)
print("input phase", circuit.global_phase, "loaded phase", loaded.global_phase)
print("operator equal", Operator(circuit) == Operator(loaded))
print("exported gate", next(line for line in exported.splitlines() if line.startswith("rzz")))
