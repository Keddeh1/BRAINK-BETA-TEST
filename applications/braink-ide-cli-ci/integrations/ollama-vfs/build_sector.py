"""Reproducible isolated build of the model-node wheel; no external inference claims."""
import argparse, hashlib, json, shutil, subprocess, sys, tempfile
from pathlib import Path
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args();source=Path(__file__).resolve().parent
output=args.output.resolve();output.mkdir(parents=True,exist_ok=True)
stage=Path(tempfile.mkdtemp(prefix='build-',dir=output))
for path in (source/'native').glob('*.py'):shutil.copy2(path,stage/path.name)
for path in source.glob('*.mjs'):shutil.copy2(path,stage/path.name)
shutil.copy2(source/'packaging/pyproject.toml',stage/'pyproject.toml')
result=subprocess.run([sys.executable,'-m','pip','wheel','--no-deps','--no-build-isolation','--wheel-dir',str(output/'wheels'),str(stage)],capture_output=True,text=True)
(output/'build.log').write_text(result.stdout+result.stderr)
if result.returncode:sys.exit(result.returncode)
for wheel in (output/'wheels').glob('*.whl'):
 print(json.dumps({'wheel':str(wheel),'sha256':hashlib.sha256(wheel.read_bytes()).hexdigest()}))
