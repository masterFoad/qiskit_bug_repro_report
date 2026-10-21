"""Reproduce CommutativeCancellation's fixed merged-angle cutoff.

Expected: two RZ(6e-5) rotations (total angle 1.2e-4) are removed, although the
result differs from the input by a phase-aligned operator norm near 6e-5. The second case shows
the same result through preset optimization level 2 and 3.
"""
# Used to print the installed Qiskit version.
import importlib.metadata
# Used to print the Python version.
import platform
# Used to print the OS platform.
import sys
# Linear algebra for the operator distance.
import numpy as np
# Circuit construction and the preset transpiler pipeline.
from qiskit import QuantumCircuit, transpile
# Builds the unitary matrix of a circuit.
from qiskit.quantum_info import Operator
# The pass under test, run on its own in the first case.
from qiskit.transpiler.passes import CommutativeCancellation


# Minimum input/output error for reporting the bug, independent of Operator.equiv's tolerances.
ERROR_THRESHOLD = 1e-6
# Strict tolerance for matching the expected CX-only output, up to global phase.
MATCH_TOLERANCE = 1e-12


# Distance between two circuits' unitaries, ignoring global phase.
# 0 means the circuits act identically; larger values mean they differ more.
# U and e^{i*phi} U are physically the same operation, so a plain ||U - V|| would
# report a false difference; the phase of one matrix is aligned to the other first.
# Example (case 1): a = RZ(1.2e-4) = diag(e^{-i*t/2}, e^{i*t/2}), b = I. The trace
# 2*cos(t/2) is real and positive, so phase = 1, and each diagonal entry of b - a has
# magnitude 2*sin(t/4) ~ t/2 = 6e-5, which is the returned distance.
# Caveat: the trace-based phase is optimal for the Frobenius norm, not always for the
# spectral norm, so in general this is an upper bound on the minimal phase-aligned
# spectral distance. For the diagonal, symmetric cases here the two coincide.
def distance(left, right):
    # Dense unitary matrices of both circuits.
    a, b = Operator(left).data, Operator(right).data
    # np.vdot flattens both and computes sum(conj(a_ij) * b_ij) = tr(a^dagger b).
    # If b = e^{i*phi} a, this equals e^{i*phi} * dim, so its angle is the phase offset;
    # if b is only close to e^{i*phi} a, its angle is still the best phase estimate.
    phase = np.vdot(a, b)
    # Keep only the unit-modulus phase factor e^{i*phi}. If the trace is zero (e.g. X vs Z),
    # there is no phase to read off, so fall back to 1 (no correction).
    phase = phase / abs(phase) if abs(phase) else 1
    # Spectral norm (largest singular value) of the difference after aligning the phase:
    # the most the two operations can disagree on any input state.
    return np.linalg.norm(b - phase * a, 2)


# Case 1: the pass alone on a single qubit.
q = QuantumCircuit(1)
# First small rotation.
q.rz(6e-5, 0)
# Second small rotation; the pass merges the two into RZ(1.2e-4).
q.rz(6e-5, 0)
# Run CommutativeCancellation directly; it drops the merged rotation as if it were zero.
out = CommutativeCancellation()(q)
# Environment details for the report.
print("qiskit", importlib.metadata.version("qiskit"))
print("python", platform.python_version(), "platform", sys.platform)
# Reproduced when every gate was removed and the phase-aligned distance exceeds
# the explicit error threshold. Operator.equiv is printed only as a diagnostic.
single_distance = distance(q, out)
single = not out.count_ops() and single_distance > ERROR_THRESHOLD
# Control: the same total angle written as one gate, so there is nothing to merge.
control = QuantumCircuit(1)
# One RZ(1.2e-4), equal to the merged rotation from case 1.
control.rz(1.2e-4, 0)
# Run the same pass on the control circuit.
control_out = CommutativeCancellation()(control)
# Case 1 result: remaining gates, equivalence check, distance and verdict.
print("single_pass", dict(out.count_ops()), "equiv", Operator(q).equiv(Operator(out)), "distance", f"{single_distance:.9g}", "REPRODUCED" if single else "NOT_REPRODUCED")
# Control result: the single RZ should be kept and the circuit should stay equivalent.
print("control_single_rz", dict(control_out.count_ops()), "equiv", Operator(control).equiv(Operator(control_out)))

# Case 2: the same rotations separated by gates they commute with, through the preset pipeline.
q = QuantumCircuit(3)
# First small rotation on qubit 0.
q.rz(6e-5, 0)
# CX controlled on qubit 0; RZ on the control commutes with it.
q.cx(0, 1)
# A second CX on the same control, also commuting with RZ on qubit 0.
q.cx(0, 2)
# Second small rotation on qubit 0; commutation analysis lets it merge with the first.
q.rz(6e-5, 0)
# Expected faulty result: both RZ rotations disappear, leaving these two CX gates.
expected_out = QuantumCircuit(3)
expected_out.cx(0, 1)
expected_out.cx(0, 2)
# Optimization levels 2 and 3 both include CommutativeCancellation.
for level in (2, 3):
    # Transpile to a fixed basis with a fixed seed so the run is deterministic.
    out = transpile(q, basis_gates=["cx", "rz", "sx", "x"], optimization_level=level, seed_transpiler=1)
    # Identify the expected loss of the rotations, with an error above the threshold.
    # An unrelated transpilation error must not be reported as this cutoff bug.
    preset_distance = distance(q, out)
    reproduced = (
        preset_distance > ERROR_THRESHOLD
        and distance(expected_out, out) <= MATCH_TOLERANCE
    )
    # Per-level result: remaining gates, equivalence check, distance and verdict.
    print("preset", level, dict(out.count_ops()), "equiv", Operator(q).equiv(Operator(out)), "distance", f"{preset_distance:.9g}", "REPRODUCED" if reproduced else "NOT_REPRODUCED")
