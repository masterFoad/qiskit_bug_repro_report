# Qiskit bug reproductions

Minimal, standalone reproductions of three bugs in Qiskit and Qiskit Aer that produce silently wrong or
hardware-invalid results. Each bug has a short script, the output we observed, and the versions tested.
None of them had a public issue when this was written (searched on 2026-10-14).

## TL;DR

| # | Bug | Library | Effect | Status on latest release |
|---|---|---|---|---|
| 1 | [Noise applied twice in a density-matrix circuit that follows a statevector circuit](#1-aer-noise-applied-twice) | qiskit-aer | Silent wrong result: trace(rho) = 2 | Broken in 0.17.2 and on main |
| 2 | [A custom gate named `rz` is kept as the native `rz`](#2-custom-gate-named-rz-kept-as-native-rz) | qiskit | Silent wrong result on hardware | Broken in 2.5.2 (also 2.4.2) |
| 3 | [`rzz` angles inside control-flow bodies are not brought into the target's bounds](#3-rzz-angle-bounds-not-enforced-inside-control-flow) | qiskit | Output is invalid for fractional-gate targets | Broken in 2.5.2 |

## Contents

- [Environment](#environment)
- [How to run](#how-to-run)
- [1. Aer: noise applied twice](#1-aer-noise-applied-twice)
- [2. Custom gate named rz kept as native rz](#2-custom-gate-named-rz-kept-as-native-rz)
- [3. rzz angle bounds not enforced inside control flow](#3-rzz-angle-bounds-not-enforced-inside-control-flow)
- [Related items already fixed upstream](#related-items-already-fixed-upstream)
- [Repository layout](#repository-layout)

## Environment

All outputs in `outputs/` were produced on Linux x86_64 with:

| Package | Version |
|---|---|
| Python | 3.13.16 |
| qiskit | 2.5.2 (bug 2 and 3 also run on 2.4.2 for comparison) |
| qiskit-aer | 0.17.2 |
| qiskit-ibm-runtime | 0.50.0 (only for the `FakeFez` target in bug 3) |

## How to run

```bash
python -m venv venv && . venv/bin/activate
pip install "qiskit==2.5.2" "qiskit-aer==0.17.2" "qiskit-ibm-runtime==0.50.0"

python aer-noise-applied-twice/repro.py
python custom-rz-name-kept-as-native/repro.py            # add --gadget for the 2-qubit case
python rzz-angle-bounds-in-control-flow/repro.py         # add --ibm-plugin for the comparison
```

Each script prints the Qiskit (and Aer) version first, then the results.

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

Full output: [`outputs/aer_noise_applied_twice.txt`](outputs/aer_noise_applied_twice.txt)

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
[`outputs/custom_rz_name_2.4.2.txt`](outputs/custom_rz_name_2.4.2.txt)

**Likely cause:** the `BasisTranslator` skips operations whose name is already in the target basis, so a custom
gate that shares the name is trusted as the standard gate. It only disappears if a later resynthesis happens to
absorb its block.

**Note:** on qiskit 2.5.0-2.5.2 the 2-qubit case can hang in `CommutativeCancellation`; that is a separate,
already known issue (Qiskit/qiskit#16937, fixed for 2.6). The 1-qubit case is unaffected by it.

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
[`outputs/rzz_bounds_control_flow_ibm_plugin_2.5.2.txt`](outputs/rzz_bounds_control_flow_ibm_plugin_2.5.2.txt)

**Likely cause:** the angle-wrapping step does not recurse into control-flow blocks; since 2.5 the optimization
stage also synthesises `rzz` inside blocks, so valid inputs now produce invalid outputs.

---

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
outputs/            observed outputs and versions.txt
```
