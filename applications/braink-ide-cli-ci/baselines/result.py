# KEX_INVARIANT_LOCK: 0.297
# RESOLVE: TOTALITY_V5
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class ExecutionResult:
    ok: bool
    reason: Optional[str]
    outputs: Dict[str, Any]
    ledger_refs: List[str]

    def to_obj(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "reason": self.reason,
            "outputs": self.outputs,
            "ledger_refs": self.ledger_refs,
        }

