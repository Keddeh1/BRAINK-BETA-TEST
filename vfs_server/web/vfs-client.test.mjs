import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createServer } from "node:http";
import { KeddehVFSClient } from "./vfs-client.mjs";

const environment = { classification: "KEDDEH_SERVICE", system: "KEDDEH_SYSTEMS",
  subsystem: "VFS_SERVER", carrier_id: "VFS_SERVER:loopback", transport: "HTTP" };
const vfsId = "a".repeat(32), entryId = "b".repeat(32);
const sha = bytes => createHash("sha256").update(bytes).digest("hex");

test("HTML client allocates VFS, admits A/B, reads both sides and observes", async () => {
  let allocation = 0, admission = 0, observation = 0, pair;
  const server = createServer(async (req, res) => {
    const json = (status, value) => { res.writeHead(status, { "content-type": "application/json" });
      res.end(JSON.stringify({ ...value, service_environment: environment })); };
    if (req.url === "/status") return json(200, { server: "VFS_SERVER", role: "VFS_ALLOCATOR" });
    if (req.headers.authorization !== "Bearer test-secret") return json(401, { error: "unauthorized" });
    const chunks = []; for await (const chunk of req) chunks.push(chunk);
    const data = chunks.length ? JSON.parse(Buffer.concat(chunks).toString()) : {};
    if (req.url === "/vfs" && req.method === "POST") {
      allocation++; assert.equal(data.source_ref, "queue#3");
      return json(201, { allocation: { vfs_id: vfsId, source_ref: data.source_ref } });
    }
    if (req.url === "/vfs/" + vfsId + "/ab" && req.method === "POST") {
      admission++; pair = data;
      const entry = { vfs_id: vfsId, entry_id: entryId, a_digest: sha(Buffer.from(pair.a_b64,"base64")),
        b_digest: sha(Buffer.from(pair.b_b64,"base64")), b_codec: "zlib" };
      return json(201, { entry, actor_receipts: [{ kind: "VFS_ARTIFACT_WRITE" }],
        verification: "PENDING_OBSERVER_READBACK" });
    }
    if (req.url === "/vfs/" + vfsId + "/ab/" + entryId && req.method === "GET")
      return json(200, { entry: { entry_id: entryId }, a_b64: pair.a_b64, b_b64: pair.b_b64 });
    if (req.url === "/vfs/" + vfsId + "/ab/" + entryId + "/verify" && req.method === "POST") {
      observation++;
      return json(200, { verified: true, entry: { entry_id: entryId },
        a_b64: pair.a_b64, b_b64: pair.b_b64, compression: { b_codec: "zlib" },
        observer_receipts: [{ kind: "OBSERVER_VFS_READBACK" }] });
    }
    return json(404, { error: "not_found" });
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  try {
    const client = new KeddehVFSClient({ endpoint: "http://127.0.0.1:" + server.address().port,
      bearer: () => "test-secret", carrierId: environment.carrier_id });
    const result = await client.allocateAndAdmit({ label: "workflow", sourceRef: "queue#3",
      a: new Uint8Array([0,1,2]), b: new Uint8Array([0,1,3]) });
    assert.equal(result.allocation.vfs_id, vfsId);
    assert.equal(result.admission.entry.entry_id, entryId);
    assert.equal(result.admission.compression.b_codec, "zlib");
    assert.equal(allocation, 1); assert.equal(admission, 1); assert.equal(observation, 1);
  } finally { await new Promise(resolve => server.close(resolve)); }
});

test("service identity mismatch stops the carrier", async () => {
  const server=createServer((_req,res)=>{res.writeHead(200,{"content-type":"application/json"});
    res.end(JSON.stringify({service_environment:{...environment,classification:"UNKNOWN"}}));});
  await new Promise(resolve => server.listen(0,"127.0.0.1",resolve));
  try {
    const client=new KeddehVFSClient({endpoint:"http://127.0.0.1:"+server.address().port});
    await assert.rejects(client.status(),/KEDDEH_SERVICE_IDENTITY_MISMATCH/);
  } finally {await new Promise(resolve=>server.close(resolve));}
});
