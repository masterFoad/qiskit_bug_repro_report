"""Aer applies a density-matrix circuit's noise twice when it follows a statevector circuit in one run().

The noise model holds a Kraus (non-unitary) error. With method="automatic", the first circuit runs with the
statevector method and the second with the density-matrix method. The second circuit's superoperator is
accumulated on top of a stale buffer, so its noise is applied twice and the trace of rho becomes 2.
"""
import numpy as np
import qiskit
import qiskit_aer
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel, phase_amplitude_damping_error

print("qiskit", qiskit.__version__, "qiskit-aer", qiskit_aer.__version__)

noise = NoiseModel(basis_gates=["x", "rz", "sx"])
noise.add_all_qubit_quantum_error(phase_amplitude_damping_error(0.2, 0.0), ["x"])  # Kraus error
sim = AerSimulator(noise_model=noise)

big = QuantumCircuit(14)  # large enough that the automatic method picks statevector
big.h(range(14))
big.measure_all()

small = QuantumCircuit(1)  # small and noisy: the automatic method picks density_matrix
small.x(0)
small.save_density_matrix(label="rho")
small.measure_all()
# Expected: amplitude damping 0.2 after X on |0> gives rho = diag(0.2, 0.8), trace 1.

for name, batch, idx in [("small alone", [small], 0),
                         ("[small, big]", [small, big], 0),
                         ("[big, small]", [big, small], 1)]:
    res = sim.run(batch, shots=2000, seed_simulator=7).result()
    rho = np.asarray(res.data(idx)["rho"]).real
    methods = [r.metadata["method"] for r in res.results]
    print(f"{name:13s} counts={res.get_counts(idx)}")
    print(f"              methods={methods} diag(rho)={np.round(np.diag(rho), 4)} trace={np.trace(rho):.4f}")
