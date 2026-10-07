const MAX_BYTES = 64 * 1024 * 1024;
const hex = bytes => [...new Uint8Array(bytes)].map(value => value.toString(16).padStart(2, "0")).join("");
async function digest(bytes) { return hex(await crypto.subtle.digest("SHA-256", bytes)); }

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
  async request(path, { method = "GET", body, headers = {} } = {}) {
    const token = typeof this.bearer === "function" ? await this.bearer() : this.bearer;
    const response = await this.transport(this.endpoint + path, {
      method, headers: { ...(token ? { Authorization: "Bearer " + token } : {}), ...headers },
      ...(body === undefined ? {} : { body })
    });
    if (!response.ok) throw new Error("VFS_HTTP_" + response.status);
    return response;
  }
  async status() {
    const data = await (await this.request("/status")).json();
    this.assertService(data);
    return data;
  }
  async commit({ path, bytes, source, predecessor, mediaType = "application/octet-stream" }) {
    if (!(bytes instanceof Uint8Array) || bytes.byteLength > MAX_BYTES || !path || !source)
      throw new Error("VFS_COMMIT_INPUT_INVALID");
    const expected = await digest(bytes);
    const headers = { "content-type": mediaType, "x-vfs-path": encodeURIComponent(path), "x-vfs-source": encodeURIComponent(source) };
    if (predecessor) headers["x-vfs-predecessor"] = predecessor;
    const created = await (await this.request("/artifacts/raw", { method: "POST", body: bytes, headers })).json();
    const env = this.assertService(created);
    if (created.artifact?.digest !== expected || created.actor_receipt?.kind !== "VFS_ARTIFACT_WRITE" ||
        created.verification !== "PENDING_OBSERVER_READBACK") throw new Error("VFS_ACTOR_MISMATCH");
    const read = await this.request("/artifacts/" + expected + "/raw");
    if (read.headers.get("x-keddeh-service") !== "KEDDEH_SERVICE" ||
        read.headers.get("x-content-sha256") !== expected ||
        (this.carrierId && read.headers.get("x-keddeh-carrier-id") !== this.carrierId))
      throw new Error("VFS_READBACK_IDENTITY_MISMATCH");
    const observed = new Uint8Array(await read.arrayBuffer());
    if (observed.byteLength !== bytes.byteLength || await digest(observed) !== expected)
      throw new Error("VFS_CONTENT_READBACK_MISMATCH");
    const verified = await (await this.request("/verify", {
      method: "POST", body: JSON.stringify({ digest: expected }),
      headers: { "content-type": "application/json" }
    })).json();
    this.assertService(verified);
    if (verified.verified !== true || verified.receipt?.kind !== "OBSERVER_VFS_READBACK" ||
        verified.artifact?.digest !== expected) throw new Error("VFS_OBSERVER_MISMATCH");
    return Object.freeze({ digest: expected, actorReceipt: created.actor_receipt,
      observerReceipt: verified.receipt, serviceEnvironment: env });
  }
}
