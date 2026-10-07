from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from .canonical import sha256_hex, canonical_bytes
from .ledger import LedgerStore
from .ingest import iter_files, store_artifact_bytes


def _stable_hash_text(text: str) -> str:
    return sha256_hex(text.encode("utf-8"))


@dataclass(frozen=True)
class InterlinkIndex:
    dekstop_root: str
    entries: List[Dict[str, Any]]

    def to_obj(self) -> Dict[str, Any]:
        return {"dekstop_root": self.dekstop_root, "entries": self.entries}


def build_interlink_index(*, dekstop_root: Path, max_entries: int = 5000,
                          excluded_roots=()) -> InterlinkIndex:
    entries = []
    for p in iter_files(dekstop_root, max_files=max_entries, excluded_roots=excluded_roots):
        entries.append({"path": str(p.resolve()), "rel": str(p.relative_to(dekstop_root)),
                        "size": p.stat().st_size, "kind": "file"})
    return InterlinkIndex(str(dekstop_root.resolve()), entries)


def write_index_artifact(*, artifacts_dir: Path, index_obj: Dict[str, Any]) -> str:
    data = canonical_bytes(index_obj)
    ref = sha256_hex(data)
    store_artifact_bytes(artifacts_dir=artifacts_dir, artifact_ref=ref, data=data)
    return ref


def ledger_index(*, store: LedgerStore, dekstop_root: Path, artifacts_dir: Path,
                 route: str, max_entries: int = 5000) -> Dict[str, Any]:
    if artifacts_dir.resolve() == dekstop_root.resolve():
        raise ValueError("Artifact directory must differ from source root")
    idx = build_interlink_index(dekstop_root=dekstop_root, max_entries=max_entries,
                                excluded_roots=(artifacts_dir, store.path,
                                                Path(str(store.path) + "-journal")))
    ref = write_index_artifact(artifacts_dir=artifacts_dir, index_obj=idx.to_obj())
    event_ref = store.append(event_type="kex.route.index.updated", route=route,
                             payload={"dekstop_root": idx.dekstop_root,
                                      "artifact_ref": ref, "entry_count": len(idx.entries)})
    return {"event_ref": event_ref, "artifact_ref": ref, "entry_count": len(idx.entries)}
