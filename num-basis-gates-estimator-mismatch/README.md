# num_basis_gates disagrees with the decomposition it estimates

For the unitary of `H; SWAP`, `TwoQubitBasisDecomposer(CX, basis_fidelity=1.0).num_basis_gates` returns 0, while the decomposer emits an equivalent circuit with 3 CX gates. Plain SWAP and the minimal script's four alternating CX gates agree with the estimator; the separate diagnostic also checks the 0/1/2/3-CX classes.

Run `python repro.py`. The script labels each case `MATCH` or `MISMATCH`. It does not claim that the synthesized circuit is incorrect; the observed issue is the estimator/decomposition disagreement.

Observed outputs are [release 2.6.0](outputs/release-2.6.0.txt) and [main ef112241](outputs/main-ef112241.txt). Both stored runs used Python 3.13.14 on macOS arm64 (`darwin`). Main reports Qiskit 2.7.0.dev0 and was built from commit `ef11224130eecc78d46e3b84f11e2155a5cb6556`; SHA-256 of the compiled Qiskit extension used: `6ad1fcd9daff14bc821e94dc4d3542c17ba5b6e0cf9fc2ed9c465d4f36b04780`.

The diagnostic finds two different sets of Weyl coordinates for `H; SWAP`. These coordinates describe the two-qubit interaction after removing single-qubit operations. The standalone calculation returns `[0, 0, 0]`, while the full decomposition used by synthesis returns `[pi/4, pi/4, pi/4]`, the coordinates of SWAP. Source reading suggests the estimator uses the standalone calculation; this script does not trace the estimator's internal calls.

Changing a physically irrelevant global phase changes the estimate: phase 0.0 gives 0 CX, while phases 0.1 and 1.0 give 3. Independent Makhlin invariants and operator Schmidt rank also identify the SWAP interaction. In particular, the rank excludes a circuit made entirely of single-qubit gates, so zero CX cannot be an exact count.

One possible fix is to use the same full decomposition to obtain the estimator's coordinates, then keep its existing comparison of candidate decompositions. This change has not been patched into Qiskit. In the separate diagnostic, calculating the estimate this way gives 3 for both `H; SWAP` and `SWAP; H`, and preserves the known 0/1/2/3-CX examples on release and main.

This matters when the estimate feeds cost or strategy choices. We did not find a matching upstream issue in the earlier search; that search was not exhaustive. `repro.py` uses only public APIs; the separate `diagnose.py` intentionally uses a private coordinate helper and is a diagnostic, not a portable public-API reproducer.

Run `python diagnose.py` for the coordinate, invariant, 0/1/2/3-CX and global-phase controls. Stored outputs: [release diagnostic](outputs/diagnosis-release-2.6.0.txt) and [main diagnostic](outputs/diagnosis-main-ef112241.txt). The source paths are `crates/synthesis/src/two_qubit_decompose/weyl_decomposition.rs` (`__num_basis_gates` and `__weyl_coordinates`) and `basis_decomposer.rs` (`call_inner`) at the main commit above. The diagnostic estimates CX counts with basis fidelity 1.0 only; other basis gates or fidelities need separate tests.
