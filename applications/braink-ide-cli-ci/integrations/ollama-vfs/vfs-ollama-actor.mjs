/** Uses the existing VFSPrimitive interface; placement IDs are supplied by native runtime. */
export function createVfsOllamaActor({vfs, inodeId, fetchImpl = fetch}) {
  async function resolve() {
    const inode = await vfs.read(inodeId);
    const binding = inode.data;
    if (!binding || binding.provider !== 'ollama' || !binding.endpoint) throw new Error('Ollama actor binding absent');
    return {inode, binding};
  }
  async function invoke(operation, payload, execution) {
    const {binding} = await resolve();
    // The execution identity comes from the native dispatcher, never from model output.
    if (!execution?.requestInodeId) throw new Error('Native execution request inode required');
    const request = {actor_inode:inodeId, operation, payload, execution};
    await vfs.create(execution.requestInodeId, {path:execution.requestPath}, request);
    const retained = await vfs.read(execution.requestInodeId);
    if (JSON.stringify(retained.data) !== JSON.stringify(request)) throw new Error('Execution request readback mismatch');
    const endpoint = new URL(operation === 'inventory' ? '/api/tags' : '/api/chat', binding.endpoint);
    if (!['http:', 'https:'].includes(endpoint.protocol)) throw new Error('Unsupported runtime transport');
    let upstream;
    try {
      upstream = await fetchImpl(endpoint, {method:operation === 'inventory' ? 'GET' : 'POST',
        ...(operation === 'inventory' ? {} : {headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)}),
        signal:execution.signal});
    } catch (error) {
      await vfs.update(execution.requestInodeId, {path:execution.requestPath}, {...request, observation:{state:operation === 'inventory' ? 'UNREACHABLE' : 'OUTCOME_UNKNOWN'}});
      throw error;
    }
    await vfs.update(execution.requestInodeId, {path:execution.requestPath}, {...request, observation:{state:'HTTP_RESPONSE_OBSERVED',http_status:upstream.status}});
    // Response headers do not establish completed inference; stream remains owned by caller.
    return upstream;
  }
  return {resolve, inventory:execution=>invoke('inventory',undefined,execution), chat:(payload,execution)=>invoke('chat',payload,execution)};
}
