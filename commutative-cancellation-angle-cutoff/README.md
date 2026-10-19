# CommutativeCancellation removes a non-identity merged rotation

`CommutativeCancellation` deletes two `RZ(6e-5)` rotations after merging them. Their total angle is `1.2e-4` radians, and the phase-aligned operator distance from the input is `6e-5`. A three-qubit construction with the rotations separated by CX gates becomes non-equivalent through preset optimization levels 2 and 3.

Run `python repro.py`. The script prints `REPRODUCED` or `NOT_REPRODUCED`; it does not fail when a future version fixes the behaviour. It also prints a one-gate `RZ(1.2e-4)` control, which survives because a one-gate run is not rewritten by the merge path.

Observed outputs are [release 2.6.0](outputs/release-2.6.0.txt) and [main ef112241](outputs/main-ef112241.txt). Both stored runs used Python 3.13.14 on macOS arm64 (`darwin`). Main was built from Qiskit commit `ef11224130eecc78d46e3b84f11e2155a5cb6556`; the SHA-256 of the compiled Qiskit extension used was `6ad1fcd9daff14bc821e94dc4d3542c17ba5b6e0cf9fc2ed9c465d4f36b04780`.

The relevant source is `is_multiple_of_pi` in `crates/transpiler/src/passes/commutation_cancellation.rs`, which uses the fixed normalized-angle cutoff. The script uses the pass default `approximation_degree` and uses `seed_transpiler=1` for the preset cases; it does not sweep other seeds.

Candidate fix, not tested: replace the fixed normalized-angle cutoff with a comparison between the merged operation and the replacement operation that respects the pass's `approximation_degree` setting. Applying the same tolerance still needs a stated bound on the resulting circuit error.

Related upstream discussion: [#16782](https://github.com/Qiskit/qiskit/issues/16782) and [#14115](https://github.com/Qiskit/qiskit/issues/14115) discuss numerical tolerance in commutation cancellation. The fixed cutoff reproduced here has not been independently matched to an upstream issue in this report.
