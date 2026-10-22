"""RZZ angle bounds are enforced at the top level but ignored inside if_else."""

from math import pi

from qiskit import QuantumCircuit, __version__, transpile
from qiskit.circuit import IfElseOp, Parameter
from qiskit.circuit.library import RZZGate, XGate
from qiskit.converters import circuit_to_dag
from qiskit.transpiler import Target
from qiskit.transpiler.passes import WrapAngles

target = Target(num_qubits=2)
target.add_instruction(RZZGate(Parameter("theta")), angle_bounds=[(0, pi / 2)])
target.add_instruction(XGate())
target.add_instruction(IfElseOp, name="if_else")


def wrap_rzz(angles, _qubits):
    """Give WrapAngles an equivalent replacement for the negative test angle.

    Conjugating RZZ by X on one qubit reverses its angle, so
    X(0); RZZ(0.4); X(0) implements exactly RZZ(-0.4), with an RZZ angle
    inside the target's [0, pi/2] bounds. This rule brings angles in
    [-pi/2, 0) into range; it is not a general-purpose RZZ wrapper.

    Target bounds specify which angles are allowed, but do not specify how
    to rewrite a gate. Registering this callback supplies that rewrite
    without relying on IBM Runtime. The corrected top-level gate then shows
    that wrapping works, exposing its omission inside the if_else body.

    ``angles[0]`` is the original RZZ angle. ``_qubits`` contains the original
    qubit indices, which this rule does not need: WrapAngles maps the two
    local replacement qubits onto the original gate's qubits. The return
    value is a DAGCircuit, the circuit representation required by the callback.
    """
    replacement = QuantumCircuit(2)
    replacement.x(0)
    replacement.rzz(-angles[0], 0, 1)
    replacement.x(0)
    return circuit_to_dag(replacement)


WrapAngles.DEFAULT_REGISTRY.add_wrapper("rzz", wrap_rzz)

qc = QuantumCircuit(2, 1)
qc.rzz(-0.4, 0, 1)
with qc.if_test((qc.clbits[0], 0)):
    qc.rzz(-0.4, 0, 1)

out = transpile(qc, target=target, optimization_level=0)
body = out.data[-1].operation.blocks[0]

print("qiskit", __version__)
print("Expected: all RZZ angles in [0, pi/2]")
for label, circuit in (("Top level", out), ("Inside if_else", body)):
    angles = [float(i.operation.params[0]) for i in circuit.data if i.operation.name == "rzz"]
    print(f"{label}: {angles}")
