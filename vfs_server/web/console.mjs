import { KeddehVFSClient } from "/vfs-client.mjs";
const $ = id => document.getElementById(id);
const client = new KeddehVFSClient({ endpoint: location.origin });
let allocation = null;
function notice(message,ok=false) { $("notice").textContent=message; $("notice").dataset.state=ok?"ok":"error"; }
function display(value) { return JSON.stringify(value,null,2); }
async function refresh() {
  try {
    const status=await client.status();
    if (status.role!=="VFS_ALLOCATOR") throw new Error("Unexpected VFS_SERVER role");
    $("service-status").textContent=status.service_environment.carrier_id+" · connected";
    $("counts").textContent=status.instances+" VFS instances · "+status.ab_entries+" A/B entries";
    const all=await client.allocations();
    $("fleet").textContent=all.allocations.length?display(all.allocations.map(x=>({vfs_id:x.vfs_id,label:x.label,source_ref:x.source_ref,state:x.state}))):"No allocations yet.";
    $("allocate").disabled=false;
    notice("VFS_SERVER connected. Open the queue form, then allocate a VFS.",true);
  } catch(error) {
    $("service-status").textContent="Service unavailable or authorization required";
    $("counts").textContent="";
    $("fleet").textContent="No live readback.";
    $("allocate").disabled=true;
    notice("Connection failed: "+error.message);
  }
}
$("refresh").addEventListener("click",refresh);
$("allocate-form").addEventListener("submit",async event=>{
  event.preventDefault();
  $("allocate").disabled=true;
  try {
    allocation=await client.allocate({label:$("label").value.trim(),sourceRef:$("source").value.trim()});
    $("allocation-result").textContent="Allocated VFS: "+allocation.vfs_id;
    $("admit").disabled=false;
    notice("VFS allocated. Select A and B, then admit the compressed pair.",true);
    await refresh();
  } catch(error) { notice("Allocation failed: "+error.message); }
  finally { $("allocate").disabled=false; }
});
$("ab-form").addEventListener("submit",async event=>{
  event.preventDefault();
  if (!allocation) return notice("Allocate a VFS first.");
  const aFile=$("a-file").files[0],bFile=$("b-file").files[0];
  if (!aFile||!bFile) return notice("Select both A and B files.");
  if (aFile.size>32*1024*1024||bFile.size>32*1024*1024) return notice("Each side must be at most 32 MiB.");
  $("admit").disabled=true;
  notice("Compressing, storing, reconstructing and observing A/B…");
  try {
    const a=new Uint8Array(await aFile.arrayBuffer()),b=new Uint8Array(await bFile.arrayBuffer());
    const result=await client.admitAB({vfsId:allocation.vfs_id,a,b,sourceRef:allocation.source_ref});
    $("evidence").textContent=display({
      classification:result.serviceEnvironment.classification,
      carrier:result.serviceEnvironment.carrier_id,
      source_ref:allocation.source_ref,
      vfs_id:allocation.vfs_id,
      entry_id:result.entry.entry_id,
      a_digest:result.entry.a_digest,b_digest:result.entry.b_digest,
      codec:result.entry.b_codec,
      source_bytes:result.compression.source_bytes,stored_bytes:result.compression.stored_bytes,
      actor_receipts:result.actorReceipts.map(x=>x.receipt_id),
      observer_receipts:result.observerReceipts.map(x=>x.receipt_id),
      readback:"VERIFIED"
    });
    notice("A/B reconstructed and independently observed. Record this evidence in the queue issue.",true);
    await refresh();
  } catch(error) { notice("A/B admission or readback failed: "+error.message); }
  finally { $("admit").disabled=false; }
});
refresh();
