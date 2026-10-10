"""Build both specified HCI slot paths; no physical media or boot secrets touched."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile


def build(output):
    source = Path(__file__).parent
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    entries = {}
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for slot in ('a', 'b'):
            for name in ('keddeh_hci_core.py', 'kex_diagnostics_panel.py'):
                path = f'mnt/KEX_RUNTIME/slot_{slot}/bin/{name}'
                content = (source / name).read_bytes()
                archive.writestr(path, content)
                entries[path] = hashlib.sha256(content).hexdigest()
        archive.writestr('physical-layout.json', (source / 'physical-layout.json').read_bytes())
    with zipfile.ZipFile(output) as archive:
        for name, expected in entries.items():
            if hashlib.sha256(archive.read(name)).hexdigest() != expected:
                raise RuntimeError('Packaged source readback differs')
    return {'artifact': output.name, 'sha256': hashlib.sha256(output.read_bytes()).hexdigest(),
            'slot_files': entries, 'packaged_readback_verified': True,
            'boot_secrets_included': False, 'physical_media_written': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.output), indent=2))
