"""Operational entrypoint for the native model colony, preserving per-variant execution custody."""
import argparse, json, sys
from pathlib import Path
from braink_node.protocol.instances import InstanceManager
from braink_node.protocol.binding import FunctionBindings
from braink_node.protocol.transport import HubSubscription, JSONTransport


def invoke_variant(root, config_path, variant, operation, payload=None, request_id=None):
    manifest = json.loads((Path(root)/'deployment.json').read_text())
    target = '/model_store/' + ('attach_model_store' if operation=='attach-store' else 'verify_model_store') if operation in ('attach-store','verify-store') else '/ollama_node/execute'
    row = next(row for row in manifest['instances'] if row['definition_id'].endswith(target)
        and row['occurrence'][1] == 'variant://braink-ollama/' + variant)
    config = json.loads(Path(config_path).read_text())
    manager = InstanceManager(Path(root)/'instances',
        HubSubscription(JSONTransport(config['vfs_url'],Path(config['vfs_token_file']).read_text().strip())),
        JSONTransport(config['mesh_url'],Path(config['mesh_token_file']).read_text().strip()))
    bindings = FunctionBindings(manifest['catalogue'])
    if operation in ('attach-store','verify-store'):
        vault = next(item for item in manifest['instances'] if item['definition_id']=='family://braink-ollama/model-vault')
        vault_root=str(Path(root)/'instances'/vault['instance']/'vfs')
        if operation=='attach-store':
            arguments=[vault_root,payload['models_root'],payload['manifest_path'],payload['model'],vault['instance']]
        else:
            arguments=[vault_root,payload['model']]
        return {'state':'RETURNED','result':manager.invoke(row['instance'],bindings,arguments)}
    return manager.invoke(row['instance'],bindings,
        [str(Path(root)/'instances'/row['instance']/'vfs'),operation,payload],
        {'request_id':request_id})



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--variant',choices=['console','ide','cli','ci'],default='cli')
    parser.add_argument('--request-id')
    parser.add_argument('operation',choices=['inventory','show','pull','chat','attach-store','verify-store'])
    parser.add_argument('--payload',type=Path,help='JSON request file; chat context is preserved')
    args=parser.parse_args()
    payload=json.loads(args.payload.read_text()) if args.payload else None
    result=invoke_variant(args.root,args.config,args.variant,args.operation,payload,args.request_id)
    print(json.dumps(result))
    return 0 if result['state']=='RETURNED' else 1

if __name__=='__main__':sys.exit(main())
