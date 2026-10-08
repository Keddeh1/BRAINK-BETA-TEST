"""Package addressable functions, source families, variants and colonies without flattening them."""
import json
from pathlib import Path
import shutil
import sys

from braink_node.canonical import canonical_bytes
from braink_node.protocol.catalogue import compile_catalogue, digest


def package(source, output, artifacts=None):
    source, output = Path(source).resolve(), Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    catalogue = compile_catalogue(source)
    (output / 'catalogue.json').write_bytes(canonical_bytes(catalogue))
    for module in catalogue['modules'].values():
        directory = output / 'modules' / digest(module['id'])
        directory.mkdir(parents=True)
        (directory / 'module.json').write_bytes(canonical_bytes(module))
        (directory / ('function.js' if module['binding'].get('runtime') == 'browser-javascript' else 'function.py')).write_text(module['source_body'] + '\n')
    for family in catalogue['families']:
        directory = output / 'families' / digest(family['id'])
        directory.mkdir(parents=True)
        (directory / 'family.json').write_bytes(canonical_bytes(family))
        # Preserve the compilation unit for imports, decorators, receivers and closures.
        shutil.copy2(source / family['source_path'], directory / ('implementation' + Path(family['source_path']).suffix))
    for category in ('variants', 'colonies'):
        for definition in catalogue[category]:
            directory = output / category / digest(definition['id'])
            directory.mkdir(parents=True)
            (directory / 'definition.json').write_bytes(canonical_bytes(definition))
    if artifacts is not None:
        artifacts = Path(artifacts)
        import hashlib
        builds = json.loads((artifacts / 'sector-builds.json').read_text())['builds']
        for colony in catalogue['colonies']:
            directory = output / 'colonies' / digest(colony['id']) / 'artifacts'
            relevant = [row for row in builds if row['sector'] in {'core', colony['sector']}]
            directory.mkdir()
            for row in relevant:
                wheel = artifacts / row['wheel']
                if hashlib.sha256(wheel.read_bytes()).hexdigest() != row['sha256']:
                    raise ValueError('Sector wheel differs from build receipt')
                shutil.copy2(wheel, directory / wheel.name)
            (directory.parent / 'build-references.json').write_bytes(canonical_bytes(relevant))
    # Consider all supplied baselines, tests and delivery functions explicitly, with lineage.
    from braink_node.protocol.catalogue import FunctionVisitor
    import ast
    inventory = []
    for folder, role in [('baselines', 'source-lineage'), ('tests', 'qualification'), ('scripts', 'delivery')]:
        for path in sorted((source / folder).rglob('*.py')):
            text = path.read_text()
            visitor = FunctionVisitor(text, path.relative_to(source).with_suffix('').as_posix(), path.relative_to(source).as_posix(), role)
            visitor.visit(ast.parse(text))
            inventory.extend(visitor.functions)
    (output / 'supporting-function-inventory.json').write_bytes(canonical_bytes(inventory))
    return {'catalogue_sha256': catalogue['definition_sha256'], 'modules': len(catalogue['modules']),
            'families': len(catalogue['families']), 'variants': len(catalogue['variants']),
            'colonies': len(catalogue['colonies']), 'supporting_functions': len(inventory)}


if __name__ == '__main__':
    print(json.dumps(package(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None), indent=2))
