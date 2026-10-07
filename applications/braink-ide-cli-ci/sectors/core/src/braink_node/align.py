from dataclasses import dataclass
from pathlib import Path
from .canonical import sha256_hex, canonical_bytes
from .ledger import LedgerStore
from .paths import DekstopPaths
from .registry import ProjectEntry, load_registry, store_registry, upsert_project, registry_lock


def _path_hash(path: str) -> str:
    return sha256_hex(path.encode("utf-8"))


@dataclass(frozen=True)
class AlignmentResult:
    project_id: str
    registry_updated: bool
    registry_path: str
    ledger_ref: str


def align_project_into_dekstop(*, store: LedgerStore, dekstop: DekstopPaths,
                             project_name: str, project_path: Path,
                             kind: str = "python") -> AlignmentResult:
    project_path = project_path.resolve(strict=True)
    if not project_path.is_dir():
        raise ValueError("Project path must be a directory")
    project_id = f"kexproj:{_path_hash(str(project_path))}"
    with registry_lock(dekstop.unified_project_registry_json):
        before = load_registry(dekstop.unified_project_registry_json)
        after = upsert_project(before, ProjectEntry(project_id, project_name, str(project_path), kind))
        updated = canonical_bytes(before) != canonical_bytes(after)
        if updated:
            store_registry(dekstop.unified_project_registry_json, after)
    ref = store.append(event_type="kex.route.index.updated", route="dekstop/align",
                       payload={"project_id": project_id, "project_name": project_name,
                                "project_path": str(project_path),
                                "dekstop_registry_path": str(dekstop.unified_project_registry_json),
                                "registry_updated": updated})
    return AlignmentResult(project_id, updated, str(dekstop.unified_project_registry_json), ref)
