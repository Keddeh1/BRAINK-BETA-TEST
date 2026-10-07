# KEX_INVARIANT_LOCK: 0.297
# RESOLVE: TOTALITY_V5
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class PlanningPacket:
    action_id: str
    scope: Dict[str, Any]
    provenance_edges: List[Dict[str, Any]]
    proofs: List[Dict[str, Any]]
    falsifiers: List[Dict[str, Any]]
    notes: Optional[str] = None

    def to_obj(self) -> Dict[str, Any]:
        return {
            "action_id": self.action_id,
            "scope": self.scope,
            "provenance_edges": self.provenance_edges,
            "proofs": self.proofs,
            "falsifiers": self.falsifiers,
            "notes": self.notes,
        }

