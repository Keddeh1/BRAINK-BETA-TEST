'use client';
import {useCallback,useEffect,useState} from 'react';
import {Activity,Boxes,Command,FileCode2,FolderTree,Layers3,Network,RefreshCw,Search,Server,Terminal} from 'lucide-react';
import {Button} from '@/components/ui/button';
import {Input} from '@/components/ui/input';
import {Textarea} from '@/components/ui/textarea';
import {Tabs,TabsContent,TabsList,TabsTrigger} from '@/components/ui/tabs';
import {Select,SelectContent,SelectItem,SelectTrigger,SelectValue} from '@/components/ui/select';
import {Table,TableBody,TableCell,TableHead,TableHeader,TableRow} from '@/components/ui/table';
import {requestJSON,inputTemplate,statusCounts,type Registry,type Job,type Snapshot,type Target,type StoredObject} from './model';
import './workspace.css';
import {WorkspaceContext,useWorkspaceState} from './state';
import {Overview} from './overview';
import {ExecutionConsole} from './console';
import {Topology} from './topology';
import {FileWorkspace} from './files';
import {SectorDelivery} from './delivery';
const sections=[['overview','Overview',Activity],['console','BRAINK console',Terminal],['topology','Namespaces & nodes',Network],['files','VFS workspace',FolderTree],['delivery','Sector delivery',Layers3]] as const;
export default function Workspace(){const state=useWorkspaceState();const {view,setView,registry,snapshot,jobs,targets,files,errors,busy,query,setQuery,notice,setNotice,capabilityId,setCapabilityId,namespace,setNamespace,input,setInput,result,setResult,selectedNode,setSelectedNode,objectName,setObjectName,content,setContent,opened,sector,setSector,operation,setOperation,parameters,setParameters,refresh,capability,counts,filteredFiles,filteredCapabilities,act,execute,openFile}=state;
 return <WorkspaceContext.Provider value={state}><div className="kw-shell"><a className="kw-skip" href="#kw-main">Skip to workspace</a><aside className="kw-sidebar"><a className="kw-wordmark" href="/">KEDDEH<span>SYSTEMS RUNTIME</span></a><div className="kw-estate"><Server size={19}/><div>Owner estate<small>Operational workspace</small></div></div><nav aria-label="Workspace sections">{sections.map(([id,label,Icon])=><Button key={id} variant="ghost" className={'kw-nav '+(view===id?'kw-nav-active':'')} onClick={()=>{setView(id);setQuery('')}}><Icon size={18}/>{label}</Button>)}</nav><div className="kw-sidebar-bottom"><a href="/develop">Source development</a><a href="/design-studio">Website design studio</a><a href="/agentics">IL-LLM agent surface</a><a href="/">Existing control plane</a><a href="https://www.keddeh.com/development/experience">KEDDEH.COM</a></div></aside><main id="kw-main" className="kw-main"><header className="kw-toolbar"><div className="kw-breadcrumb">KEDDEH / <span>{sections.find(s=>s[0]===view)?.[1]}</span></div><div className="kw-tools"><Search size={17}/><Input aria-label="Search capabilities or files" placeholder="Search capabilities or files" value={query} onChange={e=>{setQuery(e.target.value);if(view!=='files'&&view!=='console')setView('console')}}/><Button variant="outline" aria-label="Refresh workspace" disabled={busy} onClick={()=>void act(refresh)}><RefreshCw size={17}/></Button></div></header><div className="kw-content"><div className="kw-page-title"><div><p className="kw-eyebrow">BRAINK / KEX / IL-LLM</p><h1>{sections.find(s=>s[0]===view)?.[1]}</h1></div><p className="kw-observed">{snapshot?.observedAt?'Observed '+new Date(snapshot.observedAt).toLocaleTimeString():'Awaiting runtime response'}</p></div>{notice&&<p className="kw-notice" role="status">{notice}</p>}{errors.length>0&&<div className="kw-error" role="alert">{errors.map(error=><p key={error}>{error}</p>)}</div>}
 {view==='overview'&&<Overview/>}
 {view==='console'&&<ExecutionConsole/>}
 {view==='topology'&&<Topology/>}
 {view==='files'&&<FileWorkspace/>}
 {view==='delivery'&&<SectorDelivery/>}
 </div></main></div></WorkspaceContext.Provider>
}
