import test from "node:test";
import assert from "node:assert/strict";
import { createHash, createHmac } from "node:crypto";
import { createServer } from "node:http";
import { KeddehVFSClient } from "./vfs-client.mjs";
import { VFSActuatorConnection } from "./actuator-connection.mjs";

const environment={classification:"KEDDEH_SERVICE",system:"KEDDEH_SYSTEMS",
  subsystem:"VFS_SERVER",carrier_id:"VFS_SERVER:loopback",transport:"HTTP"};
const vfsId="a".repeat(64),entryId="b".repeat(32),secret="c".repeat(64),bits="101010101";
const digest=createHash("sha256").update(Buffer.from([0xaa,0x80])).digest("hex");
const graph={origin:{from:1,to:2,powered:true,addressable:false},
  mappings:[...bits].map((v,i)=>({x:i+1,address:i+2,state:Number(v),symbol:v==="1"?"A":"B",
    expression:(v==="1"?"A":"B")+"X("+(i+1)+")"}))};
const entry={vfs_id:vfsId,entry_id:entryId,codec:"KEDDEH_AB_BINARY_V1",
  bits_count:9,object_digest:digest};
const proof={bits,sha256:digest,codec:"KEDDEH_AB_BINARY_V1",packed_bytes:2};

test("registered actuator crosses HTTP A/B admission, readback and observation",async()=>{
  let admitted=0,observed=0,replays=0;const seen=new Set();
  const server=createServer(async(req,res)=>{
    const json=(code,value)=>{res.writeHead(code,{"content-type":"application/json"});
      res.end(JSON.stringify({...value,service_environment:environment}));};
    if(req.url==="/status")return json(200,{server:"VFS_SERVER",role:"VFS_ALLOCATOR"});
    if(req.headers.authorization!=="Bearer owner")return json(401,{error:"unauthorized"});
    const chunks=[];for await(const chunk of req)chunks.push(chunk);
    const raw=Buffer.concat(chunks),body=raw.length?JSON.parse(raw.toString()):{};
    if(req.url==="/vfs"&&req.method==="POST")
      return json(201,{allocation:{vfs_id:vfsId,source_ref:body.source_ref}});
    const command=req.url==="/vfs/"+vfsId+"/ab"&&req.method==="POST"?"ab.admit":
      req.url==="/vfs/"+vfsId+"/ab/"+entryId+"/verify"&&req.method==="POST"?"ab.observe":null;
    if(command){
      const nonce=req.headers["x-vfs-nonce"],at=req.headers["x-vfs-time"];
      if(req.headers["x-vfs-surface"]!=="owner-site"||!nonce||!at)return json(403,{error:"proof_required"});
      const message=["POST",req.url,"owner-site",createHash("sha256").update(raw).digest("hex"),
        at,nonce,command].join("|");
      const expected=createHmac("sha256",Buffer.from(secret,"hex")).update(message).digest("hex");
      if(expected!==req.headers["x-vfs-signature"])return json(403,{error:"invalid_signature"});
      if(seen.has(nonce)){replays++;return json(409,{error:"nonce_replayed"});}
      seen.add(nonce);
    }
    if(command==="ab.admit"){admitted++;assert.equal(body.bits,bits);
      return json(201,{entry,graph,actor_receipt:{kind:"VFS_ARTIFACT_WRITE"},
        verification:"PENDING_OBSERVER_READBACK"});}
    if(req.url==="/vfs/"+vfsId+"/ab/"+entryId&&req.method==="GET")
      return json(200,{entry,proof,graph,verified:true});
    if(command==="ab.observe"){observed++;return json(200,{entry,proof,graph,verified:true,
      observer_receipt:{kind:"OBSERVER_VFS_READBACK"}});}
    return json(404,{error:"not_found"});
  });
  await new Promise(resolve=>server.listen(0,"127.0.0.1",resolve));
  try{
    const endpoint="http://127.0.0.1:"+server.address().port;
    const actuator=new VFSActuatorConnection({surfaceId:"owner-site",secretHex:secret});
    const client=new KeddehVFSClient({endpoint,bearer:"owner",actuator,
      carrierId:environment.carrier_id});
    const allocation=await client.allocate({label:"workflow",sourceRef:"queue#3"});
    assert.equal(allocation.vfs_id,vfsId);
    const result=await client.admitAB({vfsId,bits,sourceRef:"queue#3"});
    assert.equal(result.proof.bits,bits);
    assert.equal(result.graph.origin.addressable,false);
    assert.equal(admitted,1);assert.equal(observed,1);assert.equal(replays,0);
    const noActuator=new KeddehVFSClient({endpoint,bearer:"owner"});
    await assert.rejects(noActuator.admitAB({vfsId,bits,sourceRef:"queue#3"}),
      /VFS_ACTUATOR_CONNECTION_REQUIRED/);
  }finally{await new Promise(resolve=>server.close(resolve));}
});
