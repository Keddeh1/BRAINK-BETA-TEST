# KEX_INVARIANT_LOCK: 0.297
# RESOLVE: TOTALITY_V5
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from copy import deepcopy
from .canonical import canonical_bytes


@dataclass(frozen=True)
class PlanningPacket:
    action_id: str
    scope: Dict[str, Any]
    provenance_edges: List[Dict[str, Any]]
    proofs: List[Dict[str, Any]]
    falsifiers: List[Dict[str, Any]]
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.action_id, str) or not self.action_id.strip():
            raise ValueError("action_id must be a nonempty string")
        if not isinstance(self.scope, dict):
            raise ValueError("scope must be an object")
        for value in (self.provenance_edges, self.proofs, self.falsifiers):
            if not isinstance(value, list) or any(not isinstance(x, dict) for x in value):
                raise ValueError("Packet collections must be lists of objects")
        if self.notes is not None and not isinstance(self.notes, str):
            raise ValueError("notes must be text or None")
        canonical_bytes(self.to_obj())

    def to_obj(self) -> Dict[str, Any]:
        return deepcopy({
            "action_id": self.action_id,
            "scope": self.scope,
            "provenance_edges": self.provenance_edges,
            "proofs": self.proofs,
            "falsifiers": self.falsifiers,
            "notes": self.notes,
        })

