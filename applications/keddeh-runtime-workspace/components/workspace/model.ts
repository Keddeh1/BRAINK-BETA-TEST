export type Capability={id:string;kind:string;cloud_state:string;runtime_binding:string|null;reason:string|null;input_constraints:{required?:string[];optional?:string[];oneOf?:string[];effect?:string}};
export type Namespace={id:string;foundry_id:string|null;version:number;snapshot_digest:string|null;last_command:string|null;updated_at:string};
export type RecordRow={id:string;state:string;created_at:string;updated_at:string};
export type Registry={capabilities:Capability[];namespaces:Namespace[];records:RecordRow[]};
export type Job={id:string;sector:string;status:string;created:string;updated:string;detail:{request?:{operation:string;parameters:unknown};artifacts?:{path:string;sha256:string}[];[key:string]:unknown}};
export type StoredObject={id:string;name:string;domainId:string;objectKey:string;sizeBytes:number;digest:string};
export type Snapshot={domains:{id:string;name:string;state:string;kind:string}[];receipts:{id:string;domainId:string;observedState:string;digest:string}[];observedAt:string};
export type Target={id:string;title:string;evidence:Record<string,unknown>|null};
export async function requestJSON<T>(path:string,body?:unknown):Promise<T>{
 const response=await fetch(path,{cache:'no-store',...(body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})});
 const data=await response.json() as {error?:string;code?:string};if(!response.ok)throw Error(data.error||data.code||`Request failed (${response.status})`);return data as T;
}
export function inputTemplate(capability:Capability){return JSON.stringify(Object.fromEntries((capability.input_constraints.required||[]).map(key=>[key,key==='data'?{}:''])),null,2)}
export function statusCounts(jobs:Job[]){return jobs.reduce<Record<string,number>>((counts,job)=>({...counts,[job.status]:(counts[job.status]||0)+1}),{})}
