# Understanding the RZZ angle-bounds reproduction

This guide explains [repro.py](repro.py) for someone who knows basic Python but
is new to Qiskit and quantum computing.

The script demonstrates a compiler bug: **Qiskit corrects an unsupported gate
angle at the outer level of a circuit, but leaves the same unsupported angle
inside a conditional block.** The result below was reproduced with Qiskit 2.6.0.

The script builds and compiles a circuit, then inspects its instructions.
It does not execute the circuit on a quantum computer or simulator.

## 1. The few concepts you need

| Term | Meaning in this example |
| --- | --- |
| **Classical bit** | An ordinary bit holding `0` or `1`. The condition reads one of these. |
| **Qubit** | A quantum system with two basic states, written `\|0⟩` and `\|1⟩`. A general state can be a superposition of them, described by complex amplitudes. |
| **Gate** | An operation that changes the quantum state. Here we use `RZZ` and `X`. |
| **Circuit** | A description of gates and control-flow instructions, including which qubits they act on. |
| **Angle** | A numerical parameter controlling a rotation gate. Qiskit uses radians here: `pi` radians is 180 degrees. |
| **Target** | A description of the operations and parameter values a particular device can support. |
| **Transpilation** | Compilation of a circuit into a form suitable for a target. |
| **Control flow** | Instructions such as a conditional block, whose execution depends on a classical value. |

The symbols `|0⟩` and `|1⟩` are names for quantum states. For two qubits,
`|00⟩`, `|01⟩`, `|10⟩`, and `|11⟩` name the four basic states.

## 2. The input circuit

These lines construct the circuit being tested:

```python
qc = QuantumCircuit(2, 1)
qc.rzz(-0.4, 0, 1)
with qc.if_test((qc.clbits[0], 0)):
    qc.rzz(-0.4, 0, 1)
```

`QuantumCircuit(2, 1)` creates two qubits and one classical bit. Qiskit uses
zero-based indices, so the qubits are numbered `0` and `1`.

In `qc.rzz(-0.4, 0, 1)`, the arguments mean:

| Argument | Meaning |
| --- | --- |
| `-0.4` | The RZZ rotation angle, in radians. |
| `0` | The first qubit the gate acts on. |
| `1` | The second qubit the gate acts on. |

There are two copies of exactly the same gate. The first is at the **top level**,
meaning directly in `qc`. The second is inside a conditional body.

