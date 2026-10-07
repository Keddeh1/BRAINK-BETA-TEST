# KEX_INVARIANT_LOCK: 0.297
# RESOLVE: TOTALITY_V5
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ProjectEntry:
    project_id: str
    name: str
    path: str
    kind: str

    def to_obj(self) -> Dict[str, Any]:
        return {"project_id": self.project_id, "name": self.name, "path": self.path, "kind": self.kind}


def load_registry(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"projects": []}
    return json.loads(path.read_text(encoding="utf-8"))


def upsert_project(registry_obj: Dict[str, Any], entry: ProjectEntry) -> Dict[str, Any]:
    projects = list(registry_obj.get("projects", []))
    updated = False
    for i, p in enumerate(projects):
        if p.get("project_id") == entry.project_id:
            projects[i] = entry.to_obj()
            updated = True
            break
    if not updated:
        projects.append(entry.to_obj())
    registry_obj["projects"] = projects
    return registry_obj


def store_registry(path: Path, registry_obj: Dict[str, Any]) -> None:
    path.write_text(json.dumps(registry_obj, sort_keys=True, indent=2) + "\n", encoding="utf-8")

