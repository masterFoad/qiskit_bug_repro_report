"""Scheduled measure and reset operations can start off the acquire-alignment grid."""
import qiskit
import qiskit_ibm_runtime
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime.fake_provider import FakePrague

t = FakePrague().target; qc = QuantumCircuit(3, 3)
qc.h(0); qc.cx(0, 1); qc.measure(0, 0); qc.x(2); qc.reset(1); qc.cx(1, 2); qc.measure([1, 2], [1, 2])
print("qiskit", qiskit.__version__, "runtime", qiskit_ibm_runtime.__version__)
print("acquire alignment:", t.acquire_alignment, "sx duration:", t.seconds_to_dt(t["sx"][(0,)].duration))
for method in ("alap", "asap"):
    out = transpile(qc, target=t, scheduling_method=method, optimization_level=1, seed_transpiler=1)
    bad = [(x.operation.name, out.find_bit(x.qubits[0]).index, s) for x, s in zip(out.data, out.op_start_times)
           if x.operation.name in {"measure", "reset"} and s % t.acquire_alignment]
    print(method, "off-grid:", bad)
