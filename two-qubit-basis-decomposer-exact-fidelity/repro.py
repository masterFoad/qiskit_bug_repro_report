"""Standalone exact-fidelity CP tiny-angle synthesis check; no grader dependency."""
from __future__ import annotations

import json
import platform

import numpy as np
import qiskit
from qiskit import QuantumCircuit
from qiskit.circuit.library import CXGate
from qiskit.quantum_info import Operator, average_gate_fidelity
from qiskit.synthesis import TwoQubitBasisDecomposer, TwoQubitWeylDecomposition


STRICT_ATOL = 1e-12


def phase_aligned(actual: np.ndarray, expected: np.ndarray) -> np.ndarray:
    """Return actual after its best trace-overlap global-phase alignment."""
    overlap = np.trace(expected.conj().T @ actual)
    return actual * np.exp(-1j * np.angle(overlap)) if abs(overlap) else actual


def independent_error(actual: np.ndarray, expected: np.ndarray) -> tuple[float, float]:
    """Report phase-aligned max entry error and average infidelity."""
    aligned = phase_aligned(actual, expected)
    return float(np.max(np.abs(aligned - expected))), float(1 - average_gate_fidelity(Operator(actual), Operator(expected)))


def row(theta: float, approximate: bool) -> dict[str, object]:
    source = QuantumCircuit(2)
    source.cp(theta, 0, 1)
    target = Operator(source).data
    output = TwoQubitBasisDecomposer(CXGate(), basis_fidelity=1.0)(target, approximate=approximate)
    actual = Operator(output).data
    maximum, infidelity = independent_error(actual, target)
    return {
        "theta": theta,
        "approximate": approximate,
        "cx_count": output.count_ops().get("cx", 0),
        "phase_aligned_max_entry_error": maximum,
        "average_gate_infidelity": infidelity,
        "operator_equiv": bool(Operator(output).equiv(Operator(source))),
        "phase_aligned_strict_atol_1e-12_equiv": bool(
            np.allclose(phase_aligned(actual, target), target, atol=STRICT_ATOL, rtol=0.0)
        ),
    }


def controls() -> dict[str, object]:
    """Prove the independent metrics accept an exact control and reject an X corruption."""
    identity = np.eye(4, dtype=complex)
    zero = row(0.0, approximate=False)
    zero_maximum, zero_infidelity = independent_error(Operator(QuantumCircuit(2)).data, identity)
    corrupted = QuantumCircuit(2)
    corrupted.x(0)
    x_maximum, x_infidelity = independent_error(Operator(corrupted).data, identity)
    if zero["phase_aligned_max_entry_error"] != 0.0 or zero["average_gate_infidelity"] != 0.0:
        raise AssertionError("theta=0 synthesis is not exact")
    if zero_maximum != 0.0 or zero_infidelity != 0.0:
        raise AssertionError("independent metrics reject the exact identity control")
    if x_maximum == 0.0 or x_infidelity == 0.0:
        raise AssertionError("independent metrics failed to reject non-global X corruption")
    return {
        "theta_0_output": zero,
        "identity_control": {
            "phase_aligned_max_entry_error": zero_maximum,
            "average_gate_infidelity": zero_infidelity,
        },
        "non_global_x_corruption": {
            "phase_aligned_max_entry_error": x_maximum,
            "average_gate_infidelity": x_infidelity,
        },
    }


def weyl_fidelity_control(theta: float = 1e-4) -> dict[str, object]:
    """Isolate the Weyl specialization default from basis-use selection."""
    source = QuantumCircuit(2)
    source.cp(theta, 0, 1)
    target = Operator(source).data

    def measure(fidelity: float | None) -> dict[str, object]:
        actual = Operator(TwoQubitWeylDecomposition(target, fidelity=fidelity).circuit()).data
        maximum, infidelity = independent_error(actual, target)
        return {
            "fidelity": fidelity,
            "phase_aligned_max_entry_error": maximum,
            "average_gate_infidelity": infidelity,
            "phase_aligned_strict_atol_1e-12_equiv": bool(
                np.allclose(phase_aligned(actual, target), target, atol=STRICT_ATOL, rtol=0.0)
            ),
        }

    default = measure(0.999999999)
    disabled = measure(None)
    if default["phase_aligned_strict_atol_1e-12_equiv"]:
        raise AssertionError("Weyl default specialization did not exercise the tiny-angle boundary")
    if not disabled["phase_aligned_strict_atol_1e-12_equiv"]:
        raise AssertionError("Weyl fidelity=None control was not strict-equivalent")
    return {"theta": theta, "default_fidelity": default, "fidelity_none": disabled}


print(json.dumps({
    "qiskit": qiskit.__version__,
    "python": platform.python_version(),
    "basis_fidelity": 1.0,
    "strict_atol": STRICT_ATOL,
    "controls": controls(),
    "default_approximate": [row(theta, approximate=True) for theta in (0.0, 1e-5, 5e-5, 1e-4)],
    "approximate_false": [row(theta, approximate=False) for theta in (0.0, 1e-5, 5e-5, 1e-4)],
    "weyl_fidelity_control": weyl_fidelity_control(),
}, sort_keys=True, indent=2))
