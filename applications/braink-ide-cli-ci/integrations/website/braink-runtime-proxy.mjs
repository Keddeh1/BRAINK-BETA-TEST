import {ownerCI as historicalOwnerCI,workerCI as historicalWorkerCI} from './braink-ci-store.mjs';
import {architectureStore as historicalArchitecture} from './braink-architecture-store.mjs';
const endpoint='https://keddeh-systems-runtime.aboudy65097.chatgpt.site/api/braink-ci/website';
const json=(value,status=200)=>Response.json(value,{status,headers:{'Cache-Control':'private,no-store'}});
async function remote(env,value,query='',fetcher=fetch,base=endpoint){
 if(!env.BRAINK_CI_WEBSITE_TOKEN)return json({error:'SERVICE_UNAVAILABLE'},503);
 try{return await fetcher(base+query,{method:value?'POST':'GET',headers:{'Authorization':'Bearer '+env.BRAINK_CI_WEBSITE_TOKEN,...(value?{'Content-Type':'application/json'}:{})},body:value?JSON.stringify(value):undefined,redirect:'manual'})}catch(error){console.error('braink-runtime-fetch',error?.name,error?.message);return json({error:'RUNTIME_UNAVAILABLE'},503)}
}
export async function runtimeOwnerCI(request,env,fetcher=fetch){
 const url=new URL(request.url);
 if(request.method==='POST'){
  const value=await request.clone().json();
  const old=await env.DB.prepare('SELECT id FROM braink_sector_jobs WHERE id=?').bind(value.id||'').first();
  return old?historicalOwnerCI(request,env.DB,env.CLAIMPATH_RECEIPTS):remote(env,value,'',fetcher);
 }
 const response=await remote(env,null,url.search,fetcher);
 if(url.searchParams.get('artifact'))return response.status===404?historicalOwnerCI(request,env.DB,env.CLAIMPATH_RECEIPTS):response;
 if(!response.ok)return response;
 const [active,prior]=await Promise.all([response.json(),historicalOwnerCI(request,env.DB,env.CLAIMPATH_RECEIPTS).then(r=>r.json())]);
 return json({...active,jobs:[...(active.jobs||[]).map(row=>({...row,storage_origin:'runtime'})),...(prior.jobs||[]).map(row=>({...row,storage_origin:'frontage-history'}))].sort((a,b)=>b.created.localeCompare(a.created)),events:[...(active.events||[]),...(prior.events||[])],backing_runtime:'Keddeh Systems Runtime'});
}
export async function runtimeWorkerCI(request,env,fetcher=fetch){
 const value=await request.clone().json();
 if(value.op==='backend-readback'){
  const responses=await Promise.all([remote(env,{op:'verify-transport'},'',fetcher),remote(env,{op:'verify-transport'},'',fetcher,'https://keddeh-systems-runtime.aboudy65097.chatgpt.site/api/experience-sector/website')]);
  const [runtime,experience]=await Promise.all(responses.map(response=>response.json()));
  const ready=responses.every(response=>response.ok)&&runtime.ready===true&&experience.verified===true;
  return json({runtime,experience,ready},ready?200:503);
 }
 if(value.op==='claim'){
  const old=await env.DB.prepare("SELECT id FROM braink_sector_jobs WHERE status IN ('queued','running') ORDER BY created LIMIT 1").first();
  if(old)return historicalWorkerCI(request,env.DB,env.CLAIMPATH_RECEIPTS);
 }else if(value.id){
  const old=await env.DB.prepare('SELECT id FROM braink_sector_jobs WHERE id=?').bind(value.id).first();
  if(old)return historicalWorkerCI(request,env.DB,env.CLAIMPATH_RECEIPTS);
 }
 return remote(env,{op:'worker',value},'',fetcher);
}
export async function runtimeArchitecture(env,value,fetcher=fetch){
 const response=await remote(env,{op:'worker',value},'',fetcher);
 if(value.op!=='architecture-status'||!response.ok)return response;
 const [active,old]=await Promise.all([response.json(),historicalArchitecture(env.DB,env.CLAIMPATH_RECEIPTS,value).then(r=>r.json())]);
 return json({...active,targets:active.targets.map(row=>{const prior=old.targets.find(x=>x.id===row.id)?.evidence;return prior&&(!row.evidence||prior.created>row.evidence.created)?{...row,evidence:prior}:row}),backing_runtime:'Keddeh Systems Runtime'});
}
