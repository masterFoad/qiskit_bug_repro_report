"""Reproduce the broken public check_commutation_entries wrapper."""
import importlib.metadata
import platform
import sys
from qiskit.circuit.commutation_library import SessionCommutationChecker as checker
from qiskit.circuit.library import CXGate, ZGate


print("qiskit", importlib.metadata.version("qiskit"))
print("python", platform.python_version(), "platform", sys.platform)
try:
    result = checker.check_commutation_entries(CXGate(), [0, 1], ZGate(), [0])
except Exception as exc:
    reproduced = isinstance(exc, AttributeError) and "library" in str(exc)
    print("exception", type(exc).__name__, str(exc), "REPRODUCED" if reproduced else "NOT_REPRODUCED")
else:
    print("result", result, "NOT_REPRODUCED")
