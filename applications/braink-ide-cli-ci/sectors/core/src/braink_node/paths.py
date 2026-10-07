from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class DekstopPaths:
    root: Path
    interconnect_root: Path
    unified_project_registry_json: Path
    interconnect_status_json: Path


def default_dekstop_paths(root: Path = None) -> DekstopPaths:
    """Retain the baseline API name; prefer explicit root then BRAINK_WORKSPACE."""
    root = (root or Path(os.environ.get("BRAINK_WORKSPACE", "./workspace"))).resolve()
    inter = root / "K_SYSTEM_INTERCONNECT"
    return DekstopPaths(root, inter, inter / "UNIFIED_PROJECT_REGISTRY.json",
                        inter / "INTERCONNECT_STATUS.json")
