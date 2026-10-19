# Near-identity rotations bypass checks for non-unitary instructions

The commutation checker reports that `RY(0)` and `RY(1e-7)` commute with a same-wire barrier, measurement, and reset, while it reports `False` for `RY(1e-3)`. This pattern is consistent with the near-identity shortcut running before the check that excludes non-unitary instructions. The relevant source functions are `CommutationChecker::commute` and `commutation_precheck` in `crates/transpiler/src/commutation_checker.rs`.

Run `python repro.py`. `RY(0.0)` is the exact-identity control, so its `True` answer is expected. Each row prints `REPRODUCED` only for the expected `True True False` sequence, otherwise `NOT_REPRODUCED`. The sampled `1e-7` and `1e-3` angles bracket the historical threshold near `2.45e-6` radians in [the findings note](../commutation-checker-findings.md). That threshold was measured for RY versus Z on the shortcut path, not for barrier, measurement or reset.

Observed outputs are [release 2.6.0](outputs/release-2.6.0.txt) and [main ef112241](outputs/main-ef112241.txt). Both stored runs used Python 3.13.14 on macOS arm64 (`darwin`). Main was built from commit `ef11224130eecc78d46e3b84f11e2155a5cb6556`; SHA-256 of the compiled Qiskit extension used: `6ad1fcd9daff14bc821e94dc4d3542c17ba5b6e0cf9fc2ed9c465d4f36b04780`.

Candidate fix, not tested: check for control-flow and non-unitary instructions before using the near-identity shortcut, or restrict that shortcut to a pair of unitary operations.

Related upstream work on the separate question of measurement commutation is [#15938](https://github.com/Qiskit/qiskit/issues/15938) and [#15964](https://github.com/Qiskit/qiskit/pull/15964). This report does not claim those items cover this ordering case.
