"""QPY loading fails for wide MCX gates (63 and 127 controls on 2.5.2).

Run from the repository root with: python qpy-wide-mcx/repro.py
This only serializes the gates; it does not decompose or simulate them.
MCX(31) and MCX(32) are controls for the tested release, while wider gates
are written and then fail during QPY loading.
The checked main snapshot also rejects 32 controls with a 31-control cap.
"""
import io
import sys
import qiskit
from qiskit import QuantumCircuit, qpy
from qiskit.circuit.library import MCXGate


print("Python", sys.version.split()[0])
print("qiskit", qiskit.__version__)
for controls in (31, 32, 63, 127):
    gate = MCXGate(controls)
    circuit = QuantumCircuit(gate.num_qubits)
    circuit.append(gate, range(gate.num_qubits))
    payload = io.BytesIO()
    qpy.dump(circuit, payload)
    print(controls, "WRITE_OK", "bytes", len(payload.getvalue()))
    try:
        loaded = qpy.load(io.BytesIO(payload.getvalue()))[0]
        print(controls, "LOAD_OK", loaded.data[0].operation.num_ctrl_qubits)
    except Exception as exc:
        print(controls, "LOAD_FAIL", type(exc).__name__, str(exc))
