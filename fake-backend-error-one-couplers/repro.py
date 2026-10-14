"""List two-qubit instructions with error 1.0 in IBM fake backend targets.

Run: python fake-backend-error-one-couplers/repro.py
Uses packaged snapshots only; no account or hardware access is needed.
"""
import platform
from importlib.metadata import version
from qiskit_ibm_runtime.fake_provider import FakeFez, FakeSherbrooke

print("python", platform.python_version())
print("qiskit", version("qiskit"))
print("qiskit-ibm-runtime", version("qiskit-ibm-runtime"))
for backend in (FakeFez(), FakeSherbrooke()):
    bad = []
    total = 0
    for name in sorted(backend.target.operation_names):
        for qargs, props in backend.target[name].items():
            if qargs is not None and len(qargs) == 2:
                total += 1
                if props is not None and props.error == 1.0:
                    bad.append((name, qargs, props.error))
    print(type(backend).__name__, "two_qubit_entries", total,
          "error_one_entries", len(bad))
    for name, qargs, error in sorted(bad):
        print(" ", name, qargs, "error", error)
