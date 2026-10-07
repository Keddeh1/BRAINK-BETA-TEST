"""Compile browser functions using the owner's Node runtime's actual JavaScript parser."""
import hashlib
from html.parser import HTMLParser
import json
import subprocess

from braink_node.protocol.catalogue import digest, module_identity


class ScriptSources(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.scripts = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == 'script':
            self.current = []

    def handle_data(self, data):
        if self.current is not None:
            self.current.append(data)

    def handle_endtag(self, tag):
        if tag == 'script' and self.current is not None:
            self.scripts.append(''.join(self.current))
            self.current = None


def browser_definitions(root):
    modules, families = {}, []
    for path in sorted((root / 'sectors/ide/src').rglob('*.html')):
        source = path.read_bytes().decode('utf-8')
        parser = ScriptSources()
        parser.feed(source)
        name = 'braink_ide.browser.' + path.stem
        family = {'schema': 'braink.module-family.v1', 'id': 'family://braink-development/' + name,
                  'sector': 'ide', 'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
                  'source_path': path.relative_to(root).as_posix(), 'modules': [], 'runtime': 'browser-javascript'}
        for index, script in enumerate(parser.scripts):
            command = ['node', '--expose-internals', '-e',
                       "const a=require('internal/deps/acorn/acorn/dist/acorn');let s='';process.stdin.on('data',c=>s+=c);process.stdin.on('end',()=>process.stdout.write(JSON.stringify(a.parse(s,{ecmaVersion:'latest',locations:true,sourceType:'script'}))));"]
            result = subprocess.run(command, input=script, text=True, capture_output=True, check=True)
            tree = json.loads(result.stdout)

            def visit(node, scope=()):
                if not isinstance(node, dict):
                    return
                function = node.get('type') in {'FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'}
                if function:
                    label = (node.get('id') or {}).get('name') or f"function@{node['loc']['start']['line']}:{node['loc']['start']['column']}"
                    qualified = '.'.join((*scope, label))
                    body = script[node['start']:node['end']]
                    definition = {'schema': 'braink.function-module.v1', 'id': module_identity(name, f'script{index}.' + qualified),
                                  'sector': 'ide', 'family': family['id'],
                                  'implementation': {'module': name, 'qualified_name': f'script{index}.' + qualified,
                                                     'source_path': family['source_path'], 'source_sha256': family['source_sha256'],
                                                     'function_sha256': hashlib.sha256(body.encode()).hexdigest(),
                                                     'line': node['loc']['start']['line'], 'end_line': node['loc']['end']['line']},
                                  'binding': {'kind': 'browser-function', 'runtime': 'browser-javascript',
                                              'lexical_scope': list(scope), 'async': node.get('async', False)},
                                  'contract': {'arguments': [script[p['start']:p['end']] for p in node['params']]},
                                  'source_body': body}
                    definition['definition_sha256'] = digest(definition)
                    modules[definition['id']] = definition
                    family['modules'].append(definition['id'])
                    scope = (*scope, label)
                for value in node.values():
                    for child in value if isinstance(value, list) else [value]:
                        if isinstance(child, dict) and 'type' in child:
                            visit(child, scope)
            visit(tree)
        family['definition_sha256'] = digest(family)
        families.append(family)
    return modules, families
