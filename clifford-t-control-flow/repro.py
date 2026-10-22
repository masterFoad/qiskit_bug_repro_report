"""Reproduce a Clifford+T translation failure with one measured qubit.

Run from the repository root: python clifford-t-control-flow/repro.py
Affected versions raise TranspilerError; successful compilation prints COMPILED.
"""
# Report the Python version used for this run.
import platform
# Report the installed Qiskit version.
import qiskit
# Construct the circuit and compile it through Qiskit's preset pipeline.
from qiskit import QuantumCircuit, transpile
# Use Qiskit's complete standard Clifford gate list.
from qiskit.quantum_info import get_clifford_gate_names

# Print the interpreter version before attempting compilation.
print("Python", platform.python_version())
# Print the Qiskit version so failures can be compared across releases.
print("qiskit", qiskit.__version__)

# One qubit and one classical bit suffice; a second qubit is unnecessary.
qc = QuantumCircuit(1, 1)
# Prepare |+> so either measurement outcome can occur.
qc.h(0)
# Store the outcome in classical bit 0.
qc.measure(0, 0)
# Create an if_else operation that runs its body only when the outcome is 1.
with qc.if_test((qc.clbits[0], 1)):
    # X already belongs to the requested Clifford+T basis.
    qc.x(0)

# Compile directly; leave the original error and traceback visible on affected versions.
output = transpile(
    qc,  # The single conditional circuit is sufficient to trigger the bug.
    basis_gates=get_clifford_gate_names() + ["t", "tdg"],  # Select the Clifford+T pipeline.
    optimization_level=2,  # Keep the optimization level of the original reproduction.
)
# This line is reached only if compilation succeeds; counts exclude the branch body.
print("COMPILED", dict(output.count_ops()))
