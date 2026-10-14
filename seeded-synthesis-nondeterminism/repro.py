"""Show repeated seeded O3 Clifford+RZ synthesis producing different RZ counts.

Run: python seeded-synthesis-nondeterminism/repro.py
Embeds the original 24-qubit adder_8 gate sequence.
"""
import platform
import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import get_clifford_gate_names

print("python", platform.python_version())
print("qiskit", qiskit.__version__)
operations = """
cx:3,2 cx:8,7 cx:14,13 cx:21,20 cx:3,4 cx:8,9 cx:14,15 cx:21,22 h:3 h:8 h:14 h:21 h:3 ccx:0,1,3 h:3 h:8 ccx:5,6,8 h:8 h:14 ccx:11,12,14 h:14 h:21 ccx:18,19,21 h:21 h:3 h:8 h:14 h:21 h:4 h:9
h:15 h:22 h:10 h:16 h:23 h:4 ccx:2,3,4 h:4 h:9 ccx:7,8,9 h:9 h:10 ccx:7,8,10 h:10 h:15 ccx:13,14,15 h:15 h:16 ccx:13,14,16 h:16 h:22 ccx:20,21,22 h:22 h:23 ccx:20,21,23 h:23 cx:6,5 cx:12,11 cx:19,18 cx:5,8
cx:11,14 cx:18,21 h:10 ccx:7,8,10 h:10 h:16 ccx:13,14,16 h:16 h:23 ccx:20,21,23 h:23 h:4 h:10 h:15 h:16 h:23 h:17 h:17 ccx:16,23,17 h:17 h:22 ccx:15,23,22 h:22 h:9 ccx:4,10,9 h:9 h:17 h:9 h:15 h:22
ccx:9,17,22 h:22 h:15 ccx:9,16,15 h:15 h:15 h:22 h:17 h:17 ccx:16,23,17 h:17 h:17 h:10 h:16 h:23 h:10 ccx:7,8,10 h:10 h:16 ccx:13,14,16 h:16 h:23 ccx:20,21,23 h:23 cx:5,8 cx:11,14 cx:18,21 cx:6,5 cx:12,11 cx:19,18
h:10 ccx:7,8,10 h:10 h:16 ccx:13,14,16 h:16 h:23 ccx:20,21,23 h:23 h:23 h:3 h:8 h:14 h:21 h:3 ccx:0,1,3 h:3 h:8 ccx:5,6,8 h:8 h:14 ccx:11,12,14 h:14 h:21 ccx:18,19,21 h:21 h:3 h:8 h:14 h:21
cx:3,2 cx:8,7 cx:14,13 cx:21,20 cx:6,5 cx:12,11 cx:19,18 cx:6,8 cx:12,14 cx:19,21 cx:4,6 cx:9,12 cx:15,19 h:3 h:8 h:14 h:21 h:3 ccx:0,1,3 h:3 h:8 ccx:5,6,8 h:8 h:14 ccx:11,12,14 h:14 h:21 ccx:18,19,21 h:21 h:3
h:8 h:14 h:21 cx:3,2 cx:8,7 cx:14,13 cx:21,20 h:3 h:8 h:14 h:21 h:3 ccx:0,1,3 h:3 h:8 ccx:5,6,8 h:8 h:14 ccx:11,12,14 h:14 h:21 ccx:18,19,21 h:21 h:3 h:8 h:14 h:21 cx:6,5 cx:12,11 cx:19,18
cx:4,6 cx:9,12 cx:15,19 cx:6,8 cx:12,14 cx:19,21 cx:1,0 cx:6,5 cx:12,11 cx:19,18 x:0 x:2 x:5 x:7 x:11 x:13 cx:3,2 cx:8,7 cx:14,13 h:3 h:8 h:14 h:3 ccx:0,1,3 h:3 h:8 ccx:5,6,8 h:8 h:14 ccx:11,12,14
h:14 h:3 h:8 h:14 cx:6,5 cx:12,11 h:10 ccx:7,8,10 h:10 h:16 ccx:13,14,16 h:16 cx:5,8 cx:11,14 h:10 ccx:7,8,10 h:10 h:16 ccx:13,14,16 h:16 h:10 h:16 h:15 h:15 ccx:9,16,15 h:15 h:9 h:9 ccx:4,10,9 h:9
h:4 h:10 h:16 h:10 ccx:7,8,10 h:10 h:16 ccx:13,14,16 h:16 cx:5,8 cx:11,14 h:10 ccx:7,8,10 h:10 h:16 ccx:13,14,16 h:16 cx:6,5 cx:12,11 h:9 ccx:7,8,9 h:9 h:15 ccx:13,14,15 h:15 h:4 ccx:2,3,4 h:4 h:4 h:9
h:10 h:15 h:16 h:3 h:8 h:14 h:3 ccx:0,1,3 h:3 h:8 ccx:5,6,8 h:8 h:14 ccx:11,12,14 h:14 h:3 h:8 h:14 cx:3,4 cx:8,9 cx:14,15 cx:3,2 cx:8,7 cx:14,13 x:0 x:2 x:5 x:7 x:11 x:13
"""
circuit = QuantumCircuit(24)
for token in operations.split():
    name, qubits = token.split(":")
    getattr(circuit, name)(*map(int, qubits.split(",")))
print("input_qubits", circuit.num_qubits, "input_operations", dict(circuit.count_ops()))
counts = [transpile(circuit, basis_gates=get_clifford_gate_names() + ["rz"],
                    optimization_level=3, seed_transpiler=0).count_ops().get("rz", 0)
          for _ in range(12)]
print("runs", len(counts), "seed_transpiler", 0)
print("rz_counts", counts)
print("min", min(counts), "max", max(counts), "unique_counts", len(set(counts)))
print("stable", len(set(counts)) == 1)
