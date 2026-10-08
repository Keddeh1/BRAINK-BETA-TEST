const json=(value,status=200)=>Response.json(value,{status,headers:{'Cache-Control':'private,no-store'}});
const sha=async value=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value))),x=>x.toString(16).padStart(2,'0')).join('');
export async function topologyStore(db,bucket,value){
 if(!db||!bucket)return json({error:'STORAGE_UNAVAILABLE'},503);
 await db.prepare('CREATE TABLE IF NOT EXISTS workspace_topology_head(id TEXT PRIMARY KEY,observed_at REAL,digest TEXT,object_key TEXT)').run();
 if(value.op==='topology-observation'){
  if(typeof value.document!=='string'||await sha(value.document)!==value.digest)return json({error:'TOPOLOGY_DIGEST_MISMATCH'},409);
  let document;try{document=JSON.parse(value.document)}catch{return json({error:'INVALID_TOPOLOGY_DOCUMENT'},400)}
  if(document.schema!=='keddeh.runtime-topology.v1'||!Number.isFinite(document.observed_at)||!Array.isArray(document.nodes)||!Array.isArray(document.instances))return json({error:'INVALID_TOPOLOGY_DOCUMENT'},400);
  const nodes=new Map(document.nodes.map(node=>[node.id,node]));
  if(nodes.size!==document.nodes.length||document.nodes.some(node=>typeof node.id!=='string'||!['colony','variant','family','function'].includes(node.kind))||new Set(document.instances.map(row=>row.id)).size!==document.instances.length||document.instances.some(row=>typeof row.id!=='string'||!Array.isArray(row.occurrence)||!row.occurrence.length||row.occurrence.some(id=>!nodes.has(id))||row.occurrence.at(-1)!==row.definition_id))return json({error:'INVALID_TOPOLOGY_RELATION'},400);
  const key='workspace-topology/'+value.digest+'.json';await bucket.put(key,value.document,{httpMetadata:{contentType:'application/json'}});
  const read=await bucket.get(key);if(!read||await sha(await read.text())!==value.digest)return json({error:'TOPOLOGY_READBACK_MISMATCH'},500);
  await db.prepare('INSERT INTO workspace_topology_head VALUES(?,?,?,?) ON CONFLICT(id) DO UPDATE SET observed_at=excluded.observed_at,digest=excluded.digest,object_key=excluded.object_key WHERE excluded.observed_at>workspace_topology_head.observed_at').bind('resident',document.observed_at,value.digest,key).run();
  const head=await db.prepare('SELECT digest FROM workspace_topology_head WHERE id=?').bind('resident').first();
  return json({stored:true,current:head.digest===value.digest,digest:value.digest,instances:document.instances.length,nodes:document.nodes.length});
 }
 const head=await db.prepare('SELECT observed_at,digest,object_key FROM workspace_topology_head WHERE id=?').bind('resident').first();
 if(!head)return json({schema:'keddeh.runtime-topology.v1',observed_at:null,nodes:[],instances:[],source:null});
 const object=await bucket.get(head.object_key);if(!object)return json({error:'TOPOLOGY_OBJECT_MISSING'},409);
 const body=await object.text();if(await sha(body)!==head.digest)return json({error:'TOPOLOGY_CONTENT_MISMATCH'},409);
 return json({...JSON.parse(body),transport_digest:head.digest});
}
