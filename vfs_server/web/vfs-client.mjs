const MAX_SIDE_BYTES = 32 * 1024 * 1024;
const hex = bytes => [...new Uint8Array(bytes)].map(value => value.toString(16).padStart(2, "0")).join("");
const digest = async bytes => hex(await crypto.subtle.digest("SHA-256", bytes));
const ident = value => /^[0-9a-f]{32}$/.test(value);
function encode(bytes) {
  let text = "";
  for (let i = 0; i < bytes.length; i += 16384)
    text += String.fromCharCode(...bytes.subarray(i, i + 16384));
  return btoa(text);
}
function decode(value) {
  const text = atob(value), bytes = new Uint8Array(text.length);
  for (let i = 0; i < text.length; i++) bytes[i] = text.charCodeAt(i);
  return bytes;
}
export class KeddehVFSClient {
  constructor({ endpoint, bearer, carrierId, transport = fetch }) {
    const url = new URL(endpoint);
    if (url.protocol !== "https:" && !(url.protocol === "http:" && ["127.0.0.1", "localhost", "[::1]"].includes(url.hostname)))
      throw new Error("VFS_TRANSPORT_NOT_ALLOWED");
    this.endpoint = url.origin;
    this.bearer = bearer;
    this.carrierId = carrierId;
    this.transport = transport;
  }
  assertService(value) {
    const env = value?.service_environment;
    if (env?.classification !== "KEDDEH_SERVICE" || env.system !== "KEDDEH_SYSTEMS" ||
        env.subsystem !== "VFS_SERVER" || (this.carrierId && env.carrier_id !== this.carrierId))
      throw new Error("KEDDEH_SERVICE_IDENTITY_MISMATCH");
    return env;
  }
  async request(path, { method = "GET", body } = {}) {
    const token = typeof this.bearer === "function" ? await this.bearer() : this.bearer;
    const response = await this.transport(this.endpoint + path, {
      method, headers: { ...(token ? { Authorization: "Bearer " + token } : {}),
        ...(body === undefined ? {} : { "content-type": "application/json" }) },
      ...(body === undefined ? {} : { body: JSON.stringify(body) })
    });
    if (!response.ok) throw new Error("VFS_HTTP_" + response.status);
    const data = await response.json();
    this.assertService(data);
    return data;
  }
  status() { return this.request("/status"); }
  allocations() { return this.request("/vfs"); }
  async allocate({ label, sourceRef, quotaBytes }) {
    if (!label || !sourceRef) throw new Error("VFS_ALLOCATION_INPUT_INVALID");
    const data = await this.request("/vfs", { method: "POST",
      body: { label, source_ref: sourceRef, ...(quotaBytes === undefined ? {} : { quota_bytes: quotaBytes }) } });
    if (!ident(data.allocation?.vfs_id) || data.allocation.source_ref !== sourceRef)
      throw new Error("VFS_ALLOCATION_MISMATCH");
    return data.allocation;
  }
  async admitAB({ vfsId, a, b, sourceRef }) {
    if (!ident(vfsId) || !(a instanceof Uint8Array) || !(b instanceof Uint8Array) ||
        a.byteLength > MAX_SIDE_BYTES || b.byteLength > MAX_SIDE_BYTES || !sourceRef)
      throw new Error("VFS_AB_INPUT_INVALID");
    const [aDigest,bDigest] = await Promise.all([digest(a),digest(b)]);
    const created = await this.request("/vfs/" + vfsId + "/ab", { method: "POST",
      body: { a_b64: encode(a), b_b64: encode(b), source_ref: sourceRef } });
    const entry = created.entry;
    if (entry?.vfs_id !== vfsId || !ident(entry.entry_id) ||
        entry.a_digest !== aDigest || entry.b_digest !== bDigest ||
        created.verification !== "PENDING_OBSERVER_READBACK" || !created.actor_receipts?.length)
      throw new Error("VFS_AB_ACTOR_MISMATCH");
    const read = await this.request("/vfs/" + vfsId + "/ab/" + entry.entry_id);
    if (read.entry?.entry_id !== entry.entry_id ||
        await digest(decode(read.a_b64)) !== aDigest || await digest(decode(read.b_b64)) !== bDigest)
      throw new Error("VFS_AB_READBACK_MISMATCH");
    const observed = await this.request("/vfs/" + vfsId + "/ab/" + entry.entry_id + "/verify",
      { method: "POST", body: {} });
    if (observed.verified !== true || observed.entry?.entry_id !== entry.entry_id ||
        !observed.observer_receipts?.length ||
        await digest(decode(observed.a_b64)) !== aDigest ||
        await digest(decode(observed.b_b64)) !== bDigest)
      throw new Error("VFS_AB_OBSERVER_MISMATCH");
    return Object.freeze({ allocationId: vfsId, entry, actorReceipts: created.actor_receipts,
      observerReceipts: observed.observer_receipts, compression: observed.compression,
      serviceEnvironment: observed.service_environment });
  }
  async allocateAndAdmit({ label, sourceRef, a, b, quotaBytes }) {
    const allocation = await this.allocate({ label, sourceRef, quotaBytes });
    const admission = await this.admitAB({ vfsId: allocation.vfs_id, a, b, sourceRef });
    return Object.freeze({ allocation, admission });
  }
}
