# KEX_INVARIANT_LOCK: 0.297
# RESOLVE: TOTALITY_V5
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .canonical import sha256_hex, canonical_bytes
from .indexer import ledger_index
from .ingest import ingest_directory
from .paths import DekstopPaths
from .ledger import LedgerStore


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(obj, dict):
            return None
        return obj
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, UnicodeDecodeError, OSError):
        return None


@dataclass(frozen=True)
class PassFinding:
    finding_id: str
    severity: str  # info|warn|blocker
    title: str
    detail: Dict[str, Any]

    def to_obj(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "severity": self.severity,
            "title": self.title,
            "detail": self.detail,
        }


def _finding_id(title: str, detail: Dict[str, Any]) -> str:
    return sha256_hex(canonical_bytes({"title": title, "detail": detail}))


def _discover_projects(dekstop_root: Path) -> List[Path]:
    projects_dir = dekstop_root / "projects"
    if not projects_dir.exists():
        return []
    out: List[Path] = []
    for p in sorted(projects_dir.iterdir()):
        if p.name.startswith("."):
            continue
        if p.is_dir() and not p.is_symlink():
            out.append(p)
    return out


def run_dekstop_pass(
    *,
    store: LedgerStore,
    dekstop: DekstopPaths,
    artifacts_dir: Path,
    pass_route: str,
    ingest_dekstop_root: bool = False,
    index_max_entries: int = 5000,
    ingest_max_files: int = 500,
) -> Dict[str, Any]:
    findings: List[PassFinding] = []

    if not dekstop.root.is_dir():
        f = PassFinding(
            finding_id=_finding_id("DEKSTOP root missing", {"path": str(dekstop.root)}),
            severity="blocker",
            title="DEKSTOP root missing",
            detail={"path": str(dekstop.root)},
        )
        findings.append(f)
        ref = store.append(event_type="kex.unresolved.detected", route=pass_route, payload={"findings": [x.to_obj() for x in findings]})
        return {"event_ref": ref, "findings": [x.to_obj() for x in findings]}

    if ingest_dekstop_root:
        ingest_directory(
            store=store,
            directory=dekstop.root,
            artifacts_dir=artifacts_dir,
            route=f"{pass_route}/ingest_dekstop_root",
            max_files=ingest_max_files,
        )

    idx_res = ledger_index(
        store=store,
        dekstop_root=dekstop.root,
        artifacts_dir=artifacts_dir,
        route=f"{pass_route}/index",
        max_entries=index_max_entries,
    )
    findings.append(
        PassFinding(
            finding_id=_finding_id("DEKSTOP index refreshed", idx_res),
            severity="info",
            title="DEKSTOP index refreshed",
            detail=idx_res,
        )
    )

    reg = _read_json(dekstop.unified_project_registry_json)
    from .registry import validate_registry
    if reg is not None:
        try:
            validate_registry(reg)
        except ValueError:
            reg = None
    if reg is None:
        findings.append(
            PassFinding(
                finding_id=_finding_id("Unified project registry missing/unreadable", {"path": str(dekstop.unified_project_registry_json)}),
                severity="warn",
                title="Unified project registry missing/unreadable",
                detail={"path": str(dekstop.unified_project_registry_json)},
            )
        )
    else:
        projects = reg.get("projects", [])
        findings.append(
            PassFinding(
                finding_id=_finding_id("Unified project registry loaded", {"count": len(projects)}),
                severity="info",
                title="Unified project registry loaded",
                detail={"count": len(projects)},
            )
        )
        disk_projects = _discover_projects(dekstop.root)
        disk_paths = {str(p.resolve()) for p in disk_projects}
        reg_paths = {str((dekstop.root / p["path"]).resolve()) for p in projects if isinstance(p, dict) and p.get("path")}
        missing = sorted(disk_paths - reg_paths)
        if missing:
            findings.append(
                PassFinding(
                    finding_id=_finding_id("Projects on disk missing from registry", {"missing": missing[:50]}),
                    severity="warn",
                    title="Projects on disk missing from registry",
                    detail={"missing": missing[:200]},
                )
            )

    status = _read_json(dekstop.interconnect_status_json)
    if status is None:
        findings.append(
            PassFinding(
                finding_id=_finding_id("Interconnect status missing/unreadable", {"path": str(dekstop.interconnect_status_json)}),
                severity="warn",
                title="Interconnect status missing/unreadable",
                detail={"path": str(dekstop.interconnect_status_json)},
            )
        )
    else:
        findings.append(
            PassFinding(
                finding_id=_finding_id("Interconnect status loaded", {"keys": sorted(list(status.keys()))[:50]}),
                severity="info",
                title="Interconnect status loaded",
                detail={"keys": sorted(list(status.keys()))},
            )
        )

    for artifact in (dekstop.unified_project_registry_json, dekstop.interconnect_status_json):
        if artifact.exists() and _read_json(artifact) is None:
            findings.append(PassFinding(_finding_id("Invalid interconnect JSON", {"path": str(artifact)}),
                                        "blocker", "Invalid interconnect JSON", {"path": str(artifact)}))
    if dekstop.unified_project_registry_json.exists() and reg is None:
        findings.append(PassFinding(_finding_id("Invalid project registry", {}), "blocker",
                                    "Invalid project registry", {"path": str(dekstop.unified_project_registry_json)}))
    ref = store.append(
        event_type="kex.packet.compiled",
        route=pass_route,
        payload={"kind": "dekstop_pass", "findings": [x.to_obj() for x in findings]},
    )
    return {"event_ref": ref, "findings": [x.to_obj() for x in findings]}

