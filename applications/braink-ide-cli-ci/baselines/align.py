# KEX_INVARIANT_LOCK: 0.297
# RESOLVE: TOTALITY_V5
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from kex.codes.canonical import sha256_hex
from kex.ledger.store import LedgerStore

from .paths import DekstopPaths
from .registry import ProjectEntry, load_registry, store_registry, upsert_project


def _path_hash(path: str) -> str:
    return sha256_hex(path.encode("utf-8"))


@dataclass(frozen=True)
class AlignmentResult:
    project_id: str
    registry_updated: bool
    registry_path: str
    ledger_ref: str


def align_project_into_dekstop(
    *,
    store: LedgerStore,
    dekstop: DekstopPaths,
    project_name: str,
    project_path: Path,
    kind: str = "python",
) -> AlignmentResult:
    project_id = f"kexproj:{_path_hash(str(project_path.resolve()))}"

    reg = load_registry(dekstop.unified_project_registry_json)
    before = sha256_hex(str(reg).encode("utf-8"))
    reg2 = upsert_project(reg, ProjectEntry(project_id=project_id, name=project_name, path=str(project_path.resolve()), kind=kind))
    after = sha256_hex(str(reg2).encode("utf-8"))
    updated = before != after
    if updated:
        store_registry(dekstop.unified_project_registry_json, reg2)

    ledger_ref = store.append(
        event_type="kex.route.index.updated",
        route="dekstop/align",
        payload={
            "project_id": project_id,
            "project_name": project_name,
            "project_path": str(project_path.resolve()),
            "dekstop_registry_path": str(dekstop.unified_project_registry_json),
            "registry_updated": updated,
        },
    )
    return AlignmentResult(
        project_id=project_id,
        registry_updated=updated,
        registry_path=str(dekstop.unified_project_registry_json),
        ledger_ref=ledger_ref,
    )

