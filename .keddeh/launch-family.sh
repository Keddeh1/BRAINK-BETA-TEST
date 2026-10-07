#!/usr/bin/env bash
set -euo pipefail
family_directory="$(cd "$(dirname "$0")" && pwd)"
engine_root=${KEDDEH_ENGINE_ROOT:-/workspace/KEDDEH-SOVEREIGN-NAMESPACE-RUNTIME}
exec "$engine_root/.venv/bin/python" "$engine_root/scripts/deploy_family.py" --manifest "$family_directory/family.json"
