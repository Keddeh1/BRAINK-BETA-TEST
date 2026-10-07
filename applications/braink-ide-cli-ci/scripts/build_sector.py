"""Build each sector from a clean, sector-specific source staging tree."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def build(root, sector, run, artifacts):
    staging = run / "clean-builds" / sector
    if staging.exists():
        raise ValueError(f"Clean build staging already exists for {sector}")
    staging.mkdir(parents=True)
    source = root / "sectors" / sector
    shutil.copy2(source / "pyproject.toml", staging / "pyproject.toml")
    shutil.copytree(source / "src", staging / "src", ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.egg-info"))
    out = artifacts / sector
    out.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation",
                    "--wheel-dir", str(out), str(staging)], check=True)
    wheels = list(out.glob("*.whl"))
    if len(wheels) != 1:
        raise ValueError(f"Expected exactly one sector artifact for {sector}")
    return {"sector": sector, "wheel": str(wheels[0].relative_to(artifacts)),
            "sha256": hashlib.sha256(wheels[0].read_bytes()).hexdigest(),
            "dependencies": [] if sector == "core" else ["braink-node-core==0.1.0"]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sector", choices=("core", "cli", "ide", "ci", "all"), required=True)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    sectors = ["core", "cli", "ide", "ci"] if args.sector == "all" else ["core"] if args.sector == "core" else ["core", args.sector]
    manifest = {"schema": "braink.sector-build.v1", "requested_sector": args.sector,
                "builds": [build(root, sector, args.run, args.artifacts) for sector in sectors]}
    (args.artifacts / "sector-builds.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
