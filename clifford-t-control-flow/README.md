# Clifford+T transpilation fails on `if_else`

Qiskit fails to compile a one-qubit circuit that measures the qubit and applies
`X` when the result is 1. Both gates, `H` and `X`, already belong to the
requested Clifford+T basis.

[repro.py](repro.py) contains one circuit and one `transpile()` call, with
line-by-line comments. Including `t` and `tdg` in the basis selects the
Clifford+T pipeline; the circuit itself needs no T gates.

## Run

From the repository root, using the project's Qiskit 2.6.0 environment:

```bash
venv/bin/python clifford-t-control-flow/repro.py
```

**Expected:** compilation succeeds and preserves the conditional `X`.

**Actual:** `BasisTranslator` raises `TranspilerError` with
`Unable to translate the operations in the circuit`, mentioning `if_else`.
The script shows the traceback and exits nonzero. On a successful version,
it prints `COMPILED`.


## Cause

In Qiskit 2.6.0,
[`TranslateToCliffordRZPassManager`](https://github.com/Qiskit/qiskit/blob/2.6.0/qiskit/transpiler/preset_passmanagers/builtin_plugins.py#L1124-L1159)
builds an intermediate basis containing Clifford gates, `t`, `tdg`, and `rz`,
but omits `if_else`. The translator therefore rejects the conditional container,
even though its `X` gate is supported.
