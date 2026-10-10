"""User-supplied admission protocol. Production adapters are deliberately unbound."""
import struct
import threading


class AdmissionError(RuntimeError):
    pass


class Web4Runtime:
    def __init__(self, architecture, exchange=None, verifier=None, kex=None, ledger=None):
        if type(architecture) is not bytes or len(architecture) != 4:
            raise ValueError("Architecture requires four canonical bytes")
        self.architecture = architecture
        self.exchange = exchange
        self.verifier = verifier
        self.kex = kex
        self.ledger = ledger
        self.failure = None
        self.lock = threading.Lock()
        self.state = "IDLE" if all(x is not None for x in (exchange, verifier, kex, ledger)) else "UNBOUND"

    def receive_update(self):
        with self.lock:
            if self.state != "IDLE":
                raise AdmissionError(self.state)
            self.state = "VERIFYING"
            try:
                wire, payload = self.exchange.receive()
                if type(wire) is not bytes or len(wire) != 116:
                    raise AdmissionError("WIRE_LENGTH_MUST_BE_116")
                context = wire[:52]
                magic, epoch, arch, length, target = struct.unpack(">4sQ4sI32s", context)
                if magic != b"KEX!" or arch != self.architecture:
                    raise AdmissionError("MAGIC_OR_ARCHITECTURE_REJECTED")
                floor = self.ledger.epoch_floor()
                if type(floor) is not int or not 0 <= floor < 2**64:
                    raise AdmissionError("INVALID_LEDGER_FLOOR")
                if epoch <= floor:
                    raise AdmissionError("REPLAY_OR_DOWNGRADE")
                if self.verifier.verify(wire[52:], context) is not True:
                    raise AdmissionError("ED25519_VERIFICATION_FAILED")
                if type(payload) is not bytes or len(payload) != length:
                    raise AdmissionError("PAYLOAD_LENGTH_MISMATCH")
                if self.kex.validate(context, target, payload) is not True:
                    raise AdmissionError("KEX_SUBSTRATE_REJECTED")
                self.state = "COMMITTING"
                receipt = self.ledger.accept(floor, epoch, wire, payload)
                if type(receipt) is not str or not receipt:
                    raise AdmissionError("DURABLE_RECEIPT_MISSING")
                self.state = "IDLE"
                return receipt
            except Exception as exc:
                self.state = "HALTED"
                self.failure = str(exc) if isinstance(exc, AdmissionError) else type(exc).__name__
                raise AdmissionError(self.failure) from exc
