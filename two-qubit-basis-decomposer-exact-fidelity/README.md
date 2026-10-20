# Exact-fidelity options still permit tiny-angle approximation

`TwoQubitBasisDecomposer(CXGate(), basis_fidelity=1.0)` emits zero CX gates for `CP(theta)` at `theta=1e-5`, `5e-5`, and `1e-4`, including with `approximate=False`. On Qiskit 2.6.0 and the recorded main runtime at `f70269034d2ec07699d6c69e33594273c73f8df2`, the result fails phase-aligned equivalence at absolute tolerance `1e-12` and zero relative tolerance. At `theta=1e-4`, the maximum entry error is about `2.5e-5` and average gate infidelity is about `5e-10`.

This is an issue about behavior and the API description: the `__call__` argument docs say that `approximate` "Approximates if basis fidelities are less than 1.0." The observed error fits the Weyl specialization fidelity default of `1 - 1e-9` even when the basis-fidelity options request exactness.

```sh
python repro.py
```

The script prints JSON with both call modes, the error and infidelity, an exact identity control, a non-global X corruption control, and direct Weyl decomposition with and without specialization. `Operator.equiv` is also reported; its own tolerance can accept a tiny-angle result that the stricter comparison rejects.

| CP angle | `approximate=False` CX count | Phase-aligned maximum entry error | Average gate infidelity |
|---|---|---|---|
| 0 | 0 | 0 | 0 |
| `1e-5` | 0 | about `2.5e-6` | about `5e-12` |
| `1e-4` | 0 | about `2.5e-5` | about `5e-10` |

Likely cause: the native basis decomposer constructs its target Weyl decomposition with `Some(DEFAULT_FIDELITY)`, where `DEFAULT_FIDELITY = 1 - 1e-9`, independently of the basis-use setting. For `CP(1e-4)`, direct `TwoQubitWeylDecomposition` with the default reproduces the error; setting `fidelity=None` passes the strict check with maximum error about `3.2e-16`. This isolates a plausible source of the behavior; no source fix is included.

Source at the recorded main pin:

- [Python `__call__` argument docs and forwarding](https://github.com/Qiskit/qiskit/blob/f70269034d2ec07699d6c69e33594273c73f8df2/qiskit/synthesis/two_qubit/two_qubit_decompose.py#L510).
- [Native basis-use and target Weyl construction](https://github.com/Qiskit/qiskit/blob/f70269034d2ec07699d6c69e33594273c73f8df2/crates/synthesis/src/two_qubit_decompose/basis_decomposer.rs#L674).
- [Default specialization fidelity](https://github.com/Qiskit/qiskit/blob/f70269034d2ec07699d6c69e33594273c73f8df2/crates/synthesis/src/two_qubit_decompose/common.rs#L25).

[Release output](outputs/release-2.6.0-fresh.json), [recorded main output](outputs/main-f702690.json), and [runtime details](outputs/MAIN-RUNTIME.md) retain the measurements and provenance. The main runtime uses the recorded built native extension with the Python sources copied from main f702690; the runtime details state this explicitly. Item 12 concerns a separate rotation cutoff in `CommutativeCancellation`.
