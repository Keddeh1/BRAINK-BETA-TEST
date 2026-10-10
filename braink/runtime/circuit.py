"""Bounded classical statevector execution; qubit zero is the least significant bit."""

import math


def simulate_circuit(request):
    """Execute H/X/Z/S/CX gates, preserving phase until probabilities are reported.

    Resource limits bound exponential state growth and total gate work. This is
    floating-point classical simulation, not a hardware quantum execution claim.
    """
    qubits = request.get("qubits")
    gates = request.get("gates")
    if type(qubits) is not int or not 1 <= qubits <= 16:
        raise ValueError("qubits must be between 1 and 16")
    if type(gates) is not list or len(gates) > 1024:
        raise ValueError("gate count exceeds budget")
    if len(gates) * (1 << qubits) > 4_194_304:
        raise ValueError("circuit work exceeds budget")
    validated = []
    for gate in gates:
        if type(gate) is not dict:
            raise ValueError("gate requires a mapping")
        op, target = gate.get("op"), gate.get("target")
        if op not in ("H", "X", "Z", "S", "CX"):
            raise ValueError("unsupported gate")
        if type(target) is not int or not 0 <= target < qubits:
            raise ValueError("invalid target")
        control = gate.get("control")
        if op == "CX" and (type(control) is not int or not 0 <= control < qubits or control == target):
            raise ValueError("invalid control")
        validated.append((op, target, control))
    state = [0j] * (1 << qubits)
    state[0] = 1 + 0j
    scale = math.sqrt(0.5)
    for op, target, control in validated:
        mask = 1 << target
        for i in range(len(state)):
            if i & mask:
                continue
            j = i | mask
            a, b = state[i], state[j]
            if op == "H":
                state[i], state[j] = (a + b) * scale, (a - b) * scale
            elif op == "X" or (op == "CX" and i & (1 << control)):
                state[i], state[j] = b, a
            elif op == "Z":
                state[j] = -b
            elif op == "S":
                state[j] = 1j * b
    probabilities = [abs(x) ** 2 for x in state]
    norm = math.fsum(probabilities)
    if not math.isclose(norm, 1.0, abs_tol=1e-10):
        raise RuntimeError("statevector normalization failed")
    return {"qubits": qubits, "basis_order": "little-endian",
            "amplitudes": [[x.real, x.imag] for x in state],
            "probabilities": probabilities, "norm": norm}
