# KEX_INVARIANT_LOCK: 0.297
# RESOLVE: TOTALITY_V5
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from copy import deepcopy
from .canonical import canonical_bytes


@dataclass(frozen=True)
class ExecutionResult:
    ok: bool
    reason: Optional[str]
    outputs: Dict[str, Any]
    ledger_refs: List[str]

    def __post_init__(self) -> None:
        if not isinstance(self.ok, bool) or not isinstance(self.outputs, dict):
            raise ValueError("Result requires boolean ok and object outputs")
        if self.reason is not None and not isinstance(self.reason, str):
            raise ValueError("reason must be text or None")
        if not isinstance(self.ledger_refs, list) or any(not isinstance(ref, str) for ref in self.ledger_refs):
            raise ValueError("ledger_refs must be a list of strings")
        canonical_bytes(self.to_obj())

    def to_obj(self) -> Dict[str, Any]:
        return deepcopy({
            "ok": self.ok,
            "reason": self.reason,
            "outputs": self.outputs,
            "ledger_refs": self.ledger_refs,
        })

