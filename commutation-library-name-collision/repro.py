"""Reproduce a name-keyed commutation-library false positive.

Expected: a custom gate called ``z`` that implements X is said to commute with S,
then CommutativeInverseCancellation removes S/Sdg around it and changes the unitary.
"""
import importlib.metadata
import platform
import sys
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit import Gate
from qiskit.circuit.commutation_library import SessionCommutationChecker as checker
from qiskit.circuit.library import SGate
from qiskit.quantum_info import Operator
from qiskit.transpiler.passes import CommutativeInverseCancellation


print("qiskit", importlib.metadata.version("qiskit"))
print("python", platform.python_version(), "platform", sys.platform)
try:
    body = QuantumCircuit(1)
    body.x(0)
    fake_z = Gate("z", 1, [])
    fake_z.definition = body
    reported = checker.commute(fake_z, [0], [], SGate(), [0], [])
    a = QuantumCircuit(1)
    a.append(fake_z, [0])
    a.s(0)
    b = QuantumCircuit(1)
    b.s(0)
    b.append(fake_z, [0])
    exact_distance = np.linalg.norm(Operator(a).data - Operator(b).data, 2)
    q = QuantumCircuit(1)
    q.s(0)
    q.append(fake_z, [0])
    q.sdg(0)
    out = CommutativeInverseCancellation()(q)
    pass_equiv = Operator(q).equiv(Operator(out))
    reproduced = reported is True and exact_distance > 1e-6 and not pass_equiv
    print("checker_says_commutes", reported, "exact_commutator_norm", f"{exact_distance:.9g}")
    print("pass_output", dict(out.count_ops()), "equiv", pass_equiv, "REPRODUCED" if reproduced else "NOT_REPRODUCED")
except Exception as exc:
    print("exception", type(exc).__name__, "NOT_REPRODUCED")
