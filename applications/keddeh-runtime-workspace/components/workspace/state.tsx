'use client';
import {createContext,useContext,useCallback,useEffect,useState} from 'react';
import {requestJSON,inputTemplate,statusCounts,type Registry,type Job,type Snapshot,type Target,type StoredObject} from './model';
const emptyRegistry:Registry={capabilities:[],namespaces:[],records:[]};
export function useWorkspaceState(){
 const [view,setView]=useState('overview'),[registry,setRegistry]=useState<Registry>(emptyRegistry),[snapshot,setSnapshot]=useState<Snapshot|null>(null),[jobs,setJobs]=useState<Job[]>([]),[targets,setTargets]=useState<Target[]>([]),[files,setFiles]=useState<StoredObject[]>([]),[errors,setErrors]=useState<string[]>([]),[busy,setBusy]=useState(false),[query,setQuery]=useState(''),[notice,setNotice]=useState(''),[capabilityId,setCapabilityId]=useState(''),[namespace,setNamespace]=useState('braink://owner/workspace'),[input,setInput]=useState('{}'),[result,setResult]=useState<unknown>(null),[selectedNode,setSelectedNode]=useState(''),[objectName,setObjectName]=useState(''),[content,setContent]=useState(''),[opened,setOpened]=useState<StoredObject|null>(null),[sector,setSector]=useState('ide'),[operation,setOperation]=useState('qualify'),[parameters,setParameters]=useState('{}');
 const refresh=useCallback(async()=>{
  const requests=await Promise.allSettled([requestJSON<Registry>('/api/workspace'),requestJSON<Snapshot>('/api/runtime'),requestJSON<{jobs:Job[]}>('/api/braink-ci'),requestJSON<{targets:Target[]}>('/api/workspace?view=architecture'),requestJSON<{objects:StoredObject[]}>('/api/vfs')]);
  if(requests[0].status==='fulfilled')setRegistry(requests[0].value);
  if(requests[1].status==='fulfilled')setSnapshot(requests[1].value);
  if(requests[2].status==='fulfilled')setJobs(requests[2].value.jobs);
  if(requests[3].status==='fulfilled')setTargets(requests[3].value.targets);
  if(requests[4].status==='fulfilled')setFiles(requests[4].value.objects);
  setErrors(requests.flatMap((r,i)=>r.status==='rejected'?[`${['Capabilities','Runtime','Delivery','Architecture','VFS'][i]}: ${String(r.reason)}`]:[]));
 },[]);
 useEffect(()=>{void refresh();const timer=setInterval(()=>void refresh(),15000);return()=>clearInterval(timer)},[refresh]);
 const capability=registry.capabilities.find(c=>c.id===capabilityId),counts=statusCounts(jobs),filteredFiles=files.filter(f=>(f.name+' '+f.domainId).toLowerCase().includes(query.toLowerCase())),filteredCapabilities=registry.capabilities.filter(c=>c.id.toLowerCase().includes(query.toLowerCase()));
 async function act(action:()=>Promise<void>){setBusy(true);setNotice('');try{await action();await refresh()}catch(error){setNotice(String(error))}finally{setBusy(false)}}
 async function execute(){const node=registry.namespaces.find(n=>n.id===namespace);const response=await requestJSON('/api/workspace',{commandId:'workspace-'+crypto.randomUUID(),capabilityId,namespaceId:namespace,foundryId:node?.foundry_id??null,...(node?{expectedVersion:node.version}:{}),input:JSON.parse(input)});setResult(response);setNotice('Execution record received.');}
 async function openFile(file:StoredObject){const data=await requestJSON<{name:string;content:string}>('/api/vfs?id='+encodeURIComponent(file.id));setOpened(file);setObjectName(data.name);setContent(data.content);setNotice('Stored content loaded and integrity checked.');}
 return {view,setView,registry,snapshot,jobs,targets,files,errors,busy,query,setQuery,notice,setNotice,capabilityId,setCapabilityId,namespace,setNamespace,input,setInput,result,setResult,selectedNode,setSelectedNode,objectName,setObjectName,content,setContent,opened,sector,setSector,operation,setOperation,parameters,setParameters,refresh,capability,counts,filteredFiles,filteredCapabilities,act,execute,openFile};
}
type WorkspaceState=ReturnType<typeof useWorkspaceState>;
export const WorkspaceContext=createContext<WorkspaceState|null>(null);
export function useWorkspace(){const state=useContext(WorkspaceContext);if(!state)throw Error("Workspace provider missing");return state;}
