# CommutativeCancellation drops small rotations

Two `RZ(6e-5)` gates should combine into `RZ(1.2e-4)`. Instead, `CommutativeCancellation` removes both, changing the circuit's behavior. The operator distance from the original is `6e-5`, even after ignoring global phase. The same problem occurs at transpiler optimization levels 2 and 3 when CX gates separate the rotations.

From this directory, run:

```sh
python repro.py
```

The script checks the pass directly and both optimization levels, printing `REPRODUCED` or `NOT_REPRODUCED`. It flags the bug only when the rotations disappear and the operator distance exceeds `1e-6`. It also checks that a single `RZ(1.2e-4)` gate survives, showing that the problem occurs when merging gates. `NOT_REPRODUCED` means this specific bug was not detected.

