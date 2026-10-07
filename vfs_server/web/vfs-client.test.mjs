import test from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createServer } from "node:http";
import { KeddehVFSClient } from "./vfs-client.mjs";

const environment = { classification: "KEDDEH_SERVICE", system: "KEDDEH_SYSTEMS",
  subsystem: "VFS_SERVER", carrier_id: "VFS_SERVER:loopback", transport: "HTTP" };

test("HTML-compatible client crosses HTTP write, raw readback and observer boundary", async () => {
  let content, digest, writes = 0, verifications = 0;
  const server = createServer(async (req, res) => {
    const json = (status, value) => { res.writeHead(status, { "content-type": "application/json" }); res.end(JSON.stringify({ ...value, service_environment: environment })); };
    if (req.url === "/status") return json(200, { server: "VFS_SERVER" });
    if (req.headers.authorization !== "Bearer test-secret") return json(401, { error: "unauthorized" });
    if (req.url === "/artifacts/raw" && req.method === "POST") {
      const chunks = []; for await (const chunk of req) chunks.push(chunk);
      content = Buffer.concat(chunks); digest = createHash("sha256").update(content).digest("hex");
      assert.equal(decodeURIComponent(req.headers["x-vfs-path"]), "/runtime/épreuve.bin");
      writes++;
      return json(201, { artifact: { digest }, actor_receipt: { kind: "VFS_ARTIFACT_WRITE" }, verification: "PENDING_OBSERVER_READBACK" });
    }
    if (req.url === "/artifacts/" + digest + "/raw") {
      res.writeHead(200, { "content-type": "application/octet-stream", "content-length": content.length,
        "x-content-sha256": digest, "x-keddeh-service": "KEDDEH_SERVICE",
        "x-keddeh-carrier-id": environment.carrier_id });return res.end(content);
    }
    if (req.url === "/verify" && req.method === "POST") {
      verifications++;return json(200, { verified: true, artifact: { digest }, receipt: { kind: "OBSERVER_VFS_READBACK" } });
    }
    return json(404, { error: "not_found" });
  });
  await new Promise(resolve => server.listen(0, "127.0.0.1", resolve));
  try {
    const endpoint = "http://127.0.0.1:" + server.address().port;
    const client = new KeddehVFSClient({ endpoint, bearer: () => "test-secret", carrierId: environment.carrier_id });
    assert.equal((await client.status()).service_environment.classification, "KEDDEH_SERVICE");
    const result = await client.commit({ path: "/runtime/épreuve.bin",
      bytes: new Uint8Array([0, 1, 2, 255]), source: "KEX browser carrier" });
    assert.equal(result.digest, digest);
    assert.equal(result.actorReceipt.kind, "VFS_ARTIFACT_WRITE");
    assert.equal(result.observerReceipt.kind, "OBSERVER_VFS_READBACK");
    assert.equal(writes, 1);assert.equal(verifications, 1);
  } finally { await new Promise(resolve => server.close(resolve)); }
});

test("service identity mismatch stops the carrier before accepting status", async () => {
  const server=createServer((_req,res)=>{res.writeHead(200,{"content-type":"application/json"});
    res.end(JSON.stringify({service_environment:{...environment,classification:"UNKNOWN"}}));});
  await new Promise(resolve => server.listen(0,"127.0.0.1",resolve));
  try {
    const client=new KeddehVFSClient({endpoint:"http://127.0.0.1:"+server.address().port});
    await assert.rejects(client.status(),/KEDDEH_SERVICE_IDENTITY_MISMATCH/);
  } finally {await new Promise(resolve=>server.close(resolve));}
});
