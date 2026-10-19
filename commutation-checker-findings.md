# CommutationChecker findings and limits

This note summarizes the broader commutation-checker investigation that motivated the five standalone reproductions in this repository. The five items were freshly rerun on released Qiskit 2.6.0 and upstream main commit `ef11224130eecc78d46e3b84f11e2155a5cb6556`. The counts, thresholds, and timings below come from an earlier investigation on one machine; its raw measurements are not included in this repository.

## Numerical tolerance is not exact commutation

`CommutationChecker` uses a minimum average-gate-infidelity tolerance of `1e-12`; increasing `approximation_degree` to 1 or above does not make that floor smaller. A near-identity rotation can therefore be accepted as commuting even when its matrix does not commute exactly. For example, the earlier measurements found thresholds of about `2.45e-6` radians for `RY(theta)` versus Z on the shortcut path, and about `1.22e-6` radians for a one-qubit matrix-path example.

This is documented numerical behavior, not floating-point roundoff. It is related to [Qiskit issue #13547](https://github.com/Qiskit/qiskit/issues/13547), [pull request #13874](https://github.com/Qiskit/qiskit/pull/13874), [issue #16782](https://github.com/Qiskit/qiskit/issues/16782), and [issue #14115](https://github.com/Qiskit/qiskit/issues/14115). The discussion in #16782 concerns which approximation settings should allow this tolerance; it does not establish a checker defect.

A per-decision tolerance does not bound a whole circuit. The earlier investigation applied repeated `CX; RX(1e-6); CX` crossings through `CommutativeCancellation`. The phase-aligned operator error grew approximately linearly with the number of crossings: about `N * 1e-6`, reaching about `1e-3` at 1,000 crossings and `1e-2` at 10,000. Item 12 (merged-angle cutoff) is separate: it is a fixed merged-angle cutoff in `CommutativeCancellation`, not the checker's `1e-12` floor.

## Symbolic parameters are conservative in several valid cases

The checker rejects many parameterized cases before the generic matrix path. In the earlier 41-pair sample, the comparison used six random parameter bindings per pair: 12 sampled valid commutations were missed, 26 were accepted correctly, 3 were rejected correctly, and no wrong `True` answer was found. The lost cases included symbolic RZZ or CRZ through an exact diagonal `UnitaryGate`, several symbolic U-family relations, and symbolic `XXPlusYY` relations.

This is a sampled completeness limitation, not a universal proof over symbolic values. It can leave optimization opportunities unused, but the sampled result does not show a symbolic false positive. The name-collision reproduction in this repository is a different failure mode: it is a non-standard operation presenting a standard operation name.

## No result cache in Qiskit 2.6

Qiskit 2.6 has no commutation-result cache; its deprecated cache-size API is a no-op. The earlier local microbenchmarks therefore did not measure warmed cache hits. They measured approximately 1 microsecond per table lookup or initial instruction check, 8 to 25 microseconds for small matrix paths, and roughly 42 to 45 microseconds when a custom-gate definition required an `Operator` construction. A Python dictionary lookup in that experiment was about 0.2 microseconds.

These are machine-specific local timings, not an end-to-end compiler performance claim. Rust/Python boundary costs, materializing operation objects, and matrix evaluation can matter more than the static commutation-library lookup. [Qiskit pull request #15988](https://github.com/Qiskit/qiskit/pull/15988) is the relevant cache-removal context.

## Operator.equiv is not an exact proof

`Operator.equiv` uses numerical allclose logic up to global phase. It is useful as a smoke check, but it can accept small nonzero errors and should not establish an exact rewrite. The scripts in this repository therefore print direct, more discriminating observations where needed: item 12 reports a phase-aligned operator distance; the name-collision item reports a spectral commutator norm and an end-to-end inequivalence result.

For a proof-level claim about an exact rewrite, use an exact symbolic/table argument for the supported gate class or a separately justified numerical method with a stated error bound. A tolerant checker answer alone is insufficient.

## Recommendation for exact routing rewrites

For a routing change that must preserve the circuit exactly, a table of exact commutation rules can cover supported standard gates. Check the operation type before using a table entry. For other operations, accept commutation only with a separate exact argument; otherwise leave their order unchanged. Numerical commutation checks can support approximate optimization or diagnostics when the allowed circuit error is stated explicitly.

The five focused reproductions linked from the root README cover the current concrete issues: the merged-angle cutoff, shortcut ordering, name-keyed lookup behavior, the broken session-checker wrapper, and the decomposition-estimator inconsistency. They do not establish that every checker path is unsound.
