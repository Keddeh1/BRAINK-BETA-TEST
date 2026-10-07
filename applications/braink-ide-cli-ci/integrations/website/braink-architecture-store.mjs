import {architectureTargets} from './braink-architecture.mjs';
const json=value=>Response.json(value,{headers:{'Cache-Control':'private,no-store'}});
export async function architectureStore(db,bucket,value){
 await db.prepare('CREATE TABLE IF NOT EXISTS braink_architecture_evidence(target TEXT PRIMARY KEY,id TEXT,created REAL,document TEXT)').run();
 if(value.op==='architecture-observation'){
  const row=value.evidence;
  if(!row||!architectureTargets.some(([id])=>id===row.target)||! /^[a-f0-9]{32}$/.test(row.id)||!Number.isFinite(row.created))return Response.json({error:'INVALID_EVIDENCE'}, {status:400});
  const bytes=new TextEncoder().encode(value.artifact_body);
  const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');
  const body=JSON.parse(value.artifact_body);
  if(hash!==row.artifact_digest||body.id!==row.id||body.target!==row.target||body.created!==row.created||Object.entries(body).some(([key,item])=>JSON.stringify(row[key])!==JSON.stringify(item)))return Response.json({error:'EVIDENCE_DIGEST_MISMATCH'},{status:409});
  const key='braink-architecture/'+row.target+'/'+row.id+'.json';
  await bucket.put(key,bytes,{httpMetadata:{contentType:'application/json'}});
  await db.prepare('INSERT INTO braink_architecture_evidence VALUES(?,?,?,?) ON CONFLICT(target) DO UPDATE SET id=excluded.id,created=excluded.created,document=excluded.document WHERE excluded.created>=braink_architecture_evidence.created').bind(row.target,row.id,row.created,JSON.stringify(row)).run();
  return json({id:row.id,artifact_digest:hash,stored:true});
 }
 const result=await db.prepare('SELECT target,document FROM braink_architecture_evidence').all();
 return json({schema:'braink.automation-status.v1',targets:architectureTargets.map(([id,title])=>({id,title,evidence:JSON.parse(result.results.find(row=>row.target===id)?.document||'null')}))});
}
