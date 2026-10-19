# The commutation library trusts a custom gate's standard name

A user-defined gate named `z` whose definition is X is reported to commute with S. Its commutator has spectral norm `sqrt(2)`, approximately `1.4142`. `CommutativeInverseCancellation` then removes the surrounding S/Sdg pair and changes the unitary.

Run `python repro.py`. It reports the checker answer, a direct matrix calculation, and whether the end-to-end pass changed the circuit's unitary.

Observed outputs are [release 2.6.0](outputs/release-2.6.0.txt) and [main ef112241](outputs/main-ef112241.txt). Both stored runs used Python 3.13.14 on macOS arm64 (`darwin`). Main was built from commit `ef11224130eecc78d46e3b84f11e2155a5cb6556`; SHA-256 of the compiled Qiskit extension used: `6ad1fcd9daff14bc821e94dc4d3542c17ba5b6e0cf9fc2ed9c465d4f36b04780`.

This is a design issue involving names reserved for standard gates. Qiskit also uses operation names to identify gate types elsewhere in the compiler. One possible fix is to check that an operation has the expected standard-gate type before consulting the standard commutation table. For custom operations, the checker could calculate the matrices or return False if it cannot establish commutation. This change is untested; the supported meaning of a custom operation with a standard name needs clarification.

Related upstream context: [#13988](https://github.com/Qiskit/qiskit/issues/13988) and [#13991](https://github.com/Qiskit/qiskit/pull/13991) addressed a different overloaded-name failure. They do not establish this false-positive behaviour as an upstream bug.
