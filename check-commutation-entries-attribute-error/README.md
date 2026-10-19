# CommutationChecker.check_commutation_entries raises AttributeError

The `check_commutation_entries` method on the session checker raises `AttributeError` in the reproduced versions. The wrapper imported through `qiskit.circuit.commutation_library` is defined as `SessionCommutationChecker.check_commutation_entries` in `qiskit/circuit/commutation_checker.py`.

Run `python repro.py`. The expected reproduced result is an `AttributeError` mentioning `library`; a future working return prints `NOT_REPRODUCED`.

Observed outputs are [release 2.6.0](outputs/release-2.6.0.txt) and [main ef112241](outputs/main-ef112241.txt). Both stored runs used Python 3.13.14 on macOS arm64 (`darwin`). Main was built from commit `ef11224130eecc78d46e3b84f11e2155a5cb6556`; SHA-256 of the compiled Qiskit extension used: `6ad1fcd9daff14bc821e94dc4d3542c17ba5b6e0cf9fc2ed9c465d4f36b04780`.

Candidate fix, not tested: expose a supported accelerated method for this lookup, or change the wrapper to call an already exposed method.

Related context: [#12870](https://github.com/Qiskit/qiskit/pull/12870) introduced the surrounding commutation-checker interface. We did not find a matching upstream issue in the earlier search; that search was not exhaustive.
