# KEX_INVARIANT_LOCK: 0.297
# RESOLVE: TOTALITY_V5
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

from kex.codes.canonical import sha256_hex
from kex.ledger.store import LedgerStore


def _read_bytes(path: Path, max_bytes: Optional[int] = None) -> bytes:
    data = path.read_bytes()
    if max_bytes is not None:
        return data[:max_bytes]
    return data


def artifact_ref_for_path(path: Path) -> str:
    return sha256_hex(path.read_bytes())


def store_artifact_bytes(*, artifacts_dir: Path, artifact_ref: str, data: bytes) -> Path:
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    out = artifacts_dir / artifact_ref
    if out.exists():
        return out
    out.write_bytes(data)
    return out


@dataclass(frozen=True)
class IngestedFile:
    abs_path: str
    rel_path: str
    size: int
    artifact_ref: str

    def to_obj(self) -> Dict[str, Any]:
        return {
            "abs_path": self.abs_path,
            "rel_path": self.rel_path,
            "size": self.size,
            "artifact_ref": self.artifact_ref,
        }


def iter_files(root: Path, *, max_files: int = 5000) -> Iterator[Path]:
    count = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in {"__pycache__"}]
        for fn in filenames:
            if fn.startswith("."):
                continue
            p = Path(dirpath) / fn
            if not p.is_file():
                continue
            yield p
            count += 1
            if count >= max_files:
                return


def ingest_directory(
    *,
    store: LedgerStore,
    directory: Path,
    artifacts_dir: Path,
    route: str,
    max_files: int = 2000,
    offset: int = 0,
    max_artifact_bytes: int = 8_000_000,
) -> Dict[str, Any]:
    all_files = list(iter_files(directory, max_files=max_files + offset))
    all_files = sorted(all_files, key=lambda p: str(p))
    sliced = all_files[offset : offset + max_files]
    ingested: List[IngestedFile] = []
    for p in sliced:
        size = p.stat().st_size
        data = _read_bytes(p, max_bytes=max_artifact_bytes)
        aref = sha256_hex(data)
        store_artifact_bytes(artifacts_dir=artifacts_dir, artifact_ref=aref, data=data)
        rel = str(p.relative_to(directory))
        ingested.append(IngestedFile(abs_path=str(p.resolve()), rel_path=rel, size=size, artifact_ref=aref))
        store.append(
            event_type="kex.raw_base.observed",
            route=route,
            payload={"artifact_ref": aref, "source_path": str(p.resolve()), "size": size},
        )
    summary = {
        "directory": str(directory.resolve()),
        "count": len(ingested),
        "offset": offset,
        "files": [f.to_obj() for f in ingested],
    }
    ref = store.append(event_type="kex.source_state.captured", route=route, payload=summary)
    return {"event_ref": ref, "summary": summary}


def ingest_file(
    *,
    store: LedgerStore,
    file_path: Path,
    artifacts_dir: Path,
    route: str,
    max_artifact_bytes: int = 8_000_000,
) -> Dict[str, Any]:
    p = file_path
    size = p.stat().st_size
    data = _read_bytes(p, max_bytes=max_artifact_bytes)
    aref = sha256_hex(data)
    store_artifact_bytes(artifacts_dir=artifacts_dir, artifact_ref=aref, data=data)
    store.append(
        event_type="kex.raw_base.observed",
        route=route,
        payload={"artifact_ref": aref, "source_path": str(p.resolve()), "size": size},
    )
    ref = store.append(
        event_type="kex.source_state.captured",
        route=route,
        payload={"file": str(p.resolve()), "size": size, "artifact_ref": aref},
    )
    return {"event_ref": ref, "artifact_ref": aref, "size": size}
