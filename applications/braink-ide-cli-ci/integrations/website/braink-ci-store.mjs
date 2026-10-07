// BRAINK development-sector control plane. Existing owner auth is applied by routes.
const json=(body,status=200)=>Response.json(body,{status,headers:{'Cache-Control':'private,no-store'}});
const sectors=new Set(['core','cli','ide','ci','all']);
const idPattern=/^[a-f0-9]{32}$/;
export async function ensureCI(db){
 await db.prepare(`CREATE TABLE IF NOT EXISTS braink_sector_jobs (
 id TEXT PRIMARY KEY,sector TEXT NOT NULL,status TEXT NOT NULL,created TEXT NOT NULL,
 updated TEXT NOT NULL,worker_id TEXT,lease_token TEXT,detail TEXT NOT NULL
 )`).run();
 await db.prepare(`CREATE TABLE IF NOT EXISTS braink_sector_events (
 id TEXT PRIMARY KEY,job_id TEXT,event_type TEXT NOT NULL,created TEXT NOT NULL,detail TEXT NOT NULL
 )`).run();
}
async function event(db,job,type,detail){await db.prepare('INSERT INTO braink_sector_events VALUES(?,?,?,?,?)').bind(crypto.randomUUID(),job,type,new Date().toISOString(),JSON.stringify(detail)).run()}
async function body(request){const raw=await request.text();if(raw.length>32*1024*1024)throw Error('REQUEST_TOO_LARGE');const value=JSON.parse(raw);if(!value||typeof value!=='object'||Array.isArray(value))throw Error('INVALID_REQUEST');return value}
async function sha256(value){const bytes=typeof value==='string'?new TextEncoder().encode(value):value;return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('')}
export async function ownerCI(request,db,bucket){
 if(!db)return json({error:'STORAGE_UNAVAILABLE'},503);
 try{await ensureCI(db);
  if(request.method==='GET'){
   const url=new URL(request.url),jobId=url.searchParams.get('job'),artifact=url.searchParams.get('artifact');
   if(jobId&&artifact){
    if(!idPattern.test(jobId)||!bucket)return json({error:'ARTIFACT_UNAVAILABLE'},404);
    const row=await db.prepare('SELECT detail FROM braink_sector_jobs WHERE id=?').bind(jobId).first();
    const registered=row?JSON.parse(row.detail).artifacts?.find(x=>x.path===artifact):null;
    if(!registered)return json({error:'ARTIFACT_NOT_REGISTERED'},404);
    const object=await bucket.get('braink-development/'+jobId+'/'+registered.path);
    if(!object)return json({error:'ARTIFACT_NOT_FOUND'},404);
    return new Response(object.body,{headers:{'Content-Type':'application/octet-stream','Content-Disposition':'attachment; filename="'+artifact.split('/').pop()+'"','X-BRAINK-Artifact-SHA256':registered.sha256}});
   }
   const rows=await db.prepare('SELECT id,sector,status,created,updated,worker_id,detail FROM braink_sector_jobs ORDER BY created DESC LIMIT 100').all();
   const events=await db.prepare('SELECT job_id,event_type,created,detail FROM braink_sector_events ORDER BY created DESC LIMIT 100').all();
   return json({node:'braink-development-sector',jobs:(rows.results||[]).map(row=>({...row,detail:JSON.parse(row.detail)})),events:events.results||[]});
  }
  if(request.method!=='POST')return json({error:'METHOD_NOT_ALLOWED'},405);
  const value=await body(request);
  if(value.op!=='submit'||!sectors.has(value.sector)||!idPattern.test(value.id||''))return json({error:'INVALID_SECTOR_SUBMISSION'},400);
  const old=await db.prepare('SELECT id,sector,status FROM braink_sector_jobs WHERE id=?').bind(value.id).first();
  if(old)return old.sector===value.sector?json({job:old},200):json({error:'JOB_ID_CONFLICT'},409);
  const now=new Date().toISOString();
  const operation=value.operation||'qualify';
  if(typeof operation!=='string'||!['qualify','file-list','file-read','file-save','cli','architecture'].includes(operation)||!value.parameters||typeof value.parameters!=='object')return json({error:'INVALID_OPERATION'},400);
  const detail={request:{operation,parameters:value.parameters}};
  await db.prepare('INSERT INTO braink_sector_jobs VALUES(?,?,?,?,?,?,?,?)').bind(value.id,value.sector,'queued',now,now,null,null,JSON.stringify(detail)).run();
  await event(db,value.id,'queued',{sector:value.sector,operation});
  return json({job:{id:value.id,sector:value.sector,status:'queued'}},202);
 }catch(error){return json({error:error.message||'CI_STORE_ERROR'},500)}
}
export async function workerCI(request,db,bucket){
 if(!db)return json({error:'STORAGE_UNAVAILABLE'},503);
 try{await ensureCI(db);const value=await body(request);const now=new Date().toISOString();
  if(value.op==='claim'){
   if(typeof value.worker_id!=='string'||!value.worker_id||value.worker_id.length>100)return json({error:'INVALID_WORKER'},400);
   const active=await db.prepare("SELECT id,sector,detail,lease_token FROM braink_sector_jobs WHERE status='running' AND worker_id=? ORDER BY created LIMIT 1").bind(value.worker_id).first();
   if(active)return json({job:{id:active.id,sector:active.sector,...JSON.parse(active.detail).request,lease_token:active.lease_token}});
   const job=await db.prepare("SELECT id,sector,detail FROM braink_sector_jobs WHERE status='queued' ORDER BY created LIMIT 1").first();
   if(!job)return json({job:null});
   const lease=crypto.randomUUID();
   const result=await db.prepare("UPDATE braink_sector_jobs SET status='running',worker_id=?,lease_token=?,updated=? WHERE id=? AND status='queued'").bind(value.worker_id,lease,now,job.id).run();
   if(result.meta?.changes!==1)return json({job:null});
   await event(db,job.id,'claimed',{worker_id:value.worker_id});
   return json({job:{id:job.id,sector:job.sector,...JSON.parse(job.detail).request,lease_token:lease}});
  }
  if(!idPattern.test(value.id||'')||typeof value.lease_token!=='string')return json({error:'INVALID_JOB_RECEIPT'},400);
  const job=await db.prepare('SELECT status,lease_token,detail FROM braink_sector_jobs WHERE id=?').bind(value.id).first();
  if(!job||job.lease_token!==value.lease_token)return json({error:'LEASE_MISMATCH'},409);
  if(value.op==='heartbeat'){
   await db.prepare('UPDATE braink_sector_jobs SET updated=? WHERE id=?').bind(now,value.id).run();
   return json({ok:true});
  }
  if(value.op!=='result'||!['passed','failed','error'].includes(value.report?.status)||!Array.isArray(value.report?.stages))return json({error:'INVALID_RESULT'},400);
  if(value.receipt_body&&await sha256(value.receipt_body)!==value.report.receipt_sha256)return json({error:'RECEIPT_DIGEST_MISMATCH'},400);
  for(const artifact of value.artifact_blobs||[]){
   const registered=value.report.artifacts?.find(x=>x.path===artifact.path);
   if(!bucket||!registered||typeof artifact.base64!=='string')return json({error:'ARTIFACT_STORE_UNAVAILABLE'},503);
   const bytes=Uint8Array.from(atob(artifact.base64),c=>c.charCodeAt(0));
   if(bytes.length!==registered.size||await sha256(bytes)!==registered.sha256)return json({error:'ARTIFACT_DIGEST_MISMATCH'},400);
   await bucket.put('braink-development/'+value.id+'/'+registered.path,bytes);
  }
  const serialized=JSON.stringify(value.report);
  if(job.status!=='running')return job.detail===serialized?json({ok:true,replayed:true}):json({error:'RESULT_CONFLICT'},409);
  await db.prepare('UPDATE braink_sector_jobs SET status=?,detail=?,updated=? WHERE id=?').bind(value.report.status,serialized,now,value.id).run();
  await event(db,value.id,'completed',{status:value.report.status,receipt_sha256:value.report.receipt_sha256,source_digest:value.report.source_digest});
  return json({ok:true});
 }catch(error){return json({error:error.message||'CI_WORKER_ERROR'},500)}
}
