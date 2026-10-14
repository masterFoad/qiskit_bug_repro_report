"""Show a custom cx being retained as the target's native CX opcode.

Run: python custom-cx-name-kept-as-native/repro.py
Standard names are reserved; compare the source with native-device semantics.
"""
import platform
import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import Gate, Parameter
from qiskit.circuit.library import CXGate, RZGate, SXGate, XGate
from qiskit.quantum_info import Operator
from qiskit.transpiler import Target

print("python", platform.python_version())
print("qiskit", qiskit.__version__)
custom = Gate("cx", 2, [])
custom.definition = QuantumCircuit(2)
custom.definition.h(0)
target = Target(num_qubits=2)
for op in (RZGate(Parameter("theta")), SXGate(), XGate()):
    target.add_instruction(op, {(0,): None, (1,): None})
target.add_instruction(CXGate(), {(0, 1): None})
for name in ("cx", "custom_cx"):
    gate = custom.copy(name=name)
    source = QuantumCircuit(2)
    source.append(gate, (0, 1))
    out = transpile(source, target=target, optimization_level=0)
    device = QuantumCircuit(2)
    device.global_phase = out.global_phase
    collisions = 0
    for item in out.data:
        op = item.operation
        if op.name == "cx" and op.base_class is not CXGate:
            op = CXGate()
            collisions += 1
        device.append(op, [out.find_bit(q).index for q in item.qubits])
    print("name", name, "custom_cx_retained", collisions)
    print("output_ops", dict(out.count_ops()))
    print("python_definition_matches", Operator(source).equiv(Operator(out)))
    print("native_device_matches", Operator(source).equiv(Operator(device)))
