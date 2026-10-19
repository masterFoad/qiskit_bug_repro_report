"""Reproduce CommutativeCancellation's fixed merged-angle cutoff.

Expected: two RZ(6e-5) rotations (total angle 1.2e-4) are removed, although the
result differs from the input by a phase-aligned operator norm near 6e-5. The second case shows
the same result through preset optimization level 2 and 3.
"""
import importlib.metadata
import platform
import sys
import numpy as np
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Operator
from qiskit.transpiler.passes import CommutativeCancellation


def distance(left, right):
    a, b = Operator(left).data, Operator(right).data
    phase = np.vdot(a, b)
    phase = phase / abs(phase) if abs(phase) else 1
    return np.linalg.norm(b - phase * a, 2)


q = QuantumCircuit(1)
q.rz(6e-5, 0)
q.rz(6e-5, 0)
out = CommutativeCancellation()(q)
print("qiskit", importlib.metadata.version("qiskit"))
print("python", platform.python_version(), "platform", sys.platform)
single = (not out.count_ops() and not Operator(q).equiv(Operator(out)) and distance(q, out) > 1e-6)
control = QuantumCircuit(1)
control.rz(1.2e-4, 0)
control_out = CommutativeCancellation()(control)
print("single_pass", dict(out.count_ops()), "equiv", Operator(q).equiv(Operator(out)), "distance", f"{distance(q, out):.9g}", "REPRODUCED" if single else "NOT_REPRODUCED")
print("control_single_rz", dict(control_out.count_ops()), "equiv", Operator(control).equiv(Operator(control_out)))

q = QuantumCircuit(3)
q.rz(6e-5, 0)
q.cx(0, 1)
q.cx(0, 2)
q.rz(6e-5, 0)
for level in (2, 3):
    out = transpile(q, basis_gates=["cx", "rz", "sx", "x"], optimization_level=level, seed_transpiler=1)
    reproduced = not Operator(q).equiv(Operator(out)) and distance(q, out) > 1e-6
    print("preset", level, dict(out.count_ops()), "equiv", Operator(q).equiv(Operator(out)), "distance", f"{distance(q, out):.9g}", "REPRODUCED" if reproduced else "NOT_REPRODUCED")
