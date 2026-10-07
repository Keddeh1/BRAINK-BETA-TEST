import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict
from copy import deepcopy
from contextlib import contextmanager
import sqlite3

from .storage import atomic_write


@contextmanager
def registry_lock(path: Path):
    """Serialize alignment updates across independent node processes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path.parent / ".braink-registry-lock.sqlite3", timeout=30) as lock:
        lock.execute("BEGIN IMMEDIATE")
        yield


@dataclass(frozen=True)
class ProjectEntry:
    project_id: str
    name: str
    path: str
    kind: str

    def to_obj(self) -> Dict[str, Any]:
        obj = asdict(self)
        if any(not isinstance(v, str) or not v.strip() for v in obj.values()):
            raise ValueError("Project entry fields must be nonempty strings")
        return obj


def validate_registry(obj: Any) -> Dict[str, Any]:
    if not isinstance(obj, dict) or not isinstance(obj.get("projects"), list):
        raise ValueError("Registry must be an object with a projects list")
    ids = set()
    for project in obj["projects"]:
        if not isinstance(project, dict):
            raise ValueError("Registry project must be an object")
        fields = {key: project.get(key) for key in ("project_id", "name", "path", "kind")}
        ProjectEntry(**fields).to_obj()
        if project["project_id"] in ids:
            raise ValueError("Duplicate project_id in registry")
        ids.add(project["project_id"])
    return obj


def load_registry(path: Path) -> Dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"projects": []}
    return validate_registry(json.loads(raw))


def upsert_project(registry_obj: Dict[str, Any], entry: ProjectEntry) -> Dict[str, Any]:
    result = deepcopy(validate_registry(registry_obj))
    obj = entry.to_obj()
    for i, project in enumerate(result["projects"]):
        if project["project_id"] == entry.project_id:
            # Retain extension metadata supplied by other nodes.
            result["projects"][i] = {**project, **obj}
            break
    else:
        result["projects"].append(obj)
    return result


def store_registry(path: Path, registry_obj: Dict[str, Any]) -> None:
    validate_registry(registry_obj)
    atomic_write(path, (json.dumps(registry_obj, sort_keys=True, indent=2,
                                 allow_nan=False) + "\n").encode("utf-8"))
