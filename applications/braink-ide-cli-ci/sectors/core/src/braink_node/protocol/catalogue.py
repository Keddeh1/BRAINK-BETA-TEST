"""Compile source functions into independently addressed module definitions."""
import ast
import hashlib
from pathlib import Path

from braink_node.canonical import canonical_bytes


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def module_identity(module, qualified_name):
    return 'function://braink-development/' + module + '/' + qualified_name


class FunctionVisitor(ast.NodeVisitor):
    def __init__(self, source, module, file_path, sector):
        self.source = source
        self.module = module
        self.file_path = file_path
        self.sector = sector
        self.scope = []
        self.scope_types = []
        self.functions = []

    def visit_ClassDef(self, node):
        self.scope.append(node.name)
        self.scope_types.append('class')
        self.generic_visit(node)
        self.scope.pop()
        self.scope_types.pop()

    def visit_function(self, node):
        qualified = '.'.join(self.scope + [node.name])
        body = ast.get_source_segment(self.source, node)
        context = 'closure' if 'function' in self.scope_types else 'method' if self.scope_types else 'function'
        definition = {
            'schema': 'braink.function-module.v1', 'id': module_identity(self.module, qualified),
            'sector': self.sector, 'family': 'family://braink-development/' + self.module,
            'implementation': {'module': self.module, 'qualified_name': qualified, 'source_path': self.file_path,
                               'source_sha256': hashlib.sha256(self.source.encode()).hexdigest(),
                               'function_sha256': hashlib.sha256(body.encode()).hexdigest(),
                               'line': node.lineno, 'end_line': node.end_lineno},
            'binding': {'kind': context, 'lexical_scope': list(self.scope), 'scope_types': list(self.scope_types),
                        'async': isinstance(node, ast.AsyncFunctionDef),
                        'decorators': [ast.unparse(d) for d in node.decorator_list]},
            'contract': {'arguments': ast.unparse(node.args), 'returns': ast.unparse(node.returns) if node.returns else None,
                         'definition': ast.get_docstring(node) or '',
                         'calls': sorted({ast.unparse(n.func) for n in ast.walk(node) if isinstance(n, ast.Call)})},
            'source_body': body,
        }
        definition['definition_sha256'] = digest(definition)
        self.functions.append(definition)
        self.scope.append(node.name)
        self.scope_types.append('function')
        self.generic_visit(node)
        self.scope.pop()
        self.scope_types.pop()

    visit_FunctionDef = visit_function
    visit_AsyncFunctionDef = visit_function

    def visit_Lambda(self, node):
        name = '.'.join(self.scope + [f'lambda@{node.lineno}:{node.col_offset}'])
        body = ast.get_source_segment(self.source, node)
        definition = {
            'schema': 'braink.function-module.v1', 'id': module_identity(self.module, name),
            'sector': self.sector, 'family': 'family://braink-development/' + self.module,
            'implementation': {'module': self.module, 'qualified_name': name, 'source_path': self.file_path,
                               'source_sha256': hashlib.sha256(self.source.encode()).hexdigest(),
                               'function_sha256': hashlib.sha256(body.encode()).hexdigest(),
                               'line': node.lineno, 'end_line': node.end_lineno, 'column': node.col_offset, 'end_column': node.end_col_offset},
            'binding': {'kind': 'closure', 'lexical_scope': list(self.scope), 'scope_types': list(self.scope_types), 'async': False, 'decorators': []},
            'contract': {'arguments': ast.unparse(node.args), 'returns': None, 'definition': '', 'calls': []},
            'source_body': body,
        }
        definition['definition_sha256'] = digest(definition)
        self.functions.append(definition)
        self.generic_visit(node)


def compile_catalogue(root):
    root = Path(root).resolve(strict=True)
    modules, families = {}, []
    for sector in ('core', 'cli', 'ide', 'ci'):
        base = root / 'sectors' / sector / 'src'
        for path in sorted(base.rglob('*.py')):
            relative = path.relative_to(base)
            components = list(relative.with_suffix('').parts)
            if components[-1] == '__init__':
                components.pop()
            name = '.'.join(components)
            source = path.read_text()
            visitor = FunctionVisitor(source, name, path.relative_to(root).as_posix(), sector)
            visitor.visit(ast.parse(source))
            modules.update({f['id']: f for f in visitor.functions})
            family = {'schema': 'braink.module-family.v1', 'id': 'family://braink-development/' + name,
                      'sector': sector, 'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                      'modules': [f['id'] for f in visitor.functions], 'source_path': path.relative_to(root).as_posix()}
            family['definition_sha256'] = digest(family)
            families.append(family)
    from braink_node.protocol.browser import browser_definitions
    browser_modules, browser_families = browser_definitions(root)
    modules.update(browser_modules)
    families.extend(browser_families)
    variants = []
    for sector in ('core', 'cli', 'ide', 'ci'):
        # Dependencies are explicit composition edges, retaining their own family identities.
        selected = [f for f in families if f['sector'] == sector or sector != 'core' and f['sector'] == 'core']
        variant = {'schema': 'braink.family-variant.v1', 'id': 'variant://braink-development/' + sector,
                   'sector': sector, 'families': [f['id'] for f in selected],
                   'modules': sorted({m for f in selected for m in f['modules']}),
                   'subscriptions': ['VFS_INSTANTIATION', 'IL_LLM_NETWORK_MESH']}
        variant['definition_sha256'] = digest(variant)
        variants.append(variant)
    colonies = []
    for variant in variants:
        colony = {'schema': 'braink.variant-colony.v1', 'id': 'colony://braink-development/' + variant['sector'],
                  'sector': variant['sector'], 'variants': [variant['id']], 'instance_template': 'braink.instance.v1'}
        colony['definition_sha256'] = digest(colony)
        colonies.append(colony)
    catalogue = {'schema': 'braink.deployment-protocol.v1', 'modules': modules, 'families': families,
                 'variants': variants, 'colonies': colonies,
                 'ceremony': ['DECLARE_INSTANCE', 'INSTANTIATE_VFS', 'SUBSCRIBE_VFS', 'SUBSCRIBE_IL_LLM_NETWORK_MESH', 'READBACK']}
    catalogue['definition_sha256'] = digest(catalogue)
    return catalogue
