import json,ast,hashlib
from pathlib import Path
from braink_node.protocol.catalogue import FunctionVisitor,digest
from braink_node.protocol.instances import InstanceManager
from braink_node.protocol.transport import HubSubscription,JSONTransport
from braink_node.canonical import canonical_bytes
source=Path('/workspace/work/braink-node-repo/applications/keddeh-runtime-workspace')
root=Path('/workspace/braink-setup/application-nodes/keddeh-runtime-workspace');root.mkdir(parents=True,exist_ok=True)
config=json.loads(Path('/workspace/braink-setup/application-nodes/braink-ide-cli-ci/architecture-automation.json').read_text())
path=source/'runtime/topology_sync.py';text=path.read_text();visitor=FunctionVisitor(text,'keddeh_runtime_workspace.topology_sync','runtime/topology_sync.py','core');visitor.visit(ast.parse(text));modules={row['id']:row for row in visitor.functions}
def signed(value):return {**value,'definition_sha256':digest(value)}
family=signed({'schema':'braink.module-family.v1','id':'family://braink-development/keddeh_runtime_workspace.topology_sync','sector':'core','source_path':'runtime/topology_sync.py','source_sha256':hashlib.sha256(text.encode()).hexdigest(),'modules':list(modules)})
variant=signed({'schema':'braink.family-variant.v1','id':'variant://keddeh-runtime-workspace/resident-mirror','sector':'core','families':[family['id']],'family_definition_sha256':{family['id']:family['definition_sha256']},'modules':list(modules),'subscriptions':['VFS_INSTANTIATION','IL_LLM_NETWORK_MESH']})
colony=signed({'schema':'braink.variant-colony.v1','id':'colony://keddeh-runtime-workspace/observation','sector':'core','variants':[variant['id']],'variant_definition_sha256':{variant['id']:variant['definition_sha256']},'instance_template':'braink.instance.v1'})
catalogue=signed({'schema':'braink.deployment-protocol.v1','modules':modules,'families':[family],'variants':[variant],'colonies':[colony]})
manager=InstanceManager(root/'state/instances',HubSubscription(JSONTransport(config['vfs_url'],Path(config['vfs_token_file']).read_text().strip())),JSONTransport(config['mesh_url'],Path(config['mesh_token_file']).read_text().strip()))
instances=[]
for definition,occurrence in [(colony,[colony['id']]),(variant,[colony['id'],variant['id']]),(family,[colony['id'],variant['id'],family['id']])]+[(row,[colony['id'],variant['id'],family['id'],row['id']]) for row in modules.values()]:
 row=manager.instantiate(definition,occurrence);instances.append({'instance':row['instance'],'definition_id':row['definition_id'],'occurrence':row['occurrence'],'state':row['state']})
manifest={'schema':'braink.colony-deployment.v1','catalogue_sha256':catalogue['definition_sha256'],'sectors':['core'],'sector_catalogue_sha256':{'core':catalogue['definition_sha256']},'instances':instances}
(root/'state/instances/deployment.json').write_bytes(canonical_bytes(manifest));(source/'runtime/function-modules.json').write_bytes(canonical_bytes(catalogue));print(json.dumps({'functions':len(modules),'instances':len(instances),'all_readback':all(row['state']=='READBACK' for row in instances)}))
