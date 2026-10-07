# KEX_INVARIANT_LOCK: 0.297
# RESOLVE: TOTALITY_V5
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DekstopPaths:
    root: Path
    interconnect_root: Path
    unified_project_registry_json: Path
    interconnect_status_json: Path


def default_dekstop_paths() -> DekstopPaths:
    root = Path.home() / "Desktop" / "DEKSTOP"
    inter = root / "K_SYSTEM_INTERCONNECT"
    return DekstopPaths(
        root=root,
        interconnect_root=inter,
        unified_project_registry_json=inter / "UNIFIED_PROJECT_REGISTRY.json",
        interconnect_status_json=inter / "INTERCONNECT_STATUS.json",
    )

