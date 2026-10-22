# RZZ angle bounds are ignored inside control flow

Qiskit compiles a circuit for a target that only accepts `RZZ` angles between
`0` and `pi/2`, but leaves an unsupported negative angle inside an `if_else`
block. Compilation succeeds even though the result violates the target's bounds.

For a beginner-friendly walkthrough of the circuit and its wrapping rule, see
[the detailed explanation](detailed_explanation.md).

[repro.py](repro.py) places the same `RZZ(-0.4)` gate at the top level and
inside a conditional block, then calls `transpile(..., optimization_level=0)`.
It explicitly registers an equivalent replacement, `X(0); RZZ(0.4); X(0)`,
so Qiskit has a rule for bringing the test angle into range.

The target declares only `RZZ`, `X`, and `if_else`. The top-level gate acts as
a control: it comes out as `RZZ(0.4)`, which shows that the rewrite works, while
the copy inside `if_else` still has `-0.4`.
