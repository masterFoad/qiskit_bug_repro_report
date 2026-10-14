"""QPY writes arithmetic-library gates but cannot read them back.

Run from the repository root with: python qpy-arithmetic-gates/repro.py
Each gate is successfully serialized; loading its QPY payload calls a
constructor without the required arguments.
"""
import io
import sys
import qiskit
from qiskit import QuantumCircuit, qpy
from qiskit.circuit.library import (
    HalfAdderGate, IntegerComparatorGate, LinearPauliRotationsGate,
    ModularAdderGate, MultiplierGate,
)


print("Python", sys.version.split()[0])
print("qiskit", qiskit.__version__)
gates = (
    HalfAdderGate(2),
    ModularAdderGate(2),
    MultiplierGate(2),
    IntegerComparatorGate(2, 1),
    LinearPauliRotationsGate(2),
)
for gate in gates:
    circuit = QuantumCircuit(gate.num_qubits)
    circuit.append(gate, range(gate.num_qubits))
    payload = io.BytesIO()
    qpy.dump(circuit, payload)
    print(gate.name, "WRITE_OK", "bytes", len(payload.getvalue()))
    try:
        loaded = qpy.load(io.BytesIO(payload.getvalue()))[0]
        print(gate.name, "LOAD_OK", type(loaded.data[0].operation).__name__)
    except Exception as exc:
        print(gate.name, "LOAD_FAIL", type(exc).__name__, str(exc))
