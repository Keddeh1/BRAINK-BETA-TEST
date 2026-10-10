"""Additive native registration; credentials are read from the existing owner configuration."""
import argparse, ast, hashlib, json, sys
from pathlib import Path
from braink_node.protocol.catalogue import FunctionVisitor, digest
from braink_node.protocol.instances import InstanceManager
from braink_node.protocol.binding import FunctionBindings
from braink_node.protocol.transport import HubSubscription, JSONTransport
from braink_node.canonical import canonical_bytes


def signed(document):
    return {**document, 'definition_sha256': digest(document)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--endpoint', default='http://127.0.0.1:11434')
    args = parser.parse_args()
    source = Path(__file__).with_name('ollama_node.py')
    text = source.read_text()
    visitor = FunctionVisitor(text, 'ollama_node', 'native/ollama_node.py', 'core')
    visitor.visit(ast.parse(text))
    modules = {row['id']: row for row in visitor.functions}
    family = signed({'schema':'braink.module-family.v1', 'id':'family://braink-ollama/native',
        'sector':'core', 'source_path':'native/ollama_node.py',
        'source_sha256':hashlib.sha256(text.encode()).hexdigest(), 'modules':list(modules)})
    variants = [signed({'schema':'braink.family-variant.v1', 'id':'variant://braink-ollama/'+name,
        'sector':'core', 'families':[family['id']], 'modules':list(modules),
        'family_definition_sha256':{family['id']:family['definition_sha256']},
        'subscriptions':['VFS_INSTANTIATION','IL_LLM_NETWORK_MESH']}) for name in ['console','ide','cli','ci']]
    colony = signed({'schema':'braink.variant-colony.v1', 'id':'colony://braink-ollama/development',
        'sector':'core', 'variants':[row['id'] for row in variants],
        'variant_definition_sha256':{row['id']:row['definition_sha256'] for row in variants},
        'instance_template':'braink.instance.v1'})
    catalogue = signed({'schema':'braink.deployment-protocol.v1','modules':modules,
        'families':[family],'variants':variants,'colonies':[colony]})
    config = json.loads(args.config.read_text())
    hub = HubSubscription(JSONTransport(config['vfs_url'],Path(config['vfs_token_file']).read_text().strip()))
    mesh = JSONTransport(config['mesh_url'],Path(config['mesh_token_file']).read_text().strip())
    manager = InstanceManager(args.root/'instances',hub,mesh)
    instances = [manager.instantiate(colony,[colony['id']])]
    for variant in variants:
        ancestry = [colony['id'],variant['id']]
        instances.append(manager.instantiate(variant,ancestry))
        instances.append(manager.instantiate(family,ancestry+[family['id']]))
        for definition in modules.values():
            instances.append(manager.instantiate(definition,ancestry+[family['id'],definition['id']]))
    sys.path.insert(0,str(source.parent))
    bindings = FunctionBindings(catalogue)
    observations = []
    for row in instances:
        if not row['definition_id'].endswith('/execute'): continue
        own_vfs = str(args.root/'instances'/row['instance']/'vfs')
        import ollama_node
        ollama_node.attach(own_vfs,row['instance'],args.endpoint,
            'volume://keddeh/braink/root','volume://keddeh/braink/models')
        child = next(item for item in instances if item['definition_id'] == family['id'] and item['occurrence'][1] == row['occurrence'][1])
        ollama_node.mount_model_volume(own_vfs,args.root/'instances'/child['instance']/'vfs',
            'volume://keddeh/braink/models',row['instance'])
        ollama_node.resolve_model_volume(own_vfs)
        result = manager.invoke(row['instance'],bindings,[own_vfs,'inventory'])
        observations.append({'instance':row['instance'],'variant':row['occurrence'][1],**result})
    sender = next(row for row in instances if row['definition_id']=='variant://braink-ollama/console')
    recipient = next(row for row in instances if row['definition_id']=='variant://braink-ollama/ci')
    anchor = {'type':'RELATIONAL_ANCHOR','source':sender['instance'],'definition':sender['definition_id'],
        'relation':'model-node-variant-in-colony','uncertainty':[],'contradiction':[], 'next_route':recipient['instance']}
    exchanged = mesh.request('/exchange',{'sender':sender['instance'],'recipient':recipient['instance'],
        'row':anchor,'message_id':digest(anchor)})
    inbox = mesh.request('/inbox',{'instance':recipient['instance'],'after':exchanged['sequence']-1})
    if not any(row['digest']==exchanged['digest'] for row in inbox): raise RuntimeError('Mesh exchange readback differs')
    report = {'schema':'keddeh.ollama.native-attachment.v1','source_sha256':hashlib.sha256(text.encode()).hexdigest(),
        'instances':len(instances),'distinct_vfs_roots':len({row['steps']['INSTANTIATE_VFS']['root'] for row in instances}),
        'all_ceremonies_readback':all(row['state']=='READBACK' for row in instances),
        'variant_inventory_observations':observations,'mesh_exchange':exchanged,
        'nested_vfs_reference_resolution_verified':True,
        'model_weights_materialisation_verified':False, 'ollama_inference_verified':False,'scope':'Current connected execution workspace; no production or Android inference claim'}
    args.root.mkdir(parents=True,exist_ok=True)
    (args.root/'deployment.json').write_bytes(canonical_bytes({'catalogue':catalogue,'instances':instances}))
    (args.root/'attachment-evidence.json').write_bytes(canonical_bytes(report))
    print(json.dumps({'instances':report['instances'],'distinct_vfs_roots':report['distinct_vfs_roots'],
        'all_ceremonies_readback':report['all_ceremonies_readback'], 'inventory_states':[row['state'] for row in observations],
        'mesh_exchange_observer_verified':exchanged['observer']['verified']}))

if __name__ == '__main__':
    main()
