# KEX_INVARIANT_LOCK: 0.297
# RESOLVE: TOTALITY_V5
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from kex.codes.canonical import sha256_hex
from kex.ledger.store import LedgerStore


def _stable_hash_text(text: str) -> str:
    return sha256_hex(text.encode("utf-8"))


@dataclass(frozen=True)
class InterlinkIndex:
    dekstop_root: str
    entries: List[Dict[str, Any]]

    def to_obj(self) -> Dict[str, Any]:
        return {"dekstop_root": self.dekstop_root, "entries": self.entries}


def build_interlink_index(*, dekstop_root: Path, max_entries: int = 5000) -> InterlinkIndex:
    entries: List[Dict[str, Any]] = []
    count = 0
    for p in dekstop_root.rglob("*"):
        name = p.name
        if name.startswith("."):
            continue
        if p.is_dir():
            continue
        try:
            st = p.stat()
        except FileNotFoundError:
            continue
        entries.append(
            {
                "path": str(p.resolve()),
                "rel": str(p.relative_to(dekstop_root)),
                "size": int(st.st_size),
                "kind": "file",
            }
        )
        count += 1
        if count >= max_entries:
            break
    return InterlinkIndex(dekstop_root=str(dekstop_root.resolve()), entries=entries)


def write_index_artifact(*, artifacts_dir: Path, index_obj: Dict[str, Any]) -> str:
    data = json.dumps(index_obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    aref = sha256_hex(data)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    out = artifacts_dir / aref
    if not out.exists():
        out.write_bytes(data)
    return aref


def ledger_index(
    *,
    store: LedgerStore,
    dekstop_root: Path,
    artifacts_dir: Path,
    route: str,
    max_entries: int = 5000,
) -> Dict[str, Any]:
    idx = build_interlink_index(dekstop_root=dekstop_root, max_entries=max_entries)
    aref = write_index_artifact(artifacts_dir=artifacts_dir, index_obj=idx.to_obj())
    ref = store.append(
        event_type="kex.route.index.updated",
        route=route,
        payload={"dekstop_root": idx.dekstop_root, "artifact_ref": aref, "entry_count": len(idx.entries)},
    )
    return {"event_ref": ref, "artifact_ref": aref, "entry_count": len(idx.entries)}

