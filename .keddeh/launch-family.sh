#!/usr/bin/env bash
set -euo pipefail
family_directory="$(cd "$(dirname "$0")" && pwd)"
engine_root=${KEDDEH_ENGINE_ROOT:-/workspace/KEDDEH-SOVEREIGN-NAMESPACE-RUNTIME}
"$engine_root/.venv/bin/python" "$family_directory/verify-engine.py" "$engine_root"
"$engine_root/.venv/bin/python" "$engine_root/scripts/launch_resident_controller.py" --manifest "$family_directory/family.json"
exec "$engine_root/.venv/bin/python" "$engine_root/scripts/bootstrap_owner_environment.py" --root "$("$engine_root/.venv/bin/python" -c 'import json,sys; print(json.load(open(sys.argv[1]))["runtime_root"])' "$family_directory/family.json")"
