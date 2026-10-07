import {ownerCI,workerCI} from './braink-ci-store.mjs';
const json=(value,status=200)=>Response.json(value,{status,headers:{'Cache-Control':'private,no-store'}});
export async function developmentAPI(request,env){
 const path=new URL(request.url).pathname;
 if(path==='/api/braink-development/worker'){
  if(request.method!=='POST')return json({error:'METHOD_NOT_ALLOWED'},405);
  if(!env.BRAINK_CI_AGENT_TOKEN||request.headers.get('Authorization')!=='Bearer '+env.BRAINK_CI_AGENT_TOKEN)return json({error:'UNAUTHORIZED'},401);
  const value=await request.clone().json();
  if(['submit','list','artifact'].includes(value.op)){
   const url=new URL(request.url);url.pathname='/api/braink-development';
   if(value.op==='artifact'){url.searchParams.set('job',value.id);url.searchParams.set('artifact',value.path)}
   const forwarded=new Request(url,{method:value.op==='submit'?'POST':'GET',headers:{'Content-Type':'application/json'},body:value.op==='submit'?JSON.stringify(value):undefined});
   return ownerCI(forwarded,env.DB,env.CLAIMPATH_RECEIPTS);
  }
  return workerCI(request,env.DB,env.CLAIMPATH_RECEIPTS);
 }
 if(!['/api/braink-development','/api/braink-development/artifact'].includes(path))return null;
 const id=request.headers.get('oai-authenticated-user-id'),email=request.headers.get('oai-authenticated-user-email');
 if(!id||!email)return json({error:'AUTHENTICATION_REQUIRED'},401);
 if(!env.BRAINK_OWNER_EMAIL||email.trim().toLowerCase()!==env.BRAINK_OWNER_EMAIL.trim().toLowerCase())return json({error:'ACCESS_DENIED'},403);
 if(!['GET','POST'].includes(request.method))return json({error:'METHOD_NOT_ALLOWED'},405);
 if(request.method==='POST'){
  const origin=request.headers.get('Origin');
  if(request.headers.get('Sec-Fetch-Site')==='cross-site'||origin&&origin!==new URL(request.url).origin)return json({error:'ACCESS_DENIED'},403);
 }
 return ownerCI(request,env.DB,env.CLAIMPATH_RECEIPTS);
}
export function developmentPage(path){
 if(!['/braink/development','/braink/ci','/braink/ide','/braink/cli'].includes(path))return null;
 const mode=path.split('/').pop();
 return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>BRAINK ${mode.toUpperCase()} · Keddeh Systems</title>
 <style>*{box-sizing:border-box}body{margin:0;background:#07111f;color:#e8f1ff;font:16px/1.6 system-ui}a{color:#b5d8ff}header{padding:24px 5vw;border-bottom:1px solid #324860;display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap}main{padding:28px 5vw;max-width:1500px;margin:auto}h1{font-size:30px;margin:0 0 18px}nav{display:flex;gap:20px;flex-wrap:wrap}button,input,select,textarea{font:inherit;color:inherit;background:#12253c;border:1px solid #597089;border-radius:5px;padding:10px}button{cursor:pointer}button:disabled{opacity:.5;cursor:wait}button:focus-visible,a:focus-visible,input:focus-visible,textarea:focus-visible{outline:3px solid #98e9d8;outline-offset:3px}.toolbar{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:24px}.grid{display:grid;grid-template-columns:240px 1fr;gap:20px}textarea{width:100%;height:45vh;font:14px/1.6 monospace}.files button{display:block;width:100%;text-align:left;overflow-wrap:anywhere;margin:8px 0}table{border-collapse:collapse;width:100%}td,th{padding:12px;text-align:left;border-bottom:1px solid #324860}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#0c1b2e;padding:18px;max-height:70vh;overflow:auto}.muted{color:#afc0d5}@media(max-width:700px){.grid{grid-template-columns:1fr}table{display:block;overflow:auto}}</style>
 <header><a href="/braink">KEDDEH SYSTEMS / BRAINK</a><nav aria-label="Development sector"><a href="/braink/development">Delivery</a><a href="/braink/ide">IDE</a><a href="/braink/cli">CLI</a><a href="/braink/ci">CI</a></nav></header>
 <main><h1>BRAINK ${mode==='development'?'development sector':mode.toUpperCase()}</h1><div id="auth"><a href="/signin-with-chatgpt?return_to=${encodeURIComponent(path)}" target="_top">Sign in with your owner account</a></div>
 ${mode==='ide'?'<div class="toolbar"><button id="files-button">Load workspace</button><input id="file-path" aria-label="Workspace file path" placeholder="projects/BRAINK/main.py"><button id="new-file">New file</button><button id="save-file">Save file</button></div><div class="grid"><aside id="file-list" class="files"></aside><section><label for="editor">File contents</label><textarea id="editor" spellcheck="false"></textarea></section></div>':''}
 ${mode==='cli'?'<form id="cli-form" class="toolbar"><label for="command">braink-node</label><input id="command" value="check" aria-label="BRAINK command arguments"><button>Execute</button></form>':''}
 <div class="toolbar"><label for="sector">Clean build</label><select id="sector"><option value="all">Every development sector</option><option value="core">Core</option><option value="ide">IDE</option><option value="cli">CLI</option><option value="ci">CI</option></select><button id="build">Run clean build</button><button id="refresh">Refresh jobs</button></div>
 <p id="status" role="status">Connecting to your runtime…</p><table><thead><tr><th>Sector</th><th>Job</th><th>Execution</th><th>Result</th></tr></thead><tbody id="jobs"></tbody></table><pre id="output" aria-live="polite">Select a job to inspect its stages, logs and artifact receipts.</pre></main>
 <script>
 const el=id=>document.getElementById(id);let state=[],revision=null;
 async function api(body){const response=await fetch('/api/braink-development',{method:body?'POST':'GET',credentials:'same-origin',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined});const result=await response.json();if(!response.ok)throw Error(result.error);return result}
 const show=value=>{el('output').textContent=JSON.stringify(value,null,2);const old=document.getElementById('artifact-links');if(old)old.remove();const links=document.createElement('nav');links.id='artifact-links';for(const artifact of value.artifacts||[]){const link=document.createElement('a');link.href='/api/braink-development/artifact?job='+encodeURIComponent(value.remote_job_id||'')+'&artifact='+encodeURIComponent(artifact.path);link.textContent='Download '+artifact.path;links.append(link)}el('output').after(links)};
 async function refresh(){const data=await api();state=data.jobs;el('auth').hidden=true;el('status').textContent='Connected to your Keddeh runtime';el('jobs').replaceChildren();for(const job of state){const row=document.createElement('tr');for(const text of [job.sector,job.id.slice(0,12),job.status]){const cell=document.createElement('td');cell.textContent=text;row.append(cell)}const cell=document.createElement('td'),button=document.createElement('button');button.textContent='Inspect';button.onclick=()=>show({...job.detail,remote_job_id:job.id});cell.append(button);row.append(cell);el('jobs').append(row)}}
 async function perform(fn){try{await fn()}catch(error){el('status').textContent=error.message;el('auth').hidden=error.message!=='AUTHENTICATION_REQUIRED'}}
 async function submit(sector,operation='qualify',parameters={}){const id=crypto.randomUUID().replaceAll('-','');await api({op:'submit',id,sector,operation,parameters});await refresh();return id}
 async function action(operation,parameters={}){const id=await submit('${mode==='cli'?'cli':'ide'}',operation,parameters);el('status').textContent='Executing '+operation;for(let n=0;n<120;n++){await new Promise(resolve=>setTimeout(resolve,1000));await refresh();const job=state.find(j=>j.id===id);if(job&&['passed','failed','error'].includes(job.status)){show(job.detail);if(job.status!=='passed')throw Error(job.detail.reason||'Execution failed');return job.detail.outputs}}throw Error('Job is still executing; inspect its retained status in the job list')}
 el('build').onclick=()=>perform(async()=>{await submit(el('sector').value);el('status').textContent='Clean sector build queued on your server'});
 el('refresh').onclick=()=>perform(refresh);
 if(el('cli-form'))el('cli-form').onsubmit=event=>{event.preventDefault();perform(async()=>show(await action('cli',{command:el('command').value})))};
 if(el('files-button')){el('files-button').onclick=()=>perform(async()=>{const result=await action('file-list');el('file-list').replaceChildren();for(const path of result.files){const button=document.createElement('button');button.textContent=path;button.onclick=()=>perform(async()=>{const file=await action('file-read',{path});el('file-path').value=path;el('editor').value=file.content;revision=file.revision});el('file-list').append(button)}});el('new-file').onclick=()=>{revision=null;el('editor').value=''};el('save-file').onclick=()=>perform(async()=>{const result=await action('file-save',{path:el('file-path').value,content:el('editor').value,revision});revision=result.revision;show(result)})}
 perform(refresh);
 </script></html>`;
}
