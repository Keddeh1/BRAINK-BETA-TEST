import {experienceAPI as historicalExperience} from './experience-service-store.mjs';
const endpoint='https://keddeh-systems-runtime.aboudy65097.chatgpt.site/api/experience-sector/website';
const json=(value,status)=>Response.json(value,{status,headers:{'Cache-Control':'private,no-store'}});
export async function experienceRuntimeAPI(request,env,fetcher=fetch){
 if(new URL(request.url).pathname!=='/api/experience-sector')return null;
 const user_id=request.headers.get('oai-authenticated-user-id'),email=request.headers.get('oai-authenticated-user-email');
 if(!user_id||!email)return json({error:'AUTHENTICATION_REQUIRED'},401);
 if(!['GET','POST'].includes(request.method))return json({error:'METHOD_NOT_ALLOWED'},405);
 if(request.method==='GET'&&(!env.BRAINK_OWNER_EMAIL||email.trim().toLowerCase()!==env.BRAINK_OWNER_EMAIL.trim().toLowerCase()))return json({error:'ACCESS_DENIED'},403);
 const origin=request.headers.get('Origin');
 if(request.method==='POST'&&(request.headers.get('Sec-Fetch-Site')==='cross-site'||origin&&origin!==new URL(request.url).origin))return json({error:'ACCESS_DENIED'},403);
 if(!env.BRAINK_CI_WEBSITE_TOKEN)return json({error:'SERVICE_UNAVAILABLE'},503);
 try{
  if(request.method==='POST'&&!request.headers.get('Content-Type')?.startsWith('application/json'))return json({error:'JSON_REQUIRED'},415);
  const submission=request.method==='POST'?await request.json():undefined;
  const response=await fetcher(endpoint,{method:'POST',headers:{'Authorization':'Bearer '+env.BRAINK_CI_WEBSITE_TOKEN,'Content-Type':'application/json'},body:JSON.stringify({identity:{site_id:'appgprj_6aa52748b7788191afe0f7f86fc78833',user_id,email},method:request.method,submission}),redirect:'manual'});
  if(request.method==='GET'&&response.ok){
   const active=await response.json(),priorResponse=await historicalExperience(request,env);
   if(!priorResponse.ok)return priorResponse;
   const prior=await priorResponse.json(),requests=[...active.requests,...prior.requests],feedback=[...active.feedback,...prior.feedback];
   return json({...active,requests,feedback,summary:{requests:requests.length,responses:feedback.length,mean_reported_ease:feedback.length?feedback.reduce((sum,row)=>sum+row.rating,0)/feedback.length:null}},200);
  }
  return new Response(response.body,{status:response.status,headers:{'Content-Type':'application/json','Cache-Control':'private,no-store'}});
 }catch(error){console.error('experience-runtime-fetch',error?.name,error?.message);return json({error:'SERVICE_UNAVAILABLE'},503)}
}
