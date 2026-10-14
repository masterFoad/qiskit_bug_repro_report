"""rzz angles inside control-flow bodies are not brought into the target's angle bounds.

Target: FakeFez plus RZZGate(theta) on every cz pair with angle_bounds [0, pi/2] (as on fractional-gate Heron
devices). A top-level out-of-bound rzz is folded into range, but the same gate inside an if_else body is left
as is, so the output is not a valid circuit for the target. On 2.5.x a valid body (cx; rz; cx) is also
re-synthesised into an out-of-bound rzz at O2/O3.

Usage: python repro.py              (stock translation)
       python repro.py --ibm-plugin (compare with qiskit-ibm-runtime's "ibm_dynamic_and_fractional" plugin)
"""
import math
import sys
import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ControlFlowOp, Parameter
from qiskit.circuit.library import RZZGate
from qiskit.transpiler import InstructionProperties
from qiskit_ibm_runtime.fake_provider import FakeFez

print("qiskit", qiskit.__version__)
target = FakeFez().target
props = {qargs: InstructionProperties(error=p.error, duration=p.duration) if p else None
         for qargs, p in target["cz"].items()}
target.add_instruction(RZZGate(Parameter("theta")), props, angle_bounds=[(0.0, math.pi / 2)])
print("target has angle bounds:", target.has_angle_bounds(), "| if_else supported:", "if_else" in target.operation_names)


def out_of_bounds(circuit, path="top"):
    found = []
    for inst in circuit.data:
        op = inst.operation
        if isinstance(op, ControlFlowOp):
            for k, block in enumerate(op.blocks):
                found += out_of_bounds(block, f"{path}/{op.name}[{k}]")
        elif op.name == "rzz" and not (-1e-12 <= float(op.params[0]) <= math.pi / 2 + 1e-12):
            found.append((path, round(float(op.params[0]), 6)))
    return found


def in_if_else(body, label):
    qc = QuantumCircuit(2, 1)
    qc.h(0)
    qc.measure(0, 0)
    with qc.if_test((qc.clbits[0], 1)):
        body(qc)
    return label, qc


if "--ibm-plugin" in sys.argv:
    label, qc = in_if_else(lambda q: (q.cx(0, 1), q.rz(0.4, 1), q.cx(0, 1)), "if_else{cx rz(0.4) cx}")
    for method in ("default", "ibm_dynamic_and_fractional"):
        for level in (2, 3):
            out = transpile(qc, target=target, optimization_level=level, seed_transpiler=0,
                            translation_method=method)
            print(f"{label} translation_method={method:27s} O{level}: out-of-bound rzz = {out_of_bounds(out)}")
    sys.exit()

cases = [in_if_else(lambda q: q.rzz(-math.pi / 2, 0, 1), "if_else{rzz(-pi/2)}"),
         in_if_else(lambda q: q.rzz(2.5, 0, 1), "if_else{rzz(2.5)}"),
         in_if_else(lambda q: (q.cx(0, 1), q.rz(0.4, 1), q.cx(0, 1)), "if_else{cx rz(0.4) cx}"),
         in_if_else(lambda q: q.cz(0, 1), "if_else{cz} (control)")]
top = QuantumCircuit(2)
top.rzz(-math.pi / 2, 0, 1)
cases.append(("top-level rzz(-pi/2)", top))
for label, qc in cases:
    for level in range(4):
        results = [out_of_bounds(transpile(qc, target=target, optimization_level=level, seed_transpiler=s))
                   for s in range(4)]
        bad = sum(1 for r in results if r)
        example = next((r for r in results if r), "")
        print(f"{label:26s} O{level}: out of bounds on {bad}/4 seeds {example}")
