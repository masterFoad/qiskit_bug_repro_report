"""Print three stock initial layouts for the bundled representative fixture."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import pickle
from pathlib import Path


ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "fixtures" / "input.pickle"
TARGET = ROOT / "fixtures" / "target.pickle"
EXPECTED_ENV = {
    "RAYON_NUM_THREADS": "1",
    "QISKIT_PARALLEL": "false",
    "QISKIT_NUM_PROCS": "1",
    "OMP_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "PYTHONHASHSEED": "0",
}
EXPECTED_INPUT_SHA256 = "a72cee57aafcfa75737ac8c3188489c30b09eac4b6130dc8cacc42625031caaf"
EXPECTED_TARGET_SHA256 = "0cc8128bb665d19fa53c25e92d76ae43e39462bfe19b0e534eb1741e96cf957e"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def numeric_initial_layout(circuit):
    layout = getattr(circuit, "_layout", None)
    if layout is None:
        return None
    indices = layout.input_qubit_mapping
    return sorted(
        (int(physical), int(indices.get(qubit, -1)))
        for physical, qubit in layout.initial_layout.get_physical_bits().items()
    )


def main() -> None:
    for key, value in EXPECTED_ENV.items():
        if os.environ.get(key) != value:
            raise SystemExit(f"fixed_environment_required:{key}")
    input_sha, target_sha = sha256(INPUT), sha256(TARGET)
    if input_sha != EXPECTED_INPUT_SHA256 or target_sha != EXPECTED_TARGET_SHA256:
        raise SystemExit("fixture_hash_mismatch")
    from qiskit import __version__
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    original = pickle.loads(INPUT.read_bytes())
    target = pickle.loads(TARGET.read_bytes())
    layouts = []
    for trial in range(1, 4):
        output = generate_preset_pass_manager(
            target=target, optimization_level=2, seed_transpiler=1
        ).run(copy.deepcopy(original))
        layouts.append({"trial": trial, "initial_layout": numeric_initial_layout(output)})
    print(json.dumps({
        "schema": 1,
        "qiskit_version": __version__,
        "input_sha256": input_sha,
        "target_sha256": target_sha,
        "optimization_level": 2,
        "seed_transpiler": 1,
        "environment": EXPECTED_ENV,
        "cpu_count": os.cpu_count(),
        "original_num_qubits": original.num_qubits,
        "baseline_initial_layouts": layouts,
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
