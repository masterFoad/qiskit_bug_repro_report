"""Measure scheduling and padding on a 320-qubit QFT."""

from time import perf_counter

import qiskit
from qiskit import transpile
from qiskit.circuit.library import XGate
from qiskit.providers.fake_provider import GenericBackendV2
from qiskit.synthesis.qft import synth_qft_full
from qiskit.transpiler import CouplingMap, PassManager
from qiskit.transpiler.passes import (
    ALAPScheduleAnalysis, PadDelay, PadDynamicalDecoupling, TimeUnitConversion,
)


target = GenericBackendV2(
    409, coupling_map=CouplingMap.from_heavy_hex(13),
    basis_gates=["cz", "rz", "sx", "x", "id"], control_flow=False, seed=0,
).target
circuit = synth_qft_full(320)
circuit.measure_all()
start = perf_counter()
routed = transpile(circuit, target=target, optimization_level=2, seed_transpiler=1234)
print(f"qiskit={qiskit.__version__} qubits={routed.num_qubits} ops={routed.size()}")
print(f"O2 transpile={perf_counter() - start:.3f}s", flush=True)
for label, padding in (
    ("PadDelay", PadDelay(target=target)),
    ("PadDynamicalDecoupling", PadDynamicalDecoupling(target=target, dd_sequence=[XGate(), XGate()])),
):
    times = {}
    manager = PassManager([TimeUnitConversion(target=target), ALAPScheduleAnalysis(target=target), padding])
    start = perf_counter()
    output = manager.run(routed, callback=lambda **kw: times.__setitem__(kw["pass_"].name(), kw["time"]))
    print(f"{label}={times[label]:.3f}s stage={perf_counter() - start:.3f}s "
          f"output_ops={output.size()}", flush=True)
