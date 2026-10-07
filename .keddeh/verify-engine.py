#!/usr/bin/env python3
"""Reject unqualified launcher code while allowing documentation-only revisions."""
from pathlib import Path
import hashlib,json,sys
family=Path(__file__).resolve().parent
engine=Path(sys.argv[1]).resolve()
manifest=json.loads((family/'EXECUTABLE_MANIFEST.json').read_text())
for name,digest in manifest['files'].items():
    path=engine/name
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        raise SystemExit('Unqualified engine source: '+name+'; retain state and qualify the new executable before promotion')
for path in (engine/'src/keddeh_namespace').rglob('*'):
    if path.suffix in ('.py','.js','.mjs') and path.relative_to(engine).as_posix() not in manifest['files']:
        raise SystemExit('Unadmitted engine module: '+path.name)
wheel=family.parent/'packages/owner-family'/manifest['wheel']['name']
if hashlib.sha256(wheel.read_bytes()).hexdigest()!=manifest['wheel']['sha256']:
    raise SystemExit('Distributed wheel does not match the qualified artifact')
