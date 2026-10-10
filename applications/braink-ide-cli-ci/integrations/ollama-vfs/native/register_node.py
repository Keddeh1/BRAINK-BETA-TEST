"""Additive native registration; credentials are read from the existing owner configuration."""
import argparse, ast, hashlib, json, sys
from pathlib import Path
from braink_node.protocol.catalogue import FunctionVisitor, digest
from braink_node.protocol.instances import InstanceManager
from braink_node.protocol.binding import FunctionBindings
from braink_node.protocol.transport import HubSubscription, JSONTransport
from braink_node.canonical import canonical_bytes
from braink_node.storage import atomic_write


def signed(document):
    return {**document, 'definition_sha256': digest(document)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--endpoint', default='http://127.0.0.1:11434')
    args = parser.parse_args()
    source = Path(__file__).with_name('ollama_node.py')
    modules = {}
    families = []
    for path in sorted(source.parent.glob('*.py')):
        if path.name.startswith('test_'): continue
        text = path.read_text()
        visitor = FunctionVisitor(text,path.stem,'native/'+path.name,'core')
        visitor.visit(ast.parse(text))
        rows = {row['id']:row for row in visitor.functions}
        modules.update(rows)
        families.append(signed({'schema':'braink.module-family.v1',
            'id':'family://braink-ollama/'+path.stem,'sector':'core',
            'source_path':'native/'+path.name,'source_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'modules':list(rows)}))
    vault_definition = signed({'schema':'braink.module-family.v1','id':'family://braink-ollama/model-vault',
        'sector':'core','modules':[],'role':'MODEL_BACKING_CUSTODY'})
    variants = [signed({'schema':'braink.family-variant.v1','id':'variant://braink-ollama/'+name,
        'sector':'core','families':[family['id'] for family in families],'modules':list(modules),
        'family_definition_sha256':{family['id']:family['definition_sha256'] for family in families},
        'subscriptions':['VFS_INSTANTIATION','IL_LLM_NETWORK_MESH']}) for name in ['console','ide','cli','ci']]
    colony = signed({'schema':'braink.variant-colony.v1', 'id':'colony://braink-ollama/development',
        'sector':'core', 'variants':[row['id'] for row in variants],
        'variant_definition_sha256':{row['id']:row['definition_sha256'] for row in variants},
        'instance_template':'braink.instance.v1','shared_families':[vault_definition['id']],
        'shared_family_definition_sha256':{vault_definition['id']:vault_definition['definition_sha256']}})
    catalogue = signed({'schema':'braink.deployment-protocol.v1','modules':modules,
        'families':families+[vault_definition],'variants':variants,'colonies':[colony]})
    config = json.loads(args.config.read_text())
    hub = HubSubscription(JSONTransport(config['vfs_url'],Path(config['vfs_token_file']).read_text().strip()))
    mesh = JSONTransport(config['mesh_url'],Path(config['mesh_token_file']).read_text().strip())
    manager = InstanceManager(args.root/'instances',hub,mesh)
    instances = [manager.instantiate(colony,[colony['id']])]
    for variant in variants:
        ancestry = [colony['id'],variant['id']]
        instances.append(manager.instantiate(variant,ancestry))
        for family in families:
            instances.append(manager.instantiate(family,ancestry+[family['id']]))
            for module_id in family['modules']:
                definition=modules[module_id]
                instances.append(manager.instantiate(definition,ancestry+[family['id'],definition['id']]))
    vault = manager.instantiate(vault_definition,[colony['id'],vault_definition['id']])
    instances.append(vault)
    sys.path.insert(0,str(source.parent))
    bindings = FunctionBindings(catalogue)
    observations = []
    for row in instances:
        if not row['definition_id'].endswith('/execute'): continue
        own_vfs = str(args.root/'instances'/row['instance']/'vfs')
        import ollama_node
        ollama_node.attach(own_vfs,row['instance'],args.endpoint,
            'volume://keddeh/braink/root','volume://keddeh/braink/models')
        ollama_node.mount_model_volume(own_vfs,args.root/'instances'/vault['instance']/'vfs',
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
    report = {'schema':'keddeh.ollama.native-attachment.v1','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'source_files':{family['source_path']:family['source_sha256'] for family in families},
        'modules':len(modules),'families':len(families),'instances':len(instances),'distinct_vfs_roots':len({row['steps']['INSTANTIATE_VFS']['root'] for row in instances}),
        'all_ceremonies_readback':all(row['state']=='READBACK' for row in instances),
        'variant_inventory_observations':observations,'mesh_exchange':exchanged,
        'nested_vfs_reference_resolution_verified':True,
        'model_vault_instance':vault['instance'], 'model_weights_materialisation_verified':False, 'ollama_inference_verified':False,'scope':'Current connected execution workspace; no production or Android inference claim'}
    args.root.mkdir(parents=True,exist_ok=True)
    deployment = {'catalogue':catalogue,'instances':instances}
    colony_vfs = args.root/'instances'/instances[0]['instance']/'vfs'
    ollama_node.retain(colony_vfs,'/deployment/catalogue.json',deployment,instances[0]['instance'])
    ollama_node.retain(colony_vfs,'/deployment/attachment-evidence.json',report,instances[0]['instance'])
    atomic_write(args.root/'deployment.json',canonical_bytes(deployment))
    atomic_write(args.root/'attachment-evidence.json',canonical_bytes(report))
    print(json.dumps({'instances':report['instances'],'distinct_vfs_roots':report['distinct_vfs_roots'],
        'all_ceremonies_readback':report['all_ceremonies_readback'], 'inventory_states':[row['state'] for row in observations],
        'mesh_exchange_observer_verified':exchanged['observer']['verified']}))

if __name__ == '__main__':
    main()
