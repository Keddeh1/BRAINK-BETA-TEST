"""Small browser workspace for this node; edits share CLI artifacts and ledger."""
import hmac
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from .canonical import sha256_hex
from .indexer import ledger_index
from .ingest import iter_files, _read_bytes, store_artifact_bytes
from .pass_runner import run_dekstop_pass
from .plan import PlanningPacket
from .storage import atomic_write


MAX_EDIT_BYTES = 1_000_000


def workspace_file(root: Path, relative: str, excluded_roots=()) -> Path:
    part = Path(relative)
    if not relative or part.is_absolute() or any(x in {"..", "."} or x.startswith(".") for x in part.parts):
        raise ValueError("File path must be a visible relative workspace path")
    path = root
    for component in part.parts:
        path /= component
        if path.is_symlink():
            raise ValueError("Symbolic links cannot be edited")
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("File path escapes workspace")
    for excluded in excluded_roots:
        ex = Path(excluded).resolve()
        if resolved == ex or resolved.is_relative_to(ex):
            raise ValueError("Node state cannot be edited through the workspace")
    return path


def make_server(*, paths, store, artifacts_dir, host="127.0.0.1", port=8765, token=None):
    token = token if token is not None else os.getenv("BRAINK_NODE_TOKEN", "")
    if host not in {"127.0.0.1", "localhost", "::1"} and len(token) < 32:
        raise ValueError("Remote IDE binding requires BRAINK_NODE_TOKEN with at least 32 characters")
    lock = threading.Lock()
    exclusions = (artifacts_dir, store.path, Path(str(store.path) + "-journal"))

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format, *args):
            # Do not log URLs, headers, file contents or tokens.
            pass

        def reply(self, code, obj, content_type="application/json"):
            data = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(data)

        def authorize(self):
            if token:
                return hmac.compare_digest(self.headers.get("Authorization", ""), f"Bearer {token}")
            host_header = self.headers.get("Host", "").split(":")[0]
            return host_header in {"127.0.0.1", "localhost"}

        def do_GET(self):
            url = urlparse(self.path)
            if url.path == "/health":
                return self.reply(200, {"ok": True, "node": "braink-ide-cli-ci", "version": "0.1.0"})
            if url.path == "/":
                return self.reply(200, files("braink_node").joinpath("static/index.html").read_bytes(), "text/html; charset=utf-8")
            if not self.authorize():
                return self.reply(401, {"error": "Authorization required"})
            try:
                if url.path == "/api/files":
                    result = [str(p.relative_to(paths.root)) for p in iter_files(
                        paths.root, excluded_roots=exclusions)]
                    return self.reply(200, {"files": result})
                if url.path == "/api/file":
                    relative = parse_qs(url.query).get("path", [""])[0]
                    path = workspace_file(paths.root, relative, exclusions)
                    data = _read_bytes(path, MAX_EDIT_BYTES)
                    return self.reply(200, {"path": relative, "content": data.decode("utf-8"),
                                             "revision": sha256_hex(data)})
                if url.path == "/api/ledger":
                    return self.reply(200, store.verify())
                return self.reply(404, {"error": "Unknown route"})
            except (ValueError, OSError, UnicodeError) as error:
                return self.reply(400, {"error": str(error)})

        def do_POST(self):
            if not self.authorize():
                return self.reply(401, {"error": "Authorization required"})
            if self.headers.get("Content-Type") != "application/json":
                return self.reply(415, {"error": "Send application/json"})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length < 0 or length > MAX_EDIT_BYTES * 6 + 4096:
                    return self.reply(413, {"error": "Request exceeds edit limit"})
                obj = json.loads(self.rfile.read(length))
                if not isinstance(obj, dict):
                    raise ValueError("Request must be an object")
                with lock:
                    route = urlparse(self.path).path
                    if route == "/api/file":
                        path = workspace_file(paths.root, obj.get("path", ""), exclusions)
                        content = obj.get("content")
                        if not isinstance(content, str):
                            raise ValueError("content must be text")
                        data = content.encode("utf-8")
                        if len(data) > MAX_EDIT_BYTES:
                            return self.reply(413, {"error": "File exceeds edit limit"})
                        before = _read_bytes(path, MAX_EDIT_BYTES) if path.exists() else None
                        revision = sha256_hex(before) if before is not None else None
                        if obj.get("revision") != revision:
                            return self.reply(409, {"error": "File changed; reload before saving"})
                        refs = []
                        for source in (before, data):
                            if source is not None:
                                ref = sha256_hex(source)
                                store_artifact_bytes(artifacts_dir=artifacts_dir, artifact_ref=ref, data=source)
                                refs.append(ref)
                        packet = PlanningPacket("braink-node/edit", {"path": obj["path"]},
                                                [{"artifact_ref": ref} for ref in refs], [], [])
                        store.append(event_type="braink.node.edit.planned", route="braink-node/ide", payload=packet.to_obj())
                        atomic_write(path, data)
                        ref = store.append(event_type="braink.node.file.saved", route="braink-node/ide",
                                           payload={"path": obj["path"], "before_ref": revision,
                                                    "artifact_ref": sha256_hex(data)})
                        return self.reply(200, {"ok": True, "revision": sha256_hex(data), "event_ref": ref})
                    if route == "/api/check":
                        result = run_dekstop_pass(store=store, dekstop=paths, artifacts_dir=artifacts_dir,
                                                  pass_route="braink-node/ide/check")
                        result["ok"] = not any(x["severity"] == "blocker" for x in result["findings"])
                        return self.reply(200, result)
                    if route == "/api/index":
                        return self.reply(200, ledger_index(store=store, dekstop_root=paths.root,
                                           artifacts_dir=artifacts_dir, route="braink-node/ide/index"))
                    return self.reply(404, {"error": "Unknown route"})
            except (ValueError, OSError, UnicodeError, TypeError) as error:
                return self.reply(400, {"error": str(error)})

    return ThreadingHTTPServer((host, port), Handler)


def serve(**kwargs):
    server = make_server(**kwargs)
    print(json.dumps({"node": "braink-ide-cli-ci", "listen": list(server.server_address)}), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
