# Same seed can produce different initial layouts

For one public 16-qubit circuit and Target, three stock preset-manager runs produce three different initial physical-to-input layouts. The runs use optimization level 2, seed 1, one numerical thread, one Qiskit process, and `PYTHONHASHSEED=0`. We observed this on Qiskit 2.6.0 and the recorded main runtime at `f70269034d2ec07699d6c69e33594273c73f8df2`.

This is a seeded reproducibility issue for the checked fixture. The observation does not establish a source-level cause or variability for other circuits. Different valid initial layouts alone do not imply a wrong compiled circuit.

```sh
RAYON_NUM_THREADS=1 QISKIT_PARALLEL=false QISKIT_NUM_PROCS=1 \
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 PYTHONHASHSEED=0 \
python repro.py
```

The script verifies the bundled public fixture digests before loading them:

| File | SHA-256 |
|---|---|
| `fixtures/input.pickle` | `a72cee57aafcfa75737ac8c3188489c30b09eac4b6130dc8cacc42625031caaf` |
| `fixtures/target.pickle` | `0cc8128bb665d19fa53c25e92d76ae43e39462bfe19b0e534eb1741e96cf957e` |

These are trusted recorded Qiskit objects; use the bundled files. Replacing them changes the checked input.

[Release output](outputs/release-2.6.0-fresh.json) records three distinct initial layouts from a completed fresh run. [Main controls](outputs/main-prefix-layout-controls.json) record three distinct stock baseline layouts under the same fixed environment; the paired prefix results are additional harness diagnostics. The [runtime details](outputs/MAIN-RUNTIME.md) binds this main observation to the recorded source and runtime hashes. Earlier release evidence is retained in [its runtime details](outputs/release-2.6.0-details.json); that wrapper lost the exit code after the child produced valid JSON. The fresh run completed with exit 0. A separate root verification also completed with exit 0 and observed two distinct layouts in three trials; see [its output](outputs/release-2.6.0-root.json).

Item 11 concerns seeded RZ-count drift in synthesis. This entry measures initial placement for a separate fixed circuit and Target.
