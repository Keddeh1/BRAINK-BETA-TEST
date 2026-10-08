"""Resolve modules in their original lexical context; closures require actual instances."""
import hashlib
import importlib
import inspect
from pathlib import Path


class FunctionBindings:
    def __init__(self, catalogue):
        self.catalogue = catalogue
        self.contexts = {}

    def bind(self, module_id, context, callable_object):
        definition = self.catalogue['modules'][module_id]
        if not callable(callable_object):
            raise TypeError('Binding is not callable')
        target = getattr(callable_object, '__func__', callable_object)
        while hasattr(target, '__wrapped__'):
            target = target.__wrapped__
        filename = inspect.getsourcefile(target)
        if filename is None or hashlib.sha256(Path(filename).read_bytes()).hexdigest() != definition['implementation']['source_sha256']:
            raise ValueError('Callable source does not match module definition')
        qualified = target.__qualname__.replace('.<locals>', '')
        if target.__name__ == '<lambda>':
            positions = [(a, b, c, d) for a, b, c, d in target.__code__.co_positions()
                         if c is not None and d is not None and d > c]
            candidates = []
            for candidate in self.catalogue['modules'].values():
                implementation = candidate['implementation']
                if implementation.get('column') is None or implementation['source_sha256'] != definition['implementation']['source_sha256']:
                    continue
                if implementation['line'] == target.__code__.co_firstlineno and all(
                    a >= implementation['line'] and b <= implementation['end_line'] and
                    (a != implementation['line'] or c >= implementation['column']) and
                    (b != implementation['end_line'] or d <= implementation['end_column']) for a, b, c, d in positions):
                    candidates.append(candidate['id'])
            if candidates != [module_id]:
                raise ValueError('Lambda lexical identity is ambiguous or differs')
        elif qualified != definition['implementation']['qualified_name']:
            raise ValueError('Callable lexical identity differs')
        key = (module_id, context)
        if key in self.contexts and self.contexts[key] is not callable_object:
            raise ValueError('Context already bound; give the new instance its own context')
        self.contexts[key] = callable_object
        return {'module': module_id, 'context': context, 'state': 'BOUND'}

    def resolve(self, module_id):
        definition = self.catalogue['modules'][module_id]
        if definition['binding']['kind'] != 'function':
            raise ValueError('A method or closure requires its instantiated lexical context')
        implementation = definition['implementation']
        function = getattr(importlib.import_module(implementation['module']), implementation['qualified_name'])
        self.bind(module_id, '__default__', function)
        return function

    def invoke(self, module_id, args=(), kwargs=None, context=None):
        function = self.contexts[(module_id, context)] if context is not None else self.resolve(module_id)
        # Signature binding retains the function's actual argument contract.
        inspect.signature(function).bind(*args, **(kwargs or {}))
        return function(*args, **(kwargs or {}))
