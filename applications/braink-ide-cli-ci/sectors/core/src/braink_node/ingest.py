import os
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from .canonical import sha256_hex
from .ledger import LedgerStore
from .storage import atomic_write


def _read_bytes(path: Path, max_bytes: Optional[int] = None) -> bytes:
    """Bound reads and reject oversized input instead of claiming a full capture."""
    if max_bytes is not None and max_bytes < 0:
        raise ValueError("max_bytes must be nonnegative")
    with path.open("rb") as stream:
        data = stream.read() if max_bytes is None else stream.read(max_bytes + 1)
    if max_bytes is not None and len(data) > max_bytes:
        raise ValueError(f"File exceeds artifact byte limit: {path}")
    return data


def artifact_ref_for_path(path: Path) -> str:
    import hashlib
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def store_artifact_bytes(*, artifacts_dir: Path, artifact_ref: str, data: bytes) -> Path:
    if not re.fullmatch(r"[0-9a-f]{64}", artifact_ref) or sha256_hex(data) != artifact_ref:
        raise ValueError("Artifact reference must match its content SHA-256")
    out = artifacts_dir / artifact_ref
    if out.exists():
        if out.is_symlink() or out.read_bytes() != data:
            raise ValueError("Existing artifact has incorrect content")
        return out
    atomic_write(out, data)
    return out


@dataclass(frozen=True)
class IngestedFile:
    abs_path: str
    rel_path: str
    size: int
    artifact_ref: str

    def to_obj(self) -> Dict[str, Any]:
        return asdict(self)


def iter_files(root: Path, *, max_files: int = 5000,
               excluded_roots=()) -> Iterator[Path]:
    if max_files < 0:
        raise ValueError("max_files must be nonnegative")
    if not root.is_dir():
        raise ValueError(f"Workspace directory does not exist: {root}")
    if max_files == 0:
        return
    excluded = {Path(p).resolve() for p in excluded_roots}
    count = 0
    def onerror(error):
        raise error
    for dirpath, dirnames, filenames in os.walk(root, onerror=onerror, followlinks=False):
        parent = Path(dirpath)
        dirnames[:] = sorted(d for d in dirnames if not d.startswith(".") and
                             d != "__pycache__" and not (parent / d).is_symlink() and
                             (parent / d).resolve() not in excluded)
        for name in sorted(filenames):
            p = parent / name
            if name.startswith(".") or p.is_symlink() or not p.is_file() or p.resolve() in excluded:
                continue
            yield p
            count += 1
            if count >= max_files:
                return


def _capture(*, store, path, artifacts_dir, route, max_artifact_bytes):
    data = _read_bytes(path, max_bytes=max_artifact_bytes)
    ref = sha256_hex(data)
    store_artifact_bytes(artifacts_dir=artifacts_dir, artifact_ref=ref, data=data)
    store.append(event_type="kex.raw_base.observed", route=route,
                 payload={"artifact_ref": ref, "source_path": str(path.resolve()),
                          "size": len(data)})
    return ref, len(data)


def ingest_directory(*, store: LedgerStore, directory: Path, artifacts_dir: Path,
                     route: str, max_files: int = 2000, offset: int = 0,
                     max_artifact_bytes: int = 8_000_000) -> Dict[str, Any]:
    if max_files < 0 or offset < 0 or max_artifact_bytes < 0:
        raise ValueError("Ingestion limits and offset must be nonnegative")
    if artifacts_dir.resolve() == directory.resolve():
        raise ValueError("Artifact directory must differ from the source root")
    all_files = list(iter_files(directory, max_files=max_files + offset,
                               excluded_roots=(artifacts_dir, store.path,
                                               Path(str(store.path) + "-journal"))))
    captured = []
    for p in all_files[offset:offset + max_files]:
        ref, size = _capture(store=store, path=p, artifacts_dir=artifacts_dir,
                             route=route, max_artifact_bytes=max_artifact_bytes)
        captured.append(IngestedFile(str(p.resolve()), str(p.relative_to(directory)), size, ref))
    summary = {"directory": str(directory.resolve()), "count": len(captured),
               "offset": offset, "files": [f.to_obj() for f in captured]}
    ref = store.append(event_type="kex.source_state.captured", route=route, payload=summary)
    return {"event_ref": ref, "summary": summary}


def ingest_file(*, store: LedgerStore, file_path: Path, artifacts_dir: Path,
                route: str, max_artifact_bytes: int = 8_000_000) -> Dict[str, Any]:
    if file_path.is_symlink() or not file_path.is_file():
        raise ValueError("Ingestion requires a regular file, not a symbolic link")
    ref, size = _capture(store=store, path=file_path, artifacts_dir=artifacts_dir,
                         route=route, max_artifact_bytes=max_artifact_bytes)
    event_ref = store.append(event_type="kex.source_state.captured", route=route,
                             payload={"file": str(file_path.resolve()), "size": size,
                                      "artifact_ref": ref})
    return {"event_ref": event_ref, "artifact_ref": ref, "size": size}
