"""Portable control for ``TwoQubitBasisDecomposer.num_basis_gates``.

This is a diagnostic, not a replacement estimator.  It compares the public
estimate and the emitted CX count, while independently checking that the
H--SWAP target is locally equivalent to SWAP.  The Makhlin tuple below is
computed directly from the magic-basis matrix; its normalization by det(U)
makes it invariant under a global phase.
"""

import importlib.metadata
import platform
import sys

import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import CXGate
from qiskit.quantum_info import Operator
from qiskit.synthesis import TwoQubitBasisDecomposer, TwoQubitWeylDecomposition
try:
    from qiskit._accelerate.two_qubit_decompose import weyl_coordinates
except ImportError:
    weyl_coordinates = None


MAGIC = np.array(
    [[1, 0, 0, 1j], [0, 1j, 1, 0], [0, 1j, -1, 0], [1, 0, 0, -1j]],
    dtype=complex,
) / np.sqrt(2)


def makhlin_tuple(unitary):
    """Return phase-normalized Makhlin invariants without Qiskit helpers."""
    ub = MAGIC.conj().T @ unitary @ MAGIC
    m = ub.T @ ub
    determinant = np.linalg.det(unitary)
    trace = np.trace(m)
    return np.array(
        [trace * trace / (16 * determinant), (trace * trace - np.trace(m @ m)) / (4 * determinant)]
    )


def operator_schmidt_rank(unitary):
    """Rank across the two-qubit operator bipartition; rank one means local."""
    reshaped = unitary.reshape(2, 2, 2, 2).transpose(0, 2, 1, 3).reshape(4, 4)
    return int(np.linalg.matrix_rank(reshaped, tol=1e-10))


def estimate_from_synthesis_weyl(matrix, basis_fidelity=1.0):
    """Replicate the selector using the robust decomposition coordinates.

    ``TwoQubitBasisDecomposer.__call__`` obtains these coordinates through the
    full Weyl decomposition.  This function only tests the proposed one-line
    data-source substitution in the estimator; it does not alter Qiskit.
    """
    target = TwoQubitWeylDecomposition(matrix)
    a, b, c = target.a, target.b, target.c
    traces = (
        4 * complex(np.cos(a) * np.cos(b) * np.cos(c), np.sin(a) * np.sin(b) * np.sin(c)),
        4 * complex(np.cos(np.pi / 4 - a) * np.cos(-b) * np.cos(c), np.sin(np.pi / 4 - a) * np.sin(-b) * np.sin(c)),
        complex(4 * np.cos(c), 0),
        complex(4, 0),
    )
    scores = [((4 + abs(trace) ** 2) / 20) * basis_fidelity**index for index, trace in enumerate(traces)]
    return int(np.argmax(scores))


def unitary(builder):
    circuit = QuantumCircuit(2)
    builder(circuit)
    return Operator(circuit).data


def row(name, matrix, decomposer):
    synthesized = decomposer(matrix)
    weyl = TwoQubitWeylDecomposition(matrix)
    print(
        name,
        "estimate=", decomposer.num_basis_gates(matrix),
        "estimate_from_synthesis_weyl=", estimate_from_synthesis_weyl(matrix),
        "actual=", len(synthesized.get_instructions("cx")),
        "equiv=", Operator(synthesized).equiv(Operator(matrix)),
        "rank=", operator_schmidt_rank(matrix),
        "coordinates=", np.round(weyl_coordinates(matrix), 12),
        "decomposition_coordinates=", np.round([weyl.a, weyl.b, weyl.c], 12),
        "makhlin=", np.round(makhlin_tuple(matrix), 12),
    )


def main():
    if weyl_coordinates is None:
        print("DIAGNOSTIC_UNAVAILABLE: private Weyl-coordinate API moved; run public repro.py")
        return
    decomposer = TwoQubitBasisDecomposer(CXGate(), basis_fidelity=1.0)
    identity = unitary(lambda q: None)
    dcnot = unitary(lambda q: (q.cx(0, 1), q.cx(1, 0)))
    swap = unitary(lambda q: q.swap(0, 1))
    h_swap = unitary(lambda q: (q.h(0), q.swap(0, 1)))
    h_after_swap = unitary(lambda q: (q.swap(0, 1), q.h(0)))
    rz_swap = unitary(lambda q: (q.rz(0.37, 0), q.swap(0, 1)))
    cx = unitary(lambda q: q.cx(0, 1))
    print("qiskit", importlib.metadata.version("qiskit"))
    print("python", platform.python_version(), "platform", sys.platform)
    row("identity", identity, decomposer)
    row("cx", cx, decomposer)
    row("dcnot", dcnot, decomposer)
    row("swap", swap, decomposer)
    row("h_swap", h_swap, decomposer)
    row("swap_h", h_after_swap, decomposer)
    row("rz_swap", rz_swap, decomposer)
    print("h_swap_matches_swap_makhlin=", np.allclose(makhlin_tuple(h_swap), makhlin_tuple(swap)))
    print("h_swap_rank_excludes_zero_cx=", operator_schmidt_rank(h_swap) != 1)
    for phase in (0.0, 0.1, 1.0):
        phased = np.exp(1j * phase) * h_swap
        print("phase=", phase, "estimate=", decomposer.num_basis_gates(phased), "coords=", np.round(weyl_coordinates(phased), 12))


if __name__ == "__main__":
    main()
