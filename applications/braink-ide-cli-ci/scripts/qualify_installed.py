"""Exercise the produced wheel in a fresh environment owned by this CI run."""
import json
import os
from pathlib import Path
import subprocess
import sys
import venv

artifacts = Path(sys.argv[1])
run = Path(sys.argv[2])
sector = sys.argv[3] if len(sys.argv) > 3 else "all"
wheels = list(artifacts.glob("*/*.whl"))
if not wheels:
    raise SystemExit("Expected independently built sector wheels")
venv.create(run / "qualification-venv", with_pip=True)
python = run / "qualification-venv/bin/python"
environment = os.environ.copy()
environment.pop("PYTHONPATH", None)
subprocess.run([str(python), "-m", "pip", "install", "--no-deps"] + [str(wheel) for wheel in wheels], check=True, env=environment)
sectors = ["core", "cli", "ide", "ci"] if sector == "all" else [sector]
for target in sectors:
    subprocess.run([str(python), "-m", "unittest", "discover", "-s", "tests", "-p", f"test_{target}.py", "-v"], check=True, env=environment)
if sector in {"all", "core"}:
    subprocess.run([str(python), "-m", "unittest", "discover", "-s", "tests", "-p", "test_protocol.py", "-v"], check=True, env=environment)
common = [str(python), "-m", "braink_cli.cli", "--workspace", str(run / "smoke-workspace"),
          "--state-dir", str(run / "smoke-state")]
if sector in {"all", "cli"}:
    for command in (["init"], ["check", "--fail-on", "warn"], ["verify-ledger"]):
        subprocess.run(common + command, check=True, env=environment)
print(json.dumps({"installed_wheels": [wheel.name for wheel in wheels], "sector": sector, "status": "passed"}))