The condition `(qc.clbits[0], 0)` means “execute this body when classical bit 0
equals zero.” It does not measure a qubit. The `with` statement records the body
in the circuit while Python runs; the classical condition belongs to the circuit's
execution. Qiskit represents this construct as an `IfElseOp`, even though this
example has no `else` branch. See the
[QuantumCircuit control-flow API](https://quantum.cloud.ibm.com/docs/en/api/qiskit/2.4/qiskit.circuit.QuantumCircuit#if_test).

### Why can the condition work without a measurement?

**A classical bit already has a value before any measurement writes to it.**
In the usual Qiskit execution model, including Qiskit Aer, classical bits start
at `0`. IBM's [control-flow guide](https://quantum.cloud.ibm.com/docs/en/guides/classical-feedforward-and-control-flow)
also uses an unmeasured classical bit with value zero in a register condition.

The classical bit and qubit with index `0` are separate objects. They are not
automatically connected: applying a gate to qubit 0 does not update classical
bit 0. A measurement such as `qc.measure(0, 0)` explicitly writes the measured
value of qubit 0 into classical bit 0.

Our reproduction never writes to its classical bit, so its execution logic is:

```text
Classical bit c0 starts at 0.
Apply the first RZZ gate; c0 is still 0.
Check whether c0 equals 0: yes.
Execute the RZZ gate inside the conditional block.
```

Thus, in this example, the condition would always be true during execution.
It does not depend on an unknown qubit value. If the condition tested `1`
instead, the body would not execute under the same initialization.

To make a condition depend on a quantum measurement outcome, a circuit would
measure a qubit into that classical bit **before** the condition. For example,
`qc.measure(0, 0)` would make the following `if_test((qc.clbits[0], 0))` check
whether that measurement returned zero. Adding such a measurement to our
reproduction would also require adding measurement support to its custom target.

There is a separate reason measurement is unnecessary for this bug report:
**the script only builds and transpiles the circuit.** During construction,
`qc.clbits[0]` identifies a classical wire; Python is not reading its execution
value. The `with` block records a conditional instruction. In the tested
compilation, that instruction remains in the output, where its RZZ angle can
be inspected without executing either branch.

### Reading the circuit drawing

Here is the input drawing produced by Qiskit:

```text
                  ┌──────              ───────┐
q_0: ─■───────────┤       ──■─────────        ├─
      │ZZ(-0.4)   │ If-0    │ZZ(-0.4)   End-0 │
q_1: ─■───────────┤       ──■─────────        ├─
                  └──╥───              ───────┘
                ┌────╨────┐
c: 1/═══════════╡ c_0=0x0 ╞═════════════════════
                └─────────┘
```

Read it from left to right. The connected squares marked `ZZ(-0.4)` represent
one gate acting on both qubits. The double line carries the classical bit.
`0x0` is hexadecimal notation for zero. `If-0` and `End-0` mark the conditional
region; the `0` in those labels identifies the region.

The example does not need a measurement: the compiler bug is visible simply
by retaining a conditional block and inspecting the compiled instructions.

## 3. What RZZ does

`RZZ(theta)` is a two-qubit rotation. Its action depends on whether the two
qubit values agree. It changes the **phases** of their amplitudes: the complex
factors that determine how quantum states interfere in later operations.

| Basic states | Factor applied to their amplitudes |
| --- | --- |
| `\|00⟩`, `\|11⟩` — the bits agree | `exp(-i * theta / 2)` |
| `\|01⟩`, `\|10⟩` — the bits differ | `exp(+i * theta / 2)` |

Here `i` is the imaginary unit, satisfying `i² = -1`. These factors have
magnitude one. RZZ does not flip the basic bit values, and it can entangle
suitable superposition states. Its matrix is documented in the
[RZZGate reference](https://quantum.cloud.ibm.com/docs/en/api/qiskit/2.3/qiskit.circuit.library.RZZGate).

For this reproduction, the key fact is that `RZZ(-0.4)` is a valid quantum
operation. The restriction on negative angles comes from our chosen target.

## 4. The target's restrictions

```python
target = Target(num_qubits=2)
target.add_instruction(RZZGate(Parameter("theta")), angle_bounds=[(0, pi / 2)])
target.add_instruction(XGate())
target.add_instruction(IfElseOp, name="if_else")
```

This builds a small device description with three supported operations:

| Operation | Why the example needs it |
| --- | --- |
| `RZZ` | The gate whose angle is restricted. |
| `X` | Used in the equivalent replacement described below. |
| `if_else` | Allows the circuit's conditional block. |

`Parameter("theta")` is a symbolic placeholder: the target supports an RZZ
gate with a variable angle. The actual circuit uses the concrete number `-0.4`.

`angle_bounds=[(0, pi / 2)]` gives the inclusive allowed interval for RZZ's
single parameter. Numerically, this is approximately `[0, 1.5708]`.
Thus `0.4` is allowed, while `-0.4` is outside the range.

Omitting per-qubit instruction properties declares global support for these
operations on suitable qubits. No device connection, calibration data, or IBM
account is involved. These target declarations describe capabilities; they do
not add gates to `qc`. See the
[Target API](https://quantum.cloud.ibm.com/docs/en/api/qiskit/2.3/qiskit.transpiler.Target).

## 5. How the replacement preserves the quantum operation

The compiler needs a way to implement `RZZ(-0.4)` using allowed operations.
For this angle, we provide:

```text
RZZ(-0.4)  →  X on qubit 0; RZZ(+0.4); X on qubit 0
```

The `X` gate swaps `|0⟩` and `|1⟩`. Applying it twice restores the original
state, provided nothing intervenes. These properties follow from the
[XGate definition](https://quantum.cloud.ibm.com/docs/en/api/qiskit/2.3/qiskit.circuit.library.XGate).

Here an RZZ gate sits between the two X gates, so their effect needs care:

1. The first X flips one qubit. Equal bit values become different, and different
   values become equal.
2. RZZ therefore applies the opposite entry from the phase table above.
3. The second X restores the bit values, preserving the acquired phase.

Swapping the two phase factors has exactly the effect of reversing the RZZ
angle. The identity works for any input state, including superpositions.
It introduces no extra global phase.

The replacement uses two supported X gates and an RZZ angle of `+0.4`, which
satisfies the target's bounds. Simply changing `-0.4` to `+0.4` without the X
gates would generally change the quantum operation.

### Optional mathematical explanation

The Z operation leaves `|0⟩` unchanged and multiplies `|1⟩` by `-1`.
Write `Z₀Z₁` for applying Z on both qubits and `X₀` for X on qubit 0.
RZZ has the definition:

```text
RZZ(theta) = exp(-i * theta/2 * Z₀Z₁)
```

Since `XZX = -Z` on one qubit:

```text
X₀ (Z₀Z₁) X₀ = -Z₀Z₁

X₀ RZZ(theta) X₀
    = exp(+i * theta/2 * Z₀Z₁)
    = RZZ(-theta)
```

Setting `theta = 0.4` gives the replacement used by the script.

## 6. What `wrap_rzz` does

With its explanatory docstring omitted, the callback is:

```python
def wrap_rzz(angles, _qubits):
    replacement = QuantumCircuit(2)
    replacement.x(0)
    replacement.rzz(-angles[0], 0, 1)
    replacement.x(0)
    return circuit_to_dag(replacement)
```

A **callback** is a function given to another part of a program to call when
needed. This one builds the three-gate replacement above.

| Part | Meaning for this example |
| --- | --- |
| `angles` | The original gate's parameters. Its only angle is `angles[0] = -0.4`. |
| `-angles[0]` | Negates the angle, producing `+0.4`. |
| `_qubits` | The original qubit indices. The leading underscore signals that this function deliberately does not use the argument. |
| `replacement` | A small, separate circuit with two local qubits and no classical bits. |
| `circuit_to_dag(...)` | Converts the replacement to the representation expected by the compiler callback. |

A **DAG** is a directed acyclic graph. In this context, it represents operations
and the dependencies that determine their ordering. Qiskit uses this representation
internally while transforming circuits. The conversion changes the representation,
not the quantum operation.

The replacement uses local qubit numbers `0` and `1`. When it substitutes this
circuit, Qiskit maps those local qubits onto the original RZZ gate's qubits.
That is why this rule does not need to inspect `_qubits`.

**Scope of this wrapper:** it brings negative angles in `[-pi/2, 0)` into the
allowed interval. Although the sign-flip identity holds generally, this function
does not bring every possible angle into range. For example, negating `2.0`
produces `-2.0`, which is still outside the target's bounds.

## 7. Why register the wrapper?

```python
WrapAngles.DEFAULT_REGISTRY.add_wrapper("rzz", wrap_rzz)
```

`WrapAngles` is a transpiler **pass**, meaning one step of the compilation
process. Its registry associates a gate name with a function that constructs
an equivalent replacement when an angle falls outside the target's bounds.
The target supplies the restriction; this callback supplies the rewrite.
This division is described in Qiskit's
[angle-bounds documentation](https://quantum.cloud.ibm.com/docs/en/api/qiskit/2.2/providers#angle-bounds-on-gates).

The line above passes the function itself, `wrap_rzz`, without calling it.
The default registry is shared within the Python process, so the subsequent
`transpile(...)` call can use it.

Supplying the rule explicitly keeps the reproduction self-contained. It works
with Qiskit and its required dependencies, without depending on IBM Runtime
to register a rule through its installed plugins.

The top-level gate is a useful comparison: it demonstrates that the rule is
available and successfully used. The unchanged gate inside `if_else` then
reveals the difference in how the two locations are handled.

## 8. Compiling and inspecting the result

```python
out = transpile(qc, target=target, optimization_level=0)
```

This asks Qiskit to compile `qc` for the target and return the compiled circuit
as `out`. Optimization level 0 keeps the example easy to inspect; target
translation still takes place. It does not execute quantum gates or return
measurement results. See the
[transpile API](https://quantum.cloud.ibm.com/docs/en/api/qiskit/2.3/compiler#transpile).

The observed compiled circuit has this structure:

```text
out
├── X on qubit 0
├── RZZ(+0.4) on qubits 0 and 1
├── X on qubit 0
└── if_else: classical bit 0 == 0
    └── true body
        └── RZZ(-0.4) on qubits 0 and 1
```

The first gate was replaced successfully. The gate inside the conditional body
was left unchanged.

The script extracts that body with:

```python
body = out.data[-1].operation.blocks[0]
```

| Expression | What it selects |
| --- | --- |
| `out.data` | The outer circuit's instruction sequence. |
| `[-1]` | Its last instruction, which is `if_else` in this reproduction. |
| `.operation` | The operation stored in that instruction. |
| `.blocks[0]` | The first block: the circuit executed when the condition is true. |

This indexing is deliberately specific to this small circuit. A general checker
would find control-flow operations and recursively inspect all their blocks.

Finally, the script checks `out` and `body` separately:

```python
for label, circuit in (("Top level", out), ("Inside if_else", body)):
    angles = [float(i.operation.params[0]) for i in circuit.data if i.operation.name == "rzz"]
    print(f"{label}: {angles}")
```

For each circuit, the list comprehension selects RZZ instructions, reads their
first parameter, and converts it to a plain Python `float` for consistent output.
Iterating over `out.data` alone would encounter the `if_else` container without
automatically visiting its contents. That is why the body is inspected separately.

## 9. Running it and interpreting the output

From the repository root, using the existing environment:

```sh
.venv/bin/python rzz-angle-bounds-in-control-flow/repro.py
```

Observed output with Qiskit 2.6.0:

```text
qiskit 2.6.0
Expected: all RZZ angles in [0, pi/2]
Top level: [0.4]
Inside if_else: [-0.4]
```

| Location | Expected after applying this wrapper | Observed | Within bounds? |
| --- | --- | --- | --- |
| Top level | `X; RZZ(+0.4); X` | `X; RZZ(+0.4); X` | Yes |
| Conditional body | `X; RZZ(+0.4); X` | `RZZ(-0.4)` | No |

The printed lists contain gate parameters, not measurement probabilities.
The line beginning `Expected:` is an explanatory message, not an assertion.
The program can exit successfully while its output demonstrates the bug.

The observed behavior is consistent with angle wrapping failing to visit the
nested body. This example establishes the missing correction at that location;
it does not by itself diagnose every internal compiler path.

To display the input and compiled circuits without editing the script, run this
from the repository root:

```sh
.venv/bin/python - <<'PY'
import runpy

example = runpy.run_path("rzz-angle-bounds-in-control-flow/repro.py")
print("Input circuit:")
print(example["qc"].draw(output="text", fold=-1))
print("Compiled circuit:")
print(example["out"].draw(output="text", fold=-1))
PY
```

This first runs the reproduction, then prints its two circuit drawings.

## 10. What the bug means

A compiler must preserve the intended quantum operation while producing
instructions supported by the selected target. The wrapper shows that both
requirements can be met for this input angle.

Here the compiled conditional body still requests a gate outside the target's
declared capabilities. Compilation returns a circuit despite that violation.
This is evidence of invalid compiled instructions for this target; the script
makes no claim about measured hardware results.

No simulation, noise model, or measurement statistics are needed to demonstrate
that problem. The relevant evidence is the stored angle `-0.4` and the declared
allowed interval `[0, pi/2]`. The wrapper supplies the replacement rule, but the
compiler must also apply it inside the conditional body to correct this case.
