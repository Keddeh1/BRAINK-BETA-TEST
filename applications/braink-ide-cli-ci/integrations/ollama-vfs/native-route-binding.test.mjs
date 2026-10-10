import test from 'node:test';
import assert from 'node:assert/strict';
import {registerOllamaRoutes} from './ollama-transport.mjs';
import {createVfsOllamaActor} from './vfs-ollama-actor.mjs';
test('console route dispatches through native VFS actor and dispatcher context', async()=>{
 const records=new Map([['placed',{provider:'ollama',endpoint:'http://127.0.0.1:11434'}]]);
 const events=[];const vfs={async read(id){events.push('read');return {data:records.get(id)}},async create(id,m,d){events.push('persist');records.set(id,d)},async update(id,m,d){records.set(id,d)}};
 const actor=createVfsOllamaActor({vfs,inodeId:'placed',fetchImpl:async()=>{events.push('execute');return new Response('{"message":{"content":"provider output"}}')}});
 const routes={};registerOllamaRoutes({get:(p,f)=>routes[p]=f,post:(p,f)=>routes[p]=f},{actor,executionContext:async req=>req.nativeExecution,fetchImpl:()=>{throw Error('bypassed actor')}});
 const chunks=[];const res={status(){return this},setHeader(){},write(b){chunks.push(b);return true},end(){},on(){},json(b){throw Error(JSON.stringify(b))}};
 await routes['/api/ollama/chat']({body:{model:'resident',messages:[]},nativeExecution:{requestInodeId:'execution',requestPath:'/native/requests/one'}},res);
 assert.ok(events.indexOf('persist')<events.indexOf('execute'));
 assert.equal(records.get('execution').actor_inode,'placed');
 assert.equal(JSON.parse(Buffer.concat(chunks)).message.content,'provider output');
});
