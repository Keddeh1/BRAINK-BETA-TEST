/** Transport only: native identity, VFS and mesh custody remain with the caller. */
export function registerOllamaRoutes(app, {baseURL = process.env.OLLAMA_URL || process.env.VITE_OLLAMA_URL || 'http://127.0.0.1:11434', fetchImpl = fetch} = {}) {
  const base = new URL(baseURL);
  if (!['http:', 'https:'].includes(base.protocol)) throw new Error('Invalid Ollama transport');
  async function forward(req, res, path, mutation) {
    try {
      const upstream = await fetchImpl(new URL(path, base), {
        method: mutation ? 'POST' : 'GET',
        headers: mutation ? {'Content-Type':'application/json'} : {},
        ...(mutation ? {body:JSON.stringify(req.body)} : {}),
        signal: AbortSignal.timeout(mutation ? 300000 : 10000)
      });
      res.status(upstream.status);
      res.setHeader('Content-Type', upstream.headers.get('content-type') || 'application/json');
      if (!upstream.body) return res.end();
      const reader = upstream.body.getReader();
      res.on?.('close', () => { void reader.cancel().catch(() => {}); });
      try {
        while (true) {
          const {done,value} = await reader.read();
          if (done) break;
          if (!res.write(Buffer.from(value))) await new Promise(resolve => res.once('drain',resolve));
        }
        res.end();
      } finally { reader.releaseLock(); }
    } catch {
      if (res.headersSent) { res.destroy(); return; }
      res.status(503).json({error: mutation ? 'OLLAMA_OUTCOME_UNKNOWN' : 'OLLAMA_UNREACHABLE', provider:'ollama'});
    }
  }
  app.get('/api/ollama/tags', (req,res) => forward(req,res,'/api/tags',false));
  app.post('/api/ollama/chat', (req,res) => forward(req,res,'/api/chat',true));
}
