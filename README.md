# Qiskit bug reproductions

Minimal, standalone reproductions of thirty-two observed problems in Qiskit, Qiskit Aer, and
qiskit-ibm-runtime: wrong or hardware-invalid results, compilation and serialization failures,
misleading fake-backend calibration entries, repeated synthesis work, seeded metric drift, and
slow scheduling padding.
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

The first eighteen rows retain their published priority order. Items 19-31 are new correctness
and crash cases; item 32 is a performance case. The `#` column keeps each item's number.

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
| 19 | 19 | [Rescheduling can overlap two gates](#19-rescheduling-can-overlap-two-gates) | qiskit | Two SX gates overlap by 4 dt | Reproduced in 2.6.0 |
| 20 | 20 | [Mixed alignments leave a measurement off-grid](#20-mixed-alignments-leave-a-measurement-off-grid) | qiskit | Measurement starts 11 dt off the acquire grid | Reproduced in 2.6.0 |
| 21 | 21 | [Rescheduling swaps alignment arguments](#21-rescheduling-swaps-alignment-arguments) | qiskit | X gate starts 4 dt off the pulse grid | Reproduced in 2.6.0; #16186 open |
| 22 | 22 | [QPY version 17 drops delay units](#22-qpy-version-17-drops-delay-units) | qiskit / qiskit-ibm-runtime | 100 us becomes 100 dt | Reproduced in 2.6.0 / 0.50.0; #8293 open |
| 23 | 23 | [QPY cannot reload parameterized delays](#23-qpy-cannot-reload-parameterized-delays) | qiskit | Loaded operation raises CircuitError | Reproduced in 2.6.0 |
| 24 | 24 | [BasisTranslator leaves a placeholder operation](#24-basistranslator-leaves-a-placeholder-operation) | qiskit | Reverse ECR fails at O0-O3 | Reproduced in 2.6.0 |
| 25 | 25 | [Angle wrapping leaves a zero-qubit gate](#25-angle-wrapping-leaves-a-zero-qubit-gate) | qiskit / qiskit-ibm-runtime | Output has unsupported global_phase operation | Reproduced in 2.6.0 / 0.50.0; runtime fix merged, unreleased |
| 26 | 26 | [Single-gate DD loses global phase](#26-single-gate-dd-loses-global-phase) | qiskit | Phase differs by -1.3 rad | Reproduced in 2.6.0 |
| 27 | 27 | [Mixed one-qubit bases yield unsupported gates](#27-mixed-one-qubit-bases-yield-unsupported-gates) | qiskit | O0 output has U on an RZ/SX/X-only qubit | Reproduced in 2.6.0; #11339 open |
| 28 | 28 | [Trailing delay remains off-grid](#28-trailing-delay-remains-off-grid) | qiskit | 100 dt delay fails 16 dt DD alignment | Reproduced in 2.6.0 |
| 29 | 29 | [QASM 3 exporter corrupts pi expressions](#29-qasm-3-exporter-corrupts-pi-expressions) | qiskit | Emits unparsable `2pi + pi*th` | Reproduced in 2.6.0 |
| 30 | 30 | [Measure and reset can start off-grid](#30-measure-and-reset-can-start-off-grid) | qiskit | FakePrague starts operations at 33 and 442 dt | Reproduced in 2.6.0 |
| 31 | 31 | [QASM 3 round trip changes angle and phase](#31-qasm-3-round-trip-changes-angle-and-phase) | qiskit | Angle changes by 9e-10 rad; phase 0.75 becomes 0 | Reproduced in 2.6.0 |
| 32 | 32 | [Python padding loops dominate scheduling](#32-python-padding-loops-dominate-scheduling) | qiskit | PadDelay 5.46 s vs O2 transpile 1.75 s locally | Measured in 2.6.0 |

Items 1-11 retain their published test scope; they were not revalidated in the 2026-10-19 addition.
[`CHANGES.md`](CHANGES.md) records this addition and its exclusions; the 12-16 section records
that earlier addition's separate runtime and private-API diagnostic scope.

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
- [19. Rescheduling can overlap two gates](#19-rescheduling-can-overlap-two-gates)
- [20. Mixed alignments leave a measurement off-grid](#20-mixed-alignments-leave-a-measurement-off-grid)
- [21. Rescheduling swaps alignment arguments](#21-rescheduling-swaps-alignment-arguments)
- [22. QPY version 17 drops delay units](#22-qpy-version-17-drops-delay-units)
- [23. QPY cannot reload parameterized delays](#23-qpy-cannot-reload-parameterized-delays)
- [24. BasisTranslator leaves a placeholder operation](#24-basistranslator-leaves-a-placeholder-operation)
- [25. Angle wrapping leaves a zero-qubit gate](#25-angle-wrapping-leaves-a-zero-qubit-gate)
- [26. Single-gate DD loses global phase](#26-single-gate-dd-loses-global-phase)
- [27. Mixed one-qubit bases yield unsupported gates](#27-mixed-one-qubit-bases-yield-unsupported-gates)
- [28. Trailing delay remains off-grid](#28-trailing-delay-remains-off-grid)
- [29. QASM 3 exporter corrupts pi expressions](#29-qasm-3-exporter-corrupts-pi-expressions)
- [30. Measure and reset can start off-grid](#30-measure-and-reset-can-start-off-grid)
- [31. QASM 3 round trip changes angle and phase](#31-qasm-3-round-trip-changes-angle-and-phase)
- [32. Python padding loops dominate scheduling](#32-python-padding-loops-dominate-scheduling)
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

Items 19-32 were rerun on macOS arm64 with Python 3.13.14, latest PyPI Qiskit 2.6.0,
qiskit-ibm-runtime 0.50.0 where needed, and openqasm3 1.0.1 for item 29.
See [`outputs/versions.txt`](outputs/versions.txt). Every added run had a 300-second timeout;
the recorded performance run completed in under 20 seconds on this Mac.

## How to run

```bash
python3 -m venv ./venv && . venv/bin/activate
mkdir -p .cache/pip .cache/uv .cache/tmp
export PIP_CACHE_DIR="$PWD/.cache/pip" UV_CACHE_DIR="$PWD/.cache/uv" TMPDIR="$PWD/.cache/tmp"
export QISKIT_NUM_PROCS=1 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
pip install "qiskit==2.5.2" "qiskit-aer==0.17.2" "qiskit-ibm-runtime==0.50.0"

python aer-noise-applied-twice/repro.py
python custom-rz-name-kept-as-native/repro.py            # add --gadget for the 2-qubit case
python rzz-angle-bounds-in-control-flow/repro.py         # minimal, Qiskit only
python rzz-angle-bounds-in-control-flow/repro_full.py    # add --ibm-plugin for the comparison
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
Most expected failures are caught and printed without a traceback; a successful process exit does not mean
the defect is fixed. The simplified Clifford+T script leaves its exception uncaught and exits nonzero
on affected versions. No account or hardware access is needed.

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

For items 19-32, install the current PyPI releases in a separate environment and run each
`repro.py` from its folder path. For example:

```bash
uv venv .venv-current
uv pip install --python .venv-current/bin/python qiskit qiskit-ibm-runtime openqasm3
.venv-current/bin/python constrained-reschedule-overlap/repro.py
.venv-current/bin/python padding-python-loops/repro.py
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

**Minimal script:** [`rzz-angle-bounds-in-control-flow/repro.py`](rzz-angle-bounds-in-control-flow/repro.py)
uses only Qiskit, a two-qubit `Target`, and one `transpile(..., optimization_level=0)` call.
It explicitly registers an exact wrapping rule for the test angle, then places `rzz(-0.4)`
both at the top level and inside `if_else`. On Qiskit 2.6.0 it prints:

```text
qiskit 2.6.0
Expected: all RZZ angles in [0, pi/2]
Top level: [0.4]
Inside if_else: [-0.4]
```

**Full script:** [`rzz-angle-bounds-in-control-flow/repro_full.py`](rzz-angle-bounds-in-control-flow/repro_full.py)
retains the original seed, optimization-level, and IBM plugin comparisons below
(target: `FakeFez` plus `RZZGate(theta)` on every `cz` pair with `angle_bounds=[(0, pi/2)]`).

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

**Detailed report:** [`clifford-t-control-flow/README.md`](clifford-t-control-flow/README.md)
documents the simplified one-qubit script with line-by-line comments, comparisons on 2.3.1, 2.4.0, and 2.6.0,
and the intermediate-basis diagnosis.

**Earlier two-qubit comparison** (1 classical bit, O2, `h; measure; if_else { x }`):

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

In separate Qiskit 2.6.0 measurements, Sabre layout and routing did not read gate errors. When a
Torino circuit used error-1.0 couplers, removing those entries from the test target changed its
estimated log-success from -1665 to -48. On circuits that had avoided them already, removing the
entries increased two-qubit gate counts by up to 25%. This supports avoiding these couplers during
routing without removing usable connections indiscriminately. [Qiskit/qiskit#5155](https://github.com/Qiskit/qiskit/issues/5155)
is the related open routing issue (checked 2026-10-21).

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

## 19. Rescheduling can overlap two gates

**TL;DR:** `ConstrainedReschedule` can move one SX gate into the preceding SX gate after aligning a delay.

**Who is affected:** users scheduling circuits with off-grid delays for targets with timing constraints.

**Script:** [`constrained-reschedule-overlap/repro.py`](constrained-reschedule-overlap/repro.py)

**Expected vs actual:** the first SX runs at `[272, 308)` dt. The next should start at or after 308 dt;
it starts at 304 dt, overlapping by 4 dt.

Full output: [`outputs/constrained-reschedule-overlap.txt`](outputs/constrained-reschedule-overlap.txt).

**Likely cause:** the rescheduler adds a Target duration in seconds, cast to an integer, to a start
time in dt; a subsecond gate contributes zero dt when it decides whether to move a successor.

**Workaround:** check scheduled start times for overlap before submitting; Qiskit 2.3.1 did not
show this witness.

**Related upstream issues/PRs (checked 2026-10-21):** no related issue found for this seconds-to-dt
conversion. [#16186](https://github.com/Qiskit/qiskit/issues/16186) tracks a separate alignment
argument swap; [#16210](https://github.com/Qiskit/qiskit/pull/16210) closed unmerged and
[#16482](https://github.com/Qiskit/qiskit/pull/16482) remains open without fixing this conversion.

---

## 20. Mixed alignments leave a measurement off-grid

**TL;DR:** the duration check does not request rescheduling when one alignment value is 1.

**Who is affected:** users scheduling on targets with different pulse and acquire alignments.

**Script:** [`instruction-duration-check-mixed-alignment/repro.py`](instruction-duration-check-mixed-alignment/repro.py)

**Expected vs actual:** with pulse alignment 1 dt and acquire alignment 16 dt, a 100 dt delay
should request rescheduling. The check returns `False`; measurement starts at 107 dt, 11 dt
off the acquire grid.

Full output: [`outputs/instruction-duration-check-mixed-alignment.txt`](outputs/instruction-duration-check-mixed-alignment.txt).

**Likely cause:** the check accepts a duration divisible by either alignment when it needs both.

**Workaround:** verify measurement start times against acquire alignment and align delays explicitly.

**Related upstream issues/PRs (checked 2026-10-21):** no related issue found for this condition.
The Rust duration-check port [#14700](https://github.com/Qiskit/qiskit/pull/14700) is context only.

---

## 21. Rescheduling swaps alignment arguments

**TL;DR:** `ConstrainedReschedule` applies the acquire alignment to a pulse operation.

**Who is affected:** users of targets where pulse and acquire alignments differ.

**Script:** [`constrained-reschedule-swapped-alignment/repro.py`](constrained-reschedule-swapped-alignment/repro.py)

**Expected vs actual:** with pulse alignment 16 dt and acquire alignment 1 dt, the second X
should start on a multiple of 16; it starts at 260 dt, remainder 4.

Full output: [`outputs/constrained-reschedule-swapped-alignment.txt`](outputs/constrained-reschedule-swapped-alignment.txt).

**Likely cause:** the caller passes `(acquire, pulse)` to parameters ordered `(pulse, acquire)`.

**Workaround:** verify pulse start times against the target grid; no general local correction was tested.

**Related upstream issues/PRs (checked 2026-10-21):** known in open
[#16186](https://github.com/Qiskit/qiskit/issues/16186); the targeted fix
[#16482](https://github.com/Qiskit/qiskit/pull/16482) is open and unmerged.

---

## 22. QPY version 17 drops delay units

**TL;DR:** a QPY v17 round trip, including the Runtime codec, changes `delay(100, "us")` to
`delay(100, "dt")`.

**Who is affected:** users passing circuits with non-dt delays through QPY v17 or the Runtime codec.

**Script:** [`qpy-delay-unit-dropped/repro.py`](qpy-delay-unit-dropped/repro.py)

**Expected vs actual:** the loaded delay should remain 100 us; both direct QPY v17 and Runtime
encode/decode return 100 dt.

Full output: [`outputs/qpy-delay-unit-dropped.txt`](outputs/qpy-delay-unit-dropped.txt).

**Likely cause:** QPY v17 does not serialize the delay unit. Runtime 0.50.0 uses that QPY version.

**Workaround:** transpile against the target first, or convert delays to dt explicitly before encoding.

**Related upstream issues/PRs (checked 2026-10-21):** known in open
[#8293](https://github.com/Qiskit/qiskit/issues/8293) and
[#10662](https://github.com/Qiskit/qiskit/issues/10662). Open
[#16806](https://github.com/Qiskit/qiskit/pull/16806) writes units only in QPY versions above 17.

---

## 23. QPY cannot reload parameterized delays

**TL;DR:** a dumped circuit with a parameterized delay loads, but accessing its delay operation raises.

**Who is affected:** users saving parameterized timing circuits with QPY.

**Script:** [`qpy-parameterized-delay-unloadable/repro.py`](qpy-parameterized-delay-unloadable/repro.py)

**Expected vs actual:** `delay(t)` should remain readable after load; both current QPY v18 and
v17 raise `CircuitError: Unknown unit expr is specified.`

Full output: [`outputs/qpy-parameterized-delay-unloadable.txt`](outputs/qpy-parameterized-delay-unloadable.txt).

**Likely cause:** the loader interprets a parameterized delay as a classical expression-unit delay.

**Workaround:** bind delay parameters before QPY serialization when the values are known.

**Related upstream issues/PRs (checked 2026-10-21):** no related issue found.

---

## 24. BasisTranslator leaves a placeholder operation

**TL;DR:** translation of a reverse-direction ECR on a target with mixed two-qubit gates fails.

**Who is affected:** users compiling against targets where an operation is available on only some edges.

**Script:** [`basis-translator-placeholder/repro.py`](basis-translator-placeholder/repro.py)

**Expected vs actual:** the ECR on `(2, 1)` should be translated or direction-corrected using the
target's ECR on `(1, 2)`; O0, O1, O2 and O3 all raise `TranspilerError` saying the direction could
be swapped but no rule is known.

Full output: [`outputs/basis-translator-placeholder.txt`](outputs/basis-translator-placeholder.txt).

**Likely cause:** the qubit-local translation path keeps an internal placeholder when the gate
name appears in the target but its requested direction is unsupported.

**Workaround:** decompose the reverse-direction gate before this translation path, or use a
supported physical direction when circuit placement allows it.

**Related upstream issues/PRs (checked 2026-10-21):** no related issue found for this placeholder leak.

---

## 25. Angle wrapping leaves a zero-qubit gate

**TL;DR:** wrapping an out-of-bounds RZZ leaves a zero-qubit `global_phase` operation outside the target.

**Who is affected:** users compiling bounded-angle RZZ circuits with Runtime 0.50.0's wrapper.

**Script:** [`wrap-angles-global-phase-gate/repro.py`](wrap-angles-global-phase-gate/repro.py)

**Expected vs actual:** global phase should be stored as circuit phase. O0 instead produces
`['global_phase', 'rz', 'x', 'rz', 'rzz', 'x']`; scheduling raises because the zero-qubit operation has
no target duration.

Full output: [`outputs/wrap-angles-global-phase-gate.txt`](outputs/wrap-angles-global-phase-gate.txt).

**Likely cause:** the wrapper emits `GlobalPhaseGate` as a DAG operation after target translation.

**Workaround:** avoid out-of-bounds RZZ angles or validate output against the target before scheduling.

**Related upstream issues/PRs (checked 2026-10-21):** known; Runtime
[#3489](https://github.com/Qiskit/qiskit-ibm-runtime/pull/3489) merged on 2026-10-15 and
replaces the operation with DAG global phase, but is not in the latest release 0.50.0.

---

## 26. Single-gate DD loses global phase

**TL;DR:** a one-gate dynamical decoupling sequence changes the circuit's global phase.

**Who is affected:** users adding single-gate DD to circuits used as controlled blocks or in
phase-sensitive comparisons.

**Script:** [`dd-single-gate-global-phase/repro.py`](dd-single-gate-global-phase/repro.py)

**Expected vs actual:** the padded circuit should have the same operator. It agrees only up to
global phase; the measured phase error is -1.3 rad.

Full output: [`outputs/dd-single-gate-global-phase.txt`](outputs/dd-single-gate-global-phase.txt).

**Likely cause:** the neighboring U gate absorbs the inverse DD gate through angle composition,
but the phase from that composition is discarded.

**Workaround:** use a two-gate DD sequence such as XX when it fits the idle window, or avoid
single-gate DD for phase-sensitive circuit blocks.

**Related upstream issues/PRs (checked 2026-10-21):** no related issue found.

---

## 27. Mixed one-qubit bases yield unsupported gates

**TL;DR:** a two-qubit gate translation can place one-qubit gates on a qubit whose local basis lacks them.

**Who is affected:** users of heterogeneous per-qubit target bases, particularly at O0.

**Script:** [`basis-translator-mixed-1q-basis/repro.py`](basis-translator-mixed-1q-basis/repro.py)

**Expected vs actual:** qubit 0 permits only RZ, SX and X. Translating CX emits one unsupported U
there; translating RZZ emits two U gates there and one unsupported RZ on qubit 1.

Full output: [`outputs/basis-translator-mixed-1q-basis.txt`](outputs/basis-translator-mixed-1q-basis.txt).

**Likely cause:** the one-qubit gates inside a two-qubit translation are chosen without the local
one-qubit basis for each output qubit.

**Workaround:** run `BasisTranslator` again on the translated result; higher optimization levels
also resynthesize these gates in this witness.

**Related upstream issues/PRs (checked 2026-10-21):** directly reported in open
[#11339](https://github.com/Qiskit/qiskit/issues/11339). Open
[#10013](https://github.com/Qiskit/qiskit/issues/10013) concerns a separate synthesis pass.

---

## 28. Trailing delay remains off-grid

**TL;DR:** a delay with no later operation on its wire is not aligned to the target's timing grid.

**Who is affected:** users scheduling circuits with trailing delays, especially before DD padding.

**Script:** [`trailing-delay-misaligned/repro.py`](trailing-delay-misaligned/repro.py)

**Expected vs actual:** a 100 dt delay should end on the 16 dt grid; the scheduled duration remains
100 dt, remainder 4, and DD raises `Time interval 100 is not divisible by alignment 16`.

Full output: [`outputs/trailing-delay-misaligned.txt`](outputs/trailing-delay-misaligned.txt).

**Likely cause:** constrained rescheduling aligns delays when pushing a successor, but this delay
has no successor on its wire.

**Workaround:** make trailing delays multiples of the target alignment before scheduling.

**Related upstream issues/PRs (checked 2026-10-21):** no direct issue found. Open
[#10294](https://github.com/Qiskit/qiskit/issues/10294) concerns the DD error message only.

---

## 29. QASM 3 exporter corrupts pi expressions

**TL;DR:** the default QASM 3 exporter substitutes `pi` inside a parameter expression's numeric text.

**Who is affected:** users exporting parameterized circuits whose expression contains pi-like floats.

**Script:** [`qasm3-expr-pi-substitution/repro.py`](qasm3-expr-pi-substitution/repro.py)

**Expected vs actual:** a valid expression such as `23.141592653589793 + 3.141592653589793*th`
should remain parseable. The exporter emits `2pi + pi*th`; the openqasm3 1.0.1 reference parser
raises `QASM3ParsingError`.

Full output: [`outputs/qasm3-expr-pi-substitution.txt`](outputs/qasm3-expr-pi-substitution.txt).

**Likely cause:** textual replacement of pi-like substrings changes the surrounding numeric literal.

**Workaround:** call `qasm3.dumps(circuit, disable_constants=True)` for this case.

**Related upstream issues/PRs (checked 2026-10-21):** no related issue found.

---

## 30. Measure and reset can start off-grid

**TL;DR:** scheduling can leave measurement and reset starts off the acquire grid even with no delays.

**Who is affected:** users scheduling on targets whose gate durations do not respect acquire alignment.

**Script:** [`measure-reset-misalignment/repro.py`](measure-reset-misalignment/repro.py)

**Expected vs actual:** FakePrague's acquire grid is 16 dt and SX lasts 7 dt. In the ALAP output,
reset starts at 33 dt and three measurements at 442 dt, none a multiple of 16. ASAP also has four
off-grid operations, starting at 26, 33, 435 and 442 dt.

Full output: [`outputs/measure-reset-misalignment.txt`](outputs/measure-reset-misalignment.txt).

**Likely cause:** duration checking focuses on delays and assumes gate durations already meet the grid.

**Workaround:** inspect scheduled measure/reset starts against target constraints; no general
local correction was tested.

**Related upstream issues/PRs (checked 2026-10-21):** no related issue found.

---

## 31. QASM 3 round trip changes angle and phase

**TL;DR:** default QASM 3 export changes a near-pi angle and omits circuit global phase.

**Who is affected:** users round-tripping phase-sensitive circuits or near-pi rotations through QASM 3.

**Script:** [`qasm3-angle-and-phase-change/repro.py`](qasm3-angle-and-phase-change/repro.py)

**Expected vs actual:** the input RZZ angle `1.5707963258948965` reloads as
`1.5707963267948966`, a change of `9.000000744663339e-10` rad. Circuit global phase `0.75`
reloads as `0.0`; the operators compare unequal.

Full output: [`outputs/qasm3-angle-and-phase-change.txt`](outputs/qasm3-angle-and-phase-change.txt).

**Likely cause:** default constant formatting snaps near-pi numeric values to exact pi fractions;
the exporter does not emit the circuit's global phase.

**Workaround:** `disable_constants=True` avoids the numeric snap; preserve global phase separately
if exact operator equality is required.

**Related upstream issues/PRs (checked 2026-10-21):**
the global-phase omission is known in open [#12114](https://github.com/Qiskit/qiskit/issues/12114).
Its proposed fix [#12118](https://github.com/Qiskit/qiskit/pull/12118) is open and on hold.
No related issue found for the numeric snap in this witness.

---

## 32. Python padding loops dominate scheduling

**TL;DR:** Python-side PadDelay and PadDynamicalDecoupling cost more than O2 transpilation on a
320-qubit QFT routed to a 409-qubit target.

**Who is affected:** users padding large, wide routed circuits before execution.

**Script:** [`padding-python-loops/repro.py`](padding-python-loops/repro.py)

**Expected vs actual:** the Mac rerun spent 1.753 s in O2 transpilation, 5.463 s in PadDelay and
6.067 s in PadDynamicalDecoupling (individual pass times; stage totals 6.011 and 6.633 s).
A separate 409-qubit measurement recorded 3.36 s O2 transpilation, 11.34 s PadDelay and 12.01 s
DD padding on this QFT. Its equivalent-output prototype reduced those padding times to 1.24 and
1.72 s, respectively.

Full output: [`outputs/padding-python-loops.txt`](outputs/padding-python-loops.txt).

**Likely cause:** the padding loop rebuilds the full wire-output map for each gap and repeats
qubit-index and duration lookups. Keeping the last node per wire, mapping qubits to indices once,
and caching durations by operation and qubits would remove those repeated costs.

**Workaround:** avoid optional padding on large circuits when it is not required; when it is
required, account for its time separately from transpilation.

**Related upstream issues/PRs (checked 2026-10-21):** open
[#13023](https://github.com/Qiskit/qiskit/issues/13023) describes repeated output-map rebuilding;
[#12266](https://github.com/Qiskit/qiskit/issues/12266) and
[#14620](https://github.com/Qiskit/qiskit/issues/14620) request Rust padding ports.

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
rzz-angle-bounds-in-control-flow/repro_full.py
custom-cx-name-kept-as-native/repro.py
clifford-t-control-flow/repro.py
qpy-arithmetic-gates/repro.py
qpy-wide-mcx/repro.py
reversed-custom-ecr/repro.py
fake-backend-error-one-couplers/repro.py
o3-rzz-retranslation/repro.py
seeded-synthesis-nondeterminism/repro.py
CHANGES.md          review notes and validation deviations
constrained-reschedule-overlap/repro.py
instruction-duration-check-mixed-alignment/repro.py
constrained-reschedule-swapped-alignment/repro.py
qpy-delay-unit-dropped/repro.py
qpy-parameterized-delay-unloadable/repro.py
basis-translator-placeholder/repro.py
wrap-angles-global-phase-gate/repro.py
dd-single-gate-global-phase/repro.py
basis-translator-mixed-1q-basis/repro.py
trailing-delay-misaligned/repro.py
qasm3-expr-pi-substitution/repro.py
measure-reset-misalignment/repro.py
qasm3-angle-and-phase-change/repro.py
padding-python-loops/repro.py
commutative-cancellation-angle-cutoff/             README, repro.py, outputs/
commutation-near-identity-before-precheck/          README, repro.py, outputs/
commutation-library-name-collision/                README, repro.py, outputs/
check-commutation-entries-attribute-error/          README, repro.py, outputs/
num-basis-gates-estimator-mismatch/                README, repro.py, diagnose.py, outputs/
commutation-checker-findings.md
outputs/            observed outputs and versions.txt
```
