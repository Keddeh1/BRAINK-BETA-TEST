import json
from braink_node.canonical import canonical_bytes
from braink_node.storage import atomic_write
from braink_node.protocol.catalogue import compile_catalogue


def run(context):
    current = compile_catalogue(context.desired_source) if hasattr(context, 'desired_source') else context.catalogue()
    path = context.root / 'catalogue-baseline.json'
    prior = json.loads(path.read_text()) if path.exists() else {'modules': {}}
    changed = sorted(key for key, row in current['modules'].items() if prior['modules'].get(key, {}).get('definition_sha256') != row['definition_sha256'])
    removed = sorted(prior['modules'].keys() - current['modules'].keys())
    families = sorted({current['modules'][key]['family'] for key in changed} | {prior['modules'][key]['family'] for key in removed})
    variants = sorted({row['id'] for row in current['variants'] + prior.get('variants', []) if set(families).intersection(row['families'])})
    colonies = [row['id'] for row in current['colonies'] if set(variants).intersection(row['variants'])]
    sectors = [row['sector'] for row in current['colonies'] if row['id'] in colonies]
    atomic_write(path, canonical_bytes(current))
    return {'state': 'CHANGE_DERIVED' if changed or removed else 'UNCHANGED', 'changed_modules': changed, 'removed_modules': removed,
            'affected_families': families, 'affected_variants': variants, 'affected_colonies': colonies, 'affected_sectors': sectors,
            'catalogue_sha256': current['definition_sha256']}
