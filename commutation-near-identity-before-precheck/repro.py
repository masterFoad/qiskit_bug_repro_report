"""Reproduce the near-identity shortcut occurring before the instruction precheck.

Expected: RY(1e-7) reports as commuting with barrier, measurement, and reset;
RY(1e-3) does not.  These are same-wire queries.
"""
import importlib.metadata
import platform
import sys
from qiskit.circuit import Barrier, Measure, Reset
from qiskit.circuit.commutation_library import SessionCommutationChecker as checker
from qiskit.circuit.library import RYGate


print("qiskit", importlib.metadata.version("qiskit"))
print("python", platform.python_version(), "platform", sys.platform)
for name, op in (("barrier", Barrier(1)), ("measure", Measure()), ("reset", Reset())):
    answers = [checker.commute(RYGate(angle), [0], [], op, [0], []) for angle in (0.0, 1e-7, 1e-3)]
    reproduced = answers == [True, True, False]
    print(name, "zero/near/nontrivial", *answers, "REPRODUCED" if reproduced else "NOT_REPRODUCED")
