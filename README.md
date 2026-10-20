# Qiskit bug reproductions

Minimal, standalone reproductions of eighteen observed problems in Qiskit, Qiskit Aer, and
qiskit-ibm-runtime: wrong or hardware-invalid results, compilation and serialization failures,
misleading fake-backend calibration entries, repeated synthesis work, and seeded metric drift.
Each item has a short script, the output we observed, and the versions tested. Related upstream
issues are linked below (the 2026-10-14 searches cover items 1-11; search context for
items 12-16 is described in their folder READMEs). Bugs 2 and 4 demonstrate a reserved-name
contract trap; they are not established defects for supported custom-gate names. Bug 8 also uses
a reserved name. Items 12-16 add current commutation and gate-count-estimator findings;
item 14 also exposes reserved-name assumptions.

## Start here: three to look at first

Chosen for impact and because each is quick to explain: a silently wrong compiled circuit, a regression with a candidate fix,
and a compiled circuit that is invalid for the device. The full list below is in suggested priority order.

| Rank | # | Item | Why first |
|---|---|---|---|
| 1 | 12 | [CommutativeCancellation removes a non-identity merged rotation](commutative-cancellation-angle-cutoff/) | Silent non-equivalent output in default optimization levels 2 and 3 |
| 2 | 5 | [Clifford+T translation fails on control flow](#5-cliffordt-translation-fails-on-control-flow) | Regression since 2.4.0: dynamic circuits cannot be compiled to Clifford+T |
| 3 | 3 | [`rzz` angles inside control-flow bodies are not brought into the target's bounds](#3-rzz-angle-bounds-not-enforced-inside-control-flow) | Compiled dynamic circuits are invalid on fractional-gate targets |

Also worth a look:

- **#6** [QPY writes arithmetic gates but cannot read them](#6-qpy-writes-arithmetic-gates-but-cannot-read-them): saved circuits cannot be loaded back.
- **#1** [Noise applied twice in a density-matrix circuit that follows a statevector circuit](#1-aer-noise-applied-twice): silent wrong simulation results (`trace(rho) = 2`); this one is in qiskit-aer.

## TL;DR

All eighteen items, in suggested priority order (most important first). The `#` column keeps each item's
original number, which the section headings and folders below use.

| Priority | # | Item | Library | Effect | Status as tested |
|---|---|---|---|---|---|
| 1 | 12 | [CommutativeCancellation removes a non-identity merged rotation](commutative-cancellation-angle-cutoff/) | qiskit | Non-equivalent at O2/O3 (6e-5 operator distance; seed 1, no sweep) | Reproduced in 2.6.0 and main ef112241 |
| 2 | 5 | [Clifford+T translation fails on control flow](#5-cliffordt-translation-fails-on-control-flow) | qiskit | Compilation raises TranspilerError | Broken since 2.4.0; works on 2.3.1 |
| 3 | 3 | [`rzz` angles inside control-flow bodies are not brought into the target's bounds](#3-rzz-angle-bounds-not-enforced-inside-control-flow) | qiskit | Output is invalid for fractional-gate targets | Broken in 2.5.2 |
| 4 | 6 | [QPY writes arithmetic gates but cannot read them](#6-qpy-writes-arithmetic-gates-but-cannot-read-them) | qiskit | Saved circuits cannot be loaded | Broken in 2.5.2 |
| 5 | 1 | [Noise applied twice in a density-matrix circuit that follows a statevector circuit](#1-aer-noise-applied-twice) | qiskit-aer | Silent wrong result: trace(rho) = 2 | Broken in 0.17.2 and on main |
| 6 | 7 | [QPY cannot read wide MCX gates](#7-qpy-cannot-read-wide-mcx-gates) | qiskit | Wide controlled gates cannot be loaded | 63/127 fail in 2.5.2; 32 also fails on checked main |
| 7 | 16 | [num_basis_gates disagrees with its decomposition](num-basis-gates-estimator-mismatch/) | qiskit | Estimate 0 CX for H;SWAP, equivalent synthesis emits 3 | Reproduced in 2.6.0 and main ef112241; diagnosed, unpatched |
| 8 | 13 | [Near-identity rotations bypass checks for non-unitary instructions](commutation-near-identity-before-precheck/) | qiskit | Non-unitary instructions get a unitary shortcut | Reproduced in 2.6.0 and main ef112241 |
| 9 | 17 | [Same seed can produce different initial layouts](layout-initial-layout-variability/) | qiskit | Fixed-environment initial placement varies for one 16q fixture | Observed in 2.6.0 and recorded main f702690; reproducibility issue |
| 10 | 11 | [Seeded synthesis is not run-to-run deterministic](#11-seeded-synthesis-is-not-run-to-run-deterministic) | qiskit | Same seed produces different RZ counts | Broken in 2.5.2 |
| 11 | 2 | [A custom gate named `rz` is kept as the native `rz`](#2-custom-gate-named-rz-kept-as-native-rz) | qiskit | Silent wrong result on hardware | Broken in 2.5.2 (also 2.4.2) |
| 12 | 14 | [The commutation library trusts a custom gate's standard name](commutation-library-name-collision/) | qiskit | Reserved-name custom gate can be reordered incorrectly | Reproduced in 2.6.0 and main ef112241; design issue |
| 13 | 4 | [A custom gate named `cx` is kept as the native `cx`](#4-custom-gate-named-cx-kept-as-native-cx) | qiskit | Native-device semantics differ from the definition | Observed in 2.5.2; reserved-name contract |
| 14 | 9 | [IBM fake backends advertise couplers with error 1.0](#9-ibm-fake-backends-advertise-couplers-with-error-10) | qiskit-ibm-runtime | Target contains unusable calibration entries | Present in 0.50.0 |
| 15 | 10 | [O3 repeatedly emits out-of-bounds rzz and retranslates](#10-o3-repeatedly-emits-out-of-bounds-rzz-and-retranslates) | qiskit | Extra synthesis work; compilation terminates | Broken in 2.5.2 |
| 16 | 8 | [GateDirection raises on a reversed custom ECR](#8-gatedirection-raises-on-a-reversed-custom-ecr) | qiskit | Compilation raises TranspilerError | Broken in 2.5.2 |
| 17 | 18 | [Exact-fidelity options still permit tiny-angle approximation](two-qubit-basis-decomposer-exact-fidelity/) | qiskit | CP(1e-4) emits 0 CX with infidelity about 5e-10, even with approximate=False | Observed in 2.6.0 and recorded main f702690; API behavior issue |
| 18 | 15 | [check_commutation_entries raises AttributeError](check-commutation-entries-attribute-error/) | qiskit | Method on the public session checker raises AttributeError | Reproduced in 2.6.0 and main ef112241 |

Items 1-11 retain their published test scope; they were not revalidated in the 2026-10-19 addition.
`CHANGES.md` covers that earlier 1-11 preparation only; the 12-16 section records this addition's
separate runtime and private-API diagnostic scope.

## Contents

- [Start here: three to look at first](#start-here-three-to-look-at-first)
- [Environment](#environment)
- [How to run](#how-to-run)
- [1. Aer: noise applied twice](#1-aer-noise-applied-twice)
- [2. Custom gate named rz kept as native rz](#2-custom-gate-named-rz-kept-as-native-rz)
- [4. Custom gate named cx kept as native cx](#4-custom-gate-named-cx-kept-as-native-cx)
- [3. rzz angle bounds not enforced inside control flow](#3-rzz-angle-bounds-not-enforced-inside-control-flow)
- [5. Clifford+T translation fails on control flow](#5-cliffordt-translation-fails-on-control-flow)
- [6. QPY writes arithmetic gates but cannot read them](#6-qpy-writes-arithmetic-gates-but-cannot-read-them)
- [7. QPY cannot read wide MCX gates](#7-qpy-cannot-read-wide-mcx-gates)
- [8. GateDirection raises on a reversed custom ECR](#8-gatedirection-raises-on-a-reversed-custom-ecr)
- [9. IBM fake backends advertise couplers with error 1.0](#9-ibm-fake-backends-advertise-couplers-with-error-10)
- [10. O3 repeatedly emits out-of-bounds rzz and retranslates](#10-o3-repeatedly-emits-out-of-bounds-rzz-and-retranslates)
- [11. Seeded synthesis is not run-to-run deterministic](#11-seeded-synthesis-is-not-run-to-run-deterministic)
- [12-16. Commutation and decomposition findings](#12-16-commutation-and-decomposition-findings)
- [17-18. Initial layout and exact-fidelity synthesis](#17-18-initial-layout-and-exact-fidelity-synthesis)
- [CommutationChecker findings and limits](commutation-checker-findings.md)
- [Reproducing the current main build](#reproducing-the-current-main-build)
- [Related items already fixed upstream](#related-items-already-fixed-upstream)
- [Repository layout](#repository-layout)

## Environment

Original outputs for bugs 1-3 were produced on Linux x86_64 with:

| Package | Version |
|---|---|
| Python | 3.13.16 |
| qiskit | 2.5.2 (bug 2 and 3 also run on 2.4.2 for comparison) |
| qiskit-aer | 0.17.2 |
| qiskit-ibm-runtime | 0.50.0 (only for the `FakeFez` target in bug 3) |

For items 1-11, all primary scripts were run locally; those outputs were regenerated
on macOS arm64 with Python 3.14.6,
Qiskit 2.5.2, Aer 0.17.2, and qiskit-ibm-runtime 0.50.0. The Clifford+T comparison was also run
locally on Qiskit 2.3.1. Every local script run had a 240-second timeout and completed in under
30 seconds, with at most two native numerical threads and one Qiskit process.

Files ending in `-recheck.txt` preserve earlier Linux x86_64 comparisons on Python 3.12.13.
For items 1-11, the checked main is Qiskit 2.7.0.dev0 at
`c841572607fb4db230f1cf4ba5488a3b7cd98f86` (2026-10-14); it was not built locally.
Their local dependency and comparison versions are in [`outputs/versions.txt`](outputs/versions.txt).
Items 12-16 use release 2.6.0 and locally built main 2.7.0.dev0 at
`ef11224130eecc78d46e3b84f11e2155a5cb6556` (2026-10-19), with Python 3.13.14.

## How to run

```bash
python3 -m venv ./venv && . venv/bin/activate
mkdir -p .cache/pip .cache/uv .cache/tmp
export PIP_CACHE_DIR="$PWD/.cache/pip" UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp"
export QISKIT_NUM_PROCS=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
pip install "qiskit==2.5.2" "qiskit-aer==0.17.2" "qiskit-ibm-runtime==0.50.0"

python aer-noise-applied-twice/repro.py
python custom-rz-name-kept-as-native/repro.py            # add --gadget for the 2-qubit case
python rzz-angle-bounds-in-control-flow/repro.py         # add --ibm-plugin for the comparison
python custom-cx-name-kept-as-native/repro.py
python clifford-t-control-flow/repro.py
python qpy-arithmetic-gates/repro.py
python qpy-wide-mcx/repro.py
python reversed-custom-ecr/repro.py
python fake-backend-error-one-couplers/repro.py
python o3-rzz-retranslation/repro.py
python seeded-synthesis-nondeterminism/repro.py
```

Each script prints its package versions first, then the results. The added scripts for
items 4-11, and the separate scripts for 12-16, also print Python.
Expected failures are caught and printed without a traceback; a successful process exit does not mean
the defect is fixed. No account or hardware access is needed.

The five additional items use a separate Qiskit-only environment:

```bash
python3 -m venv ./venv-2.6 && . venv-2.6/bin/activate
pip install "qiskit==2.6.0"
export QISKIT_NUM_PROCS=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
python commutative-cancellation-angle-cutoff/repro.py
python commutation-near-identity-before-precheck/repro.py
python commutation-library-name-collision/repro.py
python check-commutation-entries-attribute-error/repro.py
python num-basis-gates-estimator-mismatch/repro.py
python num-basis-gates-estimator-mismatch/diagnose.py
```

---

## 1. Aer: noise applied twice

**TL;DR:** in one `AerSimulator.run()` call with `method="automatic"`, if a statevector circuit runs before a
density-matrix circuit and the noise model contains a Kraus (non-unitary) error, the density-matrix circuit's
noise is applied twice. `trace(rho)` becomes 2 and the counts are wrong. Nothing warns.

**Who is affected:** anyone who runs mixed circuit sizes in one call on a noisy simulator, for example
`SamplerV2` / `EstimatorV2` with a fake backend, or `BackendSamplerV2`, where the method is chosen per circuit.

**Script:** [`aer-noise-applied-twice/repro.py`](aer-noise-applied-twice/repro.py)

**Expected vs actual** (amplitude damping 0.2 after `x` on `|0>`; exact result `diag(rho) = [0.2, 0.8]`):

| Batch | Methods chosen | diag(rho) | trace | counts (2000 shots) |
|---|---|---|---|---|
| small circuit alone | density_matrix | [0.2, 0.8] | 1.0 | 0: 416, 1: 1584 |
| [small, big] | density_matrix, statevector | [0.2, 0.8] | 1.0 | 0: 416, 1: 1584 |
| **[big, small]** | statevector, density_matrix | **[0.4, 1.6]** | **2.0** | **0: 816, 1: 1184** |

Full outputs: [`outputs/aer_noise_applied_twice.txt`](outputs/aer_noise_applied_twice.txt),
[`outputs/aer-noise-applied-twice-local.txt`](outputs/aer-noise-applied-twice-local.txt)

**Likely cause:** when the superoperator form of the noise is computed for the density-matrix circuit,
`superoperator_.initialize(dim, dim)` keeps the previous values when the size is unchanged, and the
following `superoperator_ += p_j * S_j` accumulates on top of the earlier result, so `S` becomes `2S`
(`quantum_error.hpp`, unchanged on main as of 2026-10-13). Zeroing the matrix before accumulating should fix it.

**Workarounds:** set `method` explicitly, run one circuit per `run()`, or put density-matrix circuits first.

---

## 2. Custom gate named rz kept as native rz

**TL;DR:** a user-defined `Gate("rz", 1, [theta])` whose definition is `ry(theta)` comes out of `transpile`
as the target's native `rz`. On hardware it would execute as a real RZ, which is a different operation.

**Who is affected:** users and libraries that define custom gates whose names collide with basis gate names.

**Script:** [`custom-rz-name-kept-as-native/repro.py`](custom-rz-name-kept-as-native/repro.py)

**Expected vs actual:**

| Case | Expected | Actual |
|---|---|---|
| 1-qubit circuit, O0-O3, any seed (2.5.2 and 2.4.2) | gate expanded to its `ry` definition | kept as native `rz` at every level |
| 2-qubit circuit `[lookalike rz; cz]` on a 27-qubit ECR backend, O2/O3, 40 seeds (2.4.2) | expanded | kept on 40/40 seeds |
| Operator of the user gate vs `RZGate(theta)` | different | (confirms the output is wrong) |

Full outputs: [`outputs/custom_rz_name_1q_2.5.2.txt`](outputs/custom_rz_name_1q_2.5.2.txt),
[`outputs/custom_rz_name_2.4.2.txt`](outputs/custom_rz_name_2.4.2.txt),
[`outputs/custom-rz-name-kept-as-native-local.txt`](outputs/custom-rz-name-kept-as-native-local.txt)

**Likely cause:** the `BasisTranslator` skips operations whose name is already in the target basis, so a custom
gate that shares the name is trusted as the standard gate. It only disappears if a later resynthesis happens to
absorb its block.

**Existing related issues:** [Qiskit/qiskit#13988](https://github.com/Qiskit/qiskit/issues/13988)
explains why standard gate names are reserved. This naming trap also appears with `cx` in
[bug 4](#4-custom-gate-named-cx-kept-as-native-cx).

**Note:** on qiskit 2.5.0-2.5.2 the 2-qubit case can hang in `CommutativeCancellation`; that is a separate,
already known issue (Qiskit/qiskit#16937, fixed for 2.6). The 1-qubit case is unaffected by it.

---

## 4. Custom gate named cx kept as native cx

**TL;DR:** a user-defined `Gate("cx", 2, [])` whose definition is `h(0)` survives O0 transpilation
as an instruction named `cx`. Interpreting that opcode as a device-native CX changes the operation.
Standard gate names are reserved; this reproduces the naming trap rather than proving supported input is broken.

**Who is affected:** users and libraries that give custom gates the same name as target basis gates,
as in [bug 2](#2-custom-gate-named-rz-kept-as-native-rz).

**Script:** [`custom-cx-name-kept-as-native/repro.py`](custom-cx-name-kept-as-native/repro.py)

**Expected vs actual** (2 qubits, O0, one custom operation):

| Gate name | Expected for its H definition | Actual output | Retained custom CX | Native-device equivalent? |
|---|---|---|---|---|
| `cx` | expand H: 2 RZ + 1 SX, or diagnose the reserved name | 1 instruction named `cx` | 1 | False |
| `custom_cx` (control) | expand H: 2 RZ + 1 SX | 2 RZ + 1 SX | 0 | True |

`Operator(output)` alone reports equivalence in both cases because it expands the Python definition.
The script replaces the surviving custom `cx` with `CXGate()` to model native-device interpretation.

Full output: [`outputs/custom-cx-name-kept-as-native.txt`](outputs/custom-cx-name-kept-as-native.txt)

**Likely cause:** the target-basis shortcut checks the instruction name and trusts `cx` as a standard opcode.

**Workaround:** use a unique name such as `custom_cx` and let the transpiler expand its definition.

**Existing related issues:** [Qiskit/qiskit#13988](https://github.com/Qiskit/qiskit/issues/13988)
explains the reserved-name contract; [#13991](https://github.com/Qiskit/qiskit/pull/13991) fixes a
related name/type mismatch in commutation checking, not this native-name survival case.

---

## 3. rzz angle bounds not enforced inside control flow

**TL;DR:** on a target where `rzz` only accepts angles in `[0, pi/2]` (as on fractional-gate Heron devices),
a top-level out-of-range `rzz` is folded into range, but inside an `if_else` body it is left as is. In 2.5.x a
valid body (`cx; rz; cx`) is also resynthesised into an out-of-range `rzz` at O2/O3. The output is not a
valid circuit for the target.

**Who is affected:** dynamic circuits compiled with stock Qiskit against an angle-bounded `Target`.

**Script:** [`rzz-angle-bounds-in-control-flow/repro.py`](rzz-angle-bounds-in-control-flow/repro.py)
(target: `FakeFez` plus `RZZGate(theta)` on every `cz` pair with `angle_bounds=[(0, pi/2)]`)

**Expected vs actual** (out-of-range `rzz` in the output, 4 seeds per cell):

| Input | O0 | O1 | O2 | O3 | Versions |
|---|---|---|---|---|---|
| top-level `rzz(-pi/2)` | 0/4 | 0/4 | 0/4 | 0/4 | 2.4.2, 2.5.2 (correct) |
| `if_else { rzz(-pi/2) }` | 4/4 | 4/4 | 4/4 | 4/4 | 2.4.2, 2.5.2 |
| `if_else { rzz(2.5) }` | 4/4 | 4/4 | 4/4 | 4/4 | 2.4.2, 2.5.2 |
| `if_else { cx; rz(0.4); cx }` (valid input) | 0/4 | 0/4 | **4/4** | **4/4** | 2.5.2 only (0/4 on 2.4.2) |
| `if_else { cz }` (control) | 0/4 | 0/4 | 0/4 | 0/4 | both |

With qiskit-ibm-runtime's `translation_method="ibm_dynamic_and_fractional"` the same case is valid at O2/O3.

Full outputs: [`outputs/rzz_bounds_control_flow_2.5.2.txt`](outputs/rzz_bounds_control_flow_2.5.2.txt),
[`outputs/rzz_bounds_control_flow_2.4.2.txt`](outputs/rzz_bounds_control_flow_2.4.2.txt),
[`outputs/rzz_bounds_control_flow_ibm_plugin_2.5.2.txt`](outputs/rzz_bounds_control_flow_ibm_plugin_2.5.2.txt),
[`outputs/rzz-angle-bounds-in-control-flow-local.txt`](outputs/rzz-angle-bounds-in-control-flow-local.txt),
[`outputs/rzz-angle-bounds-in-control-flow-ibm-plugin-local.txt`](outputs/rzz-angle-bounds-in-control-flow-ibm-plugin-local.txt)

**Likely cause:** the angle-wrapping step does not recurse into control-flow blocks; since 2.5 the optimization
stage also synthesises `rzz` inside blocks, so valid inputs now produce invalid outputs.

---

## 5. Clifford+T translation fails on control flow

**TL;DR:** the Clifford+T pipeline fails on circuits containing control flow, even when every gate
inside the body is Clifford. This is a regression since 2.4.0 introduced by PR #15625; the same
`if_else` circuit compiles on 2.3.1. A candidate fix exists.

**Who is affected:** users compiling dynamic circuits into a Clifford+T basis with the preset pipeline.

**Script:** [`clifford-t-control-flow/repro.py`](clifford-t-control-flow/repro.py)

**Expected vs actual** (2 qubits, 1 classical bit, O2, `h; measure; if_else { x }`):

| Version | Static control: compiled circuits | Expected dynamic: compiled circuits | Actual dynamic |
|---|---|---|---|
| 2.3.1 | 1/1 | 1/1 | 1/1; 1 retained `if_else` |
| 2.5.2 | 1/1 | 1/1 | 0/1; `TranspilerError` translating `if_else` |

Full outputs: [`outputs/clifford-t-control-flow.txt`](outputs/clifford-t-control-flow.txt),
[`outputs/clifford-t-control-flow-2.3.1.txt`](outputs/clifford-t-control-flow-2.3.1.txt)

**Likely cause:** the rewritten Clifford+T translation stage does not admit control-flow operations
into its intermediate basis, so the translator rejects the container before translating its body.

**Workaround:** use 2.3.1 for this pipeline, or compile with a continuous basis that supports control flow
when Clifford+T output is not required.

**Existing related issues:** [Qiskit/qiskit#15625](https://github.com/Qiskit/qiskit/pull/15625)
introduced the pipeline rewrite. No exact public fix/report was found in the checked searches;
the candidate fix is not linked here.

---

## 6. QPY writes arithmetic gates but cannot read them

**TL;DR:** QPY successfully writes `HalfAdderGate`, `ModularAdderGate`, `MultiplierGate`,
`IntegerComparatorGate`, and `LinearPauliRotationsGate`, but cannot load any of those saved circuits.

**Who is affected:** users persisting circuits with these high-level arithmetic-library gates.

**Script:** [`qpy-arithmetic-gates/repro.py`](qpy-arithmetic-gates/repro.py)

**Expected vs actual** (each gate constructed with 2 state qubits; comparator value 1):

| Gate | Bytes successfully written | Expected loaded circuits | Actual loaded circuits | Missing constructor arguments |
|---|---|---|---|---|
| HalfAdder | 241 | 1 | 0 (`TypeError`) | `num_state_qubits` |
| ModularAdder | 231 | 1 | 0 (`TypeError`) | `num_state_qubits` |
| Multiplier | 281 | 1 | 0 (`TypeError`) | `num_state_qubits` |
| IntegerComparator | 223 | 1 | 0 (`TypeError`) | `num_state_qubits`, `value` |
| LinearPauliRotations | 226 | 1 | 0 (`TypeError`) | `num_state_qubits` |

Full output: [`outputs/qpy-arithmetic-gates.txt`](outputs/qpy-arithmetic-gates.txt)

**Likely cause:** the reader recognizes the library gate class but reconstructs it without the
initialization arguments required by that class; the writer has already accepted the circuit.

**Workaround:** decompose these high-level gates before saving and verify a round trip before
relying on the saved file, or save their construction arguments separately and rebuild the gates.

**Existing related issues:** [Qiskit/qiskit#16943](https://github.com/Qiskit/qiskit/pull/16943)
proposes QPY initialization-parameter support; it is related work, not a verified fix for these five gates.

---

## 7. QPY cannot read wide MCX gates

**TL;DR:** QPY writes wide MCX gates but cannot read 63 or 127 controls on 2.5.2. On the checked
main snapshot, a 31-control reader cap also rejects 32 controls, which still loads on the release.
This does not mean every width above 31 fails on 2.5.2.

**Who is affected:** users saving wide controlled gates, including large Grover or arithmetic circuits.

**Script:** [`qpy-wide-mcx/repro.py`](qpy-wide-mcx/repro.py)
(serialization only; no decomposition or statevector allocation)

**Expected vs actual** (one MCX per circuit):

| Controls | Bytes written on 2.5.2 | Expected loaded circuits | Actual 2.5.2 | Actual checked main |
|---|---|---|---|---|
| 31 | 586 | 1 | 1; 31 controls | 1; 31 controls |
| 32 | 599 | 1 | 1; 32 controls | 0; `QpyError`, at most 31 supported |
| 63 | 1002 | 1 | 0; `OverflowError` | 0; `QpyError`, at most 31 supported |
| 127 | 1834 | 1 | 0; `OverflowError` | 0; `QpyError`, at most 31 supported |

Full outputs: [`outputs/qpy-wide-mcx.txt`](outputs/qpy-wide-mcx.txt),
[`outputs/qpy-wide-mcx-main-recheck.txt`](outputs/qpy-wide-mcx-main-recheck.txt)
(the main output is an archived recheck, not a local main build).

**Likely cause:** the release reader converts wide control-state integers into a bounded native integer;
the checked main instead rejects widths above its explicit 31-control limit. The introducing PR for
the 32-control rejection was not established.

**Workaround:** save the control count, control state, and circuit construction separately and rebuild
the MCX gate. Test QPY loading before treating a successfully written file as a usable backup.

**Existing related issues:** [Qiskit/qiskit#11377](https://github.com/Qiskit/qiskit/issues/11377)
concerns MCX QPY attributes; it does not establish a fix for this width limit.

---

## 8. GateDirection raises on a reversed custom ECR

**TL;DR:** `GateDirection` raises `TranspilerError` for a user-defined `Gate("ecr")` whose definition
is a standard ECR when the target only supports the reversed pair. A standard `ECRGate()` compiles.

**Who is affected:** users wrapping directional ECR operations in custom gates on asymmetric targets.
The reserved-name caveat from [bug 4](#4-custom-gate-named-cx-kept-as-native-cx) applies here too.

**Script:** [`reversed-custom-ecr/repro.py`](reversed-custom-ecr/repro.py)
(target: 2 qubits, ECR only on `(1, 0)`; input on `(0, 1)`, fixed layout, O2)

**Expected vs actual:**

| Input | Expected | Actual |
|---|---|---|
| Standard ECR (control) | 1 compiled circuit with supported direction | 1 compiled circuit: 1 ECR + 8 RZ + 4 SX |
| Custom ECR with the same definition | expand the definition and reverse, or diagnose the custom gate | 0 compiled circuits; `TranspilerError` says no reversal rules are known |

Full output: [`outputs/reversed-custom-ecr.txt`](outputs/reversed-custom-ecr.txt)

**Likely cause:** name-based basis handling retains the custom operation, but the direction pass's
standard reversal rules require a recognized gate type and do not expand this custom definition.

**Workaround:** use `ECRGate()` directly, or explicitly expand the custom gate before transpilation.

**Existing related issues:** [Qiskit/qiskit#12647](https://github.com/Qiskit/qiskit/issues/12647)
reports the general custom asymmetric gate direction failure.

---

## 9. IBM fake backends advertise couplers with error 1.0

**TL;DR:** packaged `FakeFez` and `FakeSherbrooke` targets advertise two-qubit instructions whose
calibrated error is exactly 1.0. There are 14 CZ entries in Fez and 9 ECR entries in Sherbrooke.
These are directed instruction entries, not counts of distinct physical couplers.

**Who is affected:** fake-backend simulation, layout, and calibration tests that trust the target's
advertised two-qubit instruction properties.

**Script:** [`fake-backend-error-one-couplers/repro.py`](fake-backend-error-one-couplers/repro.py)

**Expected vs actual** (qiskit-ibm-runtime 0.50.0 packaged snapshots):

| Backend | Two-qubit instruction entries | Expected error-1.0 entries in a usable target | Actual error-1.0 entries | Example |
|---|---|---|---|---|
| FakeFez | 352 | 0 | 14 | CZ `(27, 28)`, error 1.0 |
| FakeSherbrooke | 144 | 0 | 9 | ECR `(6, 5)`, error 1.0 |

Full output: [`outputs/fake-backend-error-one-couplers.txt`](outputs/fake-backend-error-one-couplers.txt)
(includes every error-1.0 pair).

**Likely cause:** fake targets expose the stored calibration snapshot without filtering these entries.
Faulty-operation checking and target construction are separate mechanisms; an error of 1.0 alone
does not prove the snapshot's operational flags mark that coupler faulty.

**Workaround:** inspect the target before using calibration-based scores, filter error-1.0 entries
when constructing a test target, and use the fake backend's faulty-operation checks where applicable.

**Existing related issues:** [Qiskit/qiskit-ibm-runtime#1765](https://github.com/Qiskit/qiskit-ibm-runtime/pull/1765)
adds `check_faulty` support; it does not establish target filtering of error-1.0 entries.

---

## 10. O3 repeatedly emits out-of-bounds rzz and retranslates

**TL;DR:** on an angle-bounded RZZ target, the O3 peephole optimizer repeatedly emits RZZ angles
outside `[0, pi/2]`. `GatesInBasis` then rejects each iteration and the pipeline wraps/translates again.
The compile terminates; this reproduction does not show an infinite loop or invalid final output.

**Who is affected:** users compiling at O3 for fractional-gate targets, where incompatible synthesis
and angle wrapping add repeated work.

**Script:** [`o3-rzz-retranslation/repro.py`](o3-rzz-retranslation/repro.py)
(8 qubits, all-to-all RZZ target, 28 controlled-phase gates, seed 11; an exact RZZ wrapper is registered)

**Expected vs actual:**

| Observation | Expected | Actual local run |
|---|---|---|
| Out-of-bounds RZZ after each peephole | 0 | 7, 6, 5, 4, 3, 2, 1, 1 |
| `GatesInBasis` accepts each peephole result | True | False on 8/8 checks |
| Extra wrapping after optimization due to invalid angles | 0 | 8 calls (9 total including initial translation) |
| Final output | terminates with 0 invalid angles | terminates; 0 invalid angles, depth 32, size 111 |

Full output: [`outputs/o3-rzz-retranslation.txt`](outputs/o3-rzz-retranslation.txt)

**Likely cause:** two-qubit peephole synthesis does not respect the target's angle bounds; its output
triggers translation and wrapping in the optimization loop. The loop's stopping rule eventually ends it.
Intermediate counts can vary by environment and synthesis ordering.

**Workaround:** use a lower optimization level when the repeated O3 work is unnecessary, and check
final RZZ angles against the target bounds. The control-flow bounds failure is separate:
[bug 3](#3-rzz-angle-bounds-not-enforced-inside-control-flow).

**Existing related issues:** [Qiskit/qiskit#14288](https://github.com/Qiskit/qiskit/issues/14288)
reports fractional-target RZZ angle problems; it does not establish a fix for repeated retranslation.

---

## 11. Seeded synthesis is not run-to-run deterministic

**TL;DR:** repeated synthesis of the same circuit with the same `seed_transpiler=0` produces different
RZ counts. The supplied recheck ranged from 378 to 397; this local run ranged from 381 to 401.

**Who is affected:** users relying on seeded compilation for reproducible gate counts or benchmarks.

**Script:** [`seeded-synthesis-nondeterminism/repro.py`](seeded-synthesis-nondeterminism/repro.py)
(embedded original `adder_8`: 24 qubits, 330 input gates; O3, Clifford+RZ basis)

**Expected vs actual** (12 calls in one process, identical circuit and seed):

| Environment | Expected distinct RZ counts | Actual distinct counts | Actual RZ range |
|---|---|---|---|
| Local macOS, Qiskit 2.5.2 | 1 | 8 | 381-401 |
| Archived Linux recheck, Qiskit 2.5.2 | 1 | 11 | 378-397 |
| Archived Linux recheck, checked main | 1 | 10 | 378-397 |

Full outputs: [`outputs/seeded-synthesis-nondeterminism.txt`](outputs/seeded-synthesis-nondeterminism.txt),
[`outputs/seeded-synthesis-nondeterminism-release-recheck.txt`](outputs/seeded-synthesis-nondeterminism-release-recheck.txt),
[`outputs/seeded-synthesis-nondeterminism-main-recheck.txt`](outputs/seeded-synthesis-nondeterminism-main-recheck.txt)
(the latter two preserve the earlier recheck; they were not rerun locally).

**Likely cause:** the seed does not control every ordering or synthesis decision. The exact source of
this witness's drift has not been traced; the observation alone does not establish a specific RNG defect.

**Workaround:** save and reuse the compiled circuit for comparisons, and record its gate counts together
with the seed and versions. A seed alone does not guarantee identical output for this pipeline.

**Existing related issues:** [Qiskit/qiskit#13667](https://github.com/Qiskit/qiskit/pull/13667)
improves ordering determinism in `UnitarySynthesis`, but explicitly does not guarantee determinism.
It is not a verified fix for this witness.

---

## 12-16. Commutation and decomposition findings

Items 12-16 were run on release Qiskit 2.6.0 and a fresh source build at
`ef11224130eecc78d46e3b84f11e2155a5cb6556` (2026-10-19). Each item folder has
its own README, standalone script and release/main outputs. Stored runs used
Python 3.13.14 on macOS arm64; the main build reports Qiskit 2.7.0.dev0.
We did not record run times or thread counts for these items. The commands above
limit numerical threads and Qiskit processes for reruns.
SHA-256 of the compiled Qiskit extension used:
`6ad1fcd9daff14bc821e94dc4d3542c17ba5b6e0cf9fc2ed9c465d4f36b04780`.

Item 12 removes a non-identity rotation using a fixed cutoff that ignores the pass's
`approximation_degree` setting; item 15 raises through a broken wrapper.
In item 13 a shortcut runs before the check that excludes measurements, resets
and barriers.
Item 14 is a reserved-name design issue, like the published custom-name items.
Item 16 is a diagnosed estimator inconsistency; synthesis is equivalent, and
the proposed coordinate-source repair remains unpatched. Its private-API
`diagnose.py` provides Weyl, invariant, 0/1/2/3-CX and global-phase controls;
`repro.py` uses public APIs only.

The [CommutationChecker findings note](commutation-checker-findings.md) distinguishes
historical single-machine tolerance, symbolic and timing measurements from
these fresh reproductions. Proposed fixes are unpatched directions, not tested
Qiskit source changes.

## 17-18. Initial layout and exact-fidelity synthesis

Items 17 and 18 were checked on Qiskit 2.6.0 and a recorded main runtime at
`f70269034d2ec07699d6c69e33594273c73f8df2` with CPython 3.13.14 on macOS arm64.
Their folder READMEs give standalone commands, selected release/main outputs and
source and runtime hashes. The main evidence uses the built native extension with
the Python sources copied from main f702690, as stated in each runtime details file.
Other items keep their original test scope.

Item 17 records three distinct initial layouts for one fixed circuit and Target
under seed 1 and a fixed single-thread environment. Item 18 records tiny-angle
approximation despite `basis_fidelity=1.0` and `approximate=False`, with a direct
Weyl specialization control. They are reproducibility and API behavior issues;
no source fixes or new timing claims are included. Upstream duplicate searches
for these two additions have not been performed.

## Reproducing the current main build

```bash
git clone https://github.com/Qiskit/qiskit.git /tmp/qiskit-main
git -C /tmp/qiskit-main checkout ef11224130eecc78d46e3b84f11e2155a5cb6556
python3 -m venv /tmp/qiskit-main/.venv
/tmp/qiskit-main/.venv/bin/pip install /tmp/qiskit-main
/tmp/qiskit-main/.venv/bin/python commutative-cancellation-angle-cutoff/repro.py
```

Building Qiskit requires Rust. Native-extension hashes vary with platform and
toolchain; the hash above binds the stored macOS build. Published items 1-11
retain their earlier main pin and version evidence.

## Related items already fixed upstream

| Item | Where it was fixed |
|---|---|
| MQT QCEC reported some inequivalent wide circuits as equivalent (QCEC 3.10.x) | Fixed in mqt.qcec 3.11.0 / mqt.core 3.11.0 (munich-quantum-toolkit/qcec#1100, munich-quantum-toolkit/core#2710) |
| `CommutativeCancellation` hangs on a parametrised user gate named `rz`/`rx`/`p`/`u1` next to `cz` (qiskit 2.5.0-2.5.2) | Qiskit/qiskit#16937, fixed by #16963 for 2.6.0 |

## Repository layout

```
aer-noise-applied-twice/repro.py
custom-rz-name-kept-as-native/repro.py
rzz-angle-bounds-in-control-flow/repro.py
custom-cx-name-kept-as-native/repro.py
clifford-t-control-flow/repro.py
qpy-arithmetic-gates/repro.py
qpy-wide-mcx/repro.py
reversed-custom-ecr/repro.py
fake-backend-error-one-couplers/repro.py
o3-rzz-retranslation/repro.py
seeded-synthesis-nondeterminism/repro.py
CHANGES.md          review notes and validation deviations
commutative-cancellation-angle-cutoff/             README, repro.py, outputs/
commutation-near-identity-before-precheck/          README, repro.py, outputs/
commutation-library-name-collision/                README, repro.py, outputs/
check-commutation-entries-attribute-error/          README, repro.py, outputs/
num-basis-gates-estimator-mismatch/                README, repro.py, diagnose.py, outputs/
commutation-checker-findings.md
outputs/            observed outputs and versions.txt
```
