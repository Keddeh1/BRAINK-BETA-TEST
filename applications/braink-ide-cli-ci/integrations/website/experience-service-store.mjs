const json=(value,status=200)=>Response.json(value,{status,headers:{'Cache-Control':'private,no-store'}});
const services=new Set(['experience','ide','cli','ci','architecture','storage','claimpath']);
const tasks=new Set(['discovery','request','ide','cli','ci','architecture']);
const sha=async bytes=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');
export async function experienceAPI(request,env){
 if(new URL(request.url).pathname!=='/api/experience-sector')return null;
 const user=request.headers.get('oai-authenticated-user-id'),email=request.headers.get('oai-authenticated-user-email');
 if(!user||!email)return json({error:'AUTHENTICATION_REQUIRED'},401);
 if(!['GET','POST'].includes(request.method))return json({error:'METHOD_NOT_ALLOWED'},405);
 if(!env.DB||!env.CLAIMPATH_RECEIPTS)return json({error:'SERVICE_UNAVAILABLE'},503);
 try{
  await env.DB.prepare('CREATE TABLE IF NOT EXISTS experience_records(id TEXT PRIMARY KEY,kind TEXT,user_id TEXT,created_at TEXT,digest TEXT,document TEXT)').run();
  if(request.method==='GET'){
   if(!env.BRAINK_OWNER_EMAIL||email.trim().toLowerCase()!==env.BRAINK_OWNER_EMAIL.trim().toLowerCase())return json({error:'ACCESS_DENIED'},403);
   const rows=(await env.DB.prepare('SELECT kind,document FROM experience_records ORDER BY created_at DESC').all()).results;
   const records=await Promise.all(rows.map(async row=>{const record=JSON.parse(row.document),artifact=await env.CLAIMPATH_RECEIPTS.get('experience/'+row.kind+'/'+record.id+'.json');return {...record,storage_verified:!!artifact&&await sha(await artifact.arrayBuffer())===record.artifact_digest}}));
   const requests=records.filter(row=>row.kind==='request'),feedback=records.filter(row=>row.kind==='feedback'&&row.storage_verified);
   return json({requests,feedback,summary:{requests:requests.length,responses:feedback.length,mean_reported_ease:feedback.length?feedback.reduce((sum,row)=>sum+row.rating,0)/feedback.length:null},qualification:{evidence_kind:'consented self-reported feedback',human_participant_study_completed:false,independent_assessment_report_number:null}});
  }
  const origin=request.headers.get('Origin');
  if(request.headers.get('Sec-Fetch-Site')==='cross-site'||origin&&origin!==new URL(request.url).origin)return json({error:'ACCESS_DENIED'},403);
  if(!request.headers.get('Content-Type')?.startsWith('application/json'))return json({error:'JSON_REQUIRED'},415);
  const data=await request.json();
  if(!['request','feedback'].includes(data.op))return json({error:'INVALID_OPERATION'},400);
  const text=data.op==='request'?data.goal:data.comment||'';
  if(typeof text!=='string'||data.op==='request'&&(!text.trim()||!services.has(data.service))||data.op==='feedback'&&(!tasks.has(data.task)||!Number.isInteger(data.rating)||data.rating<1||data.rating>5||data.consent!==true))return json({error:'INVALID_SUBMISSION'},400);
  const id=data.id||crypto.randomUUID();
  if(!/^[a-f0-9-]{36}$/.test(id))return json({error:'INVALID_SUBMISSION'},400);
  const payload=data.op==='request'?{service:data.service,goal:text.trim()}:{task:data.task,rating:data.rating,comment:text.trim(),consent:true};
  const artifactKey='experience/'+data.op+'/'+id+'.json';
  const prior=await env.DB.prepare('SELECT user_id,document FROM experience_records WHERE id=?').bind(id).first();
  const created_at=new Date().toISOString(),document={schema:'keddeh.experience-record.v1',id,kind:data.op,created_at,user_id:user,contact_email:email,status:data.op==='request'?'received':'recorded',payload,...payload};
  const bytes=new TextEncoder().encode(JSON.stringify(document)),digest=await sha(bytes),candidate={...document,artifact_digest:digest};
  await env.DB.prepare('INSERT OR IGNORE INTO experience_records VALUES(?,?,?,?,?,?)').bind(id,data.op,user,created_at,digest,JSON.stringify(candidate)).run();
  const stored=await env.DB.prepare('SELECT user_id,document FROM experience_records WHERE id=?').bind(id).first(),record=JSON.parse(stored.document);
  if(stored.user_id!==user||record.kind!==data.op||JSON.stringify(record.payload)!==JSON.stringify(payload))return json({error:'REQUEST_ID_CONFLICT'},409);
  const {artifact_digest,...canonical}=record,canonicalBytes=new TextEncoder().encode(JSON.stringify(canonical));
  if(await sha(canonicalBytes)!==artifact_digest)throw Error('Stored receipt integrity failure');
  let artifact=await env.CLAIMPATH_RECEIPTS.get(artifactKey);
  if(!artifact){await env.CLAIMPATH_RECEIPTS.put(artifactKey,canonicalBytes,{httpMetadata:{contentType:'application/json'}});artifact=await env.CLAIMPATH_RECEIPTS.get(artifactKey)}
  if(!artifact||await sha(await artifact.arrayBuffer())!==artifact_digest)throw Error('Receipt artifact integrity failure');
  return json({id,status:record.status,created_at:record.created_at,service:record.service,artifact_digest},prior?200:201);
 }catch(error){console.error('experience-service',error?.name||'Error');return json({error:'SERVICE_UNAVAILABLE'},503)}
}
