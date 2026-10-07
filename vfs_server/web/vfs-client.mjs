const ident = value => /^[0-9a-f]{32}$/.test(value);
const validBits = bits => typeof bits === "string" && /^[01]{1,9}$/.test(bits);
const hex = bytes => [...new Uint8Array(bytes)].map(value => value.toString(16).padStart(2,"0")).join("");
const digest = async bytes => hex(await crypto.subtle.digest("SHA-256",bytes));
function pack(bits) {
  const bytes = new Uint8Array(Math.ceil(bits.length/8));
  for (let i=0;i<bits.length;i++) if (bits[i]==="1") bytes[i>>3]|=1<<(7-i%8);
  return bytes;
}
function assertGraph(graph,bits) {
  const root=graph?.origin;
  if (root?.from!==1 || root?.to!==2 || root.powered!==true || root.addressable!==false ||
      graph.mappings?.length!==bits.length) throw new Error("VFS_ORIGIN_MISMATCH");
  graph.mappings.forEach((mapping,i)=>{
    const state=Number(bits[i]),symbol=state?"A":"B";
    if (mapping.x!==i+1 || mapping.address!==i+2 || mapping.state!==state ||
        mapping.symbol!==symbol || mapping.expression!==symbol+"X("+(i+1)+")" || mapping.address===1)
      throw new Error("VFS_AB_GRAPH_MISMATCH");
  });
}
export class KeddehVFSClient {
  constructor({ endpoint, bearer, carrierId, transport = fetch }) {
    const url = new URL(endpoint);
    if (url.protocol !== "https:" && !(url.protocol === "http:" && ["127.0.0.1","localhost","[::1]"].includes(url.hostname)))
      throw new Error("VFS_TRANSPORT_NOT_ALLOWED");
    this.endpoint=url.origin;this.bearer=bearer;this.carrierId=carrierId;this.transport=transport;
  }
  assertService(value) {
    const env=value?.service_environment;
    if (env?.classification!=="KEDDEH_SERVICE" || env.system!=="KEDDEH_SYSTEMS" ||
        env.subsystem!=="VFS_SERVER" || (this.carrierId && env.carrier_id!==this.carrierId))
      throw new Error("KEDDEH_SERVICE_IDENTITY_MISMATCH");
    return env;
  }
  async request(path,{method="GET",body}={}) {
    const token=typeof this.bearer==="function"?await this.bearer():this.bearer;
    const response=await this.transport(this.endpoint+path,{method,
      headers:{...(token?{Authorization:"Bearer "+token}:{}),
        ...(body===undefined?{}:{"content-type":"application/json"})},
      ...(body===undefined?{}:{body:JSON.stringify(body)})});
    if (!response.ok) throw new Error("VFS_HTTP_"+response.status);
    const data=await response.json();this.assertService(data);return data;
  }
  status(){return this.request("/status");}
  allocations(){return this.request("/vfs");}
  async allocate({label,sourceRef,quotaBytes}) {
    if (!label||!sourceRef) throw new Error("VFS_ALLOCATION_INPUT_INVALID");
    const data=await this.request("/vfs",{method:"POST",body:{label,source_ref:sourceRef,
      ...(quotaBytes===undefined?{}:{quota_bytes:quotaBytes})}});
    if (!ident(data.allocation?.vfs_id)||data.allocation.source_ref!==sourceRef)
      throw new Error("VFS_ALLOCATION_MISMATCH");
    return data.allocation;
  }
  async admitAB({vfsId,bits,sourceRef}) {
    if (!ident(vfsId)||!validBits(bits)||!sourceRef) throw new Error("VFS_AB_INPUT_INVALID");
    const expected=await digest(pack(bits));
    const created=await this.request("/vfs/"+vfsId+"/ab",{method:"POST",body:{bits,source_ref:sourceRef}});
    const entry=created.entry;
    if (entry?.vfs_id!==vfsId || !ident(entry.entry_id) ||
        entry.codec!=="KEDDEH_AB_BINARY_V1" || entry.bits_count!==bits.length ||
        entry.object_digest!==expected || !created.actor_receipt ||
        created.verification!=="PENDING_OBSERVER_READBACK")
      throw new Error("VFS_AB_ACTOR_MISMATCH");
    assertGraph(created.graph,bits);
    const path="/vfs/"+vfsId+"/ab/"+entry.entry_id;
    const read=await this.request(path);
    if (read.entry?.entry_id!==entry.entry_id || read.proof?.bits!==bits ||
        read.proof?.sha256!==expected || read.verified!==true)
      throw new Error("VFS_AB_REVERSE_MISMATCH");
    assertGraph(read.graph,bits);
    const observed=await this.request(path+"/verify",{method:"POST",body:{}});
    if (observed.verified!==true || observed.entry?.entry_id!==entry.entry_id ||
        observed.proof?.bits!==bits || observed.proof?.sha256!==expected ||
        observed.observer_receipt?.kind!=="OBSERVER_VFS_READBACK")
      throw new Error("VFS_AB_OBSERVER_MISMATCH");
    assertGraph(observed.graph,bits);
    return Object.freeze({allocationId:vfsId,entry,proof:observed.proof,graph:observed.graph,
      actorReceipt:created.actor_receipt,observerReceipt:observed.observer_receipt,
      serviceEnvironment:observed.service_environment});
  }
  async allocateAndAdmit({label,sourceRef,bits,quotaBytes}) {
    const allocation=await this.allocate({label,sourceRef,quotaBytes});
    const admission=await this.admitAB({vfsId:allocation.vfs_id,bits,sourceRef});
    return Object.freeze({allocation,admission});
  }
}
