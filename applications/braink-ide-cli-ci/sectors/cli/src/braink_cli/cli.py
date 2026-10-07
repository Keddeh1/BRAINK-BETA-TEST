"""The independent node's command entry point."""
import argparse
import json
import os
import threading
from dataclasses import asdict
from pathlib import Path

from braink_node.align import align_project_into_dekstop
from braink_node.indexer import ledger_index
from braink_node.ingest import ingest_directory, ingest_file
from braink_node.ledger import LedgerStore
from braink_node.paths import default_dekstop_paths
from braink_node.pass_runner import run_dekstop_pass
from braink_node.registry import store_registry
from braink_node.result import ExecutionResult
from braink_node.storage import atomic_write


def services(workspace: Path, state_dir: Path):
    paths = default_dekstop_paths(workspace)
    state = state_dir.resolve()
    if state == paths.root:
        raise ValueError("State directory must differ from workspace root")
    return paths, LedgerStore(state / "ledger.sqlite3"), state / "artifacts"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="braink-node")
    parser.add_argument("--workspace", type=Path, default=Path(os.getenv("BRAINK_WORKSPACE", "./workspace")))
    parser.add_argument("--state-dir", type=Path, default=Path(os.getenv("BRAINK_STATE_DIR", "./.braink-node")))
    subs = parser.add_subparsers(dest="command", required=True)
    subs.add_parser("init")
    align = subs.add_parser("align")
    align.add_argument("path", type=Path)
    align.add_argument("--name", required=True)
    align.add_argument("--kind", default="python")
    index = subs.add_parser("index")
    index.add_argument("--max-entries", type=int, default=5000)
    ingest = subs.add_parser("ingest")
    ingest.add_argument("path", type=Path)
    ingest.add_argument("--max-files", type=int, default=2000)
    ingest.add_argument("--offset", type=int, default=0)
    ingest.add_argument("--max-bytes", type=int, default=8_000_000)
    check = subs.add_parser("check")
    check.add_argument("--ingest", action="store_true")
    check.add_argument("--fail-on", choices=("warn", "blocker"), default="blocker")
    subs.add_parser("verify-ledger")
    protocol = subs.add_parser("protocol")
    protocol.add_argument("action", choices=("catalogue", "deploy", "mesh"))
    protocol.add_argument("--source", type=Path)
    protocol.add_argument("--sector", choices=("core", "cli", "ide", "ci", "all"), default="all")
    protocol.add_argument("--vfs-url", default="http://127.0.0.1:17887")
    protocol.add_argument("--vfs-token-file", type=Path)
    protocol.add_argument("--mesh-url", default="http://127.0.0.1:8766")
    protocol.add_argument("--mesh-token-file", type=Path)
    protocol.add_argument("--owner-export", type=Path)
    protocol.add_argument("--port", type=int, default=8766)
    ci = subs.add_parser("ci")
    ci.add_argument("action", choices=("run", "submit", "list", "show", "worker", "relay"))
    ci.add_argument("--source", type=Path)
    ci.add_argument("--pipeline", type=Path)
    ci.add_argument("--job")
    ci.add_argument("--sector", choices=("core", "cli", "ide", "ci", "all"), default="all")
    ci.add_argument("--website", default=os.getenv("BRAINK_CI_WEBSITE", "https://www.keddeh.com"))
    serve = subs.add_parser("serve")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=int(os.getenv("PORT", "8765")))
    args = parser.parse_args(argv)
    try:
        paths, store, artifacts = services(args.workspace, args.state_dir)
        if args.command == "init":
            paths.root.mkdir(parents=True, exist_ok=True)
            (paths.root / "projects").mkdir(exist_ok=True)
            if not paths.unified_project_registry_json.exists():
                store_registry(paths.unified_project_registry_json, {"projects": []})
            if not paths.interconnect_status_json.exists():
                atomic_write(paths.interconnect_status_json, b'{"node":"braink-ide-cli-ci","status":"ready"}\n')
            result = {"workspace": str(paths.root), "state_dir": str(args.state_dir.resolve())}
        elif args.command == "align":
            result = asdict(align_project_into_dekstop(store=store, dekstop=paths,
                            project_name=args.name, project_path=args.path, kind=args.kind))
        elif args.command == "index":
            result = ledger_index(store=store, dekstop_root=paths.root, artifacts_dir=artifacts,
                                   route="braink-node/index", max_entries=args.max_entries)
        elif args.command == "ingest":
            if args.path.is_dir():
                result = ingest_directory(store=store, directory=args.path, artifacts_dir=artifacts,
                         route="braink-node/ingest", max_files=args.max_files, offset=args.offset,
                         max_artifact_bytes=args.max_bytes)
            else:
                result = ingest_file(store=store, file_path=args.path, artifacts_dir=artifacts,
                                      route="braink-node/ingest", max_artifact_bytes=args.max_bytes)
        elif args.command == "check":
            result = run_dekstop_pass(store=store, dekstop=paths, artifacts_dir=artifacts,
                                       pass_route="braink-node/check", ingest_dekstop_root=args.ingest)
            failures = {"blocker", "warn"} if args.fail_on == "warn" else {"blocker"}
            ok = not any(f["severity"] in failures for f in result["findings"])
            print(json.dumps(ExecutionResult(ok, None if ok else "Findings exceed threshold",
                                             result, [result["event_ref"]]).to_obj(), indent=2))
            return 0 if ok else 1
        elif args.command == "protocol":
            from braink_node.protocol import compile_catalogue, InstanceManager
            from braink_node.protocol.transport import JSONTransport, HubSubscription
            if args.action == "mesh":
                from braink_node.protocol.mesh import MeshStore, mesh_server, owner_state
                if args.owner_export is None or args.mesh_token_file is None:
                    raise ValueError("Mesh requires the owner export implementation and credential file")
                mesh = MeshStore(args.state_dir / "protocol-mesh", owner_state(args.owner_export))
                mesh_server(mesh, "127.0.0.1", args.port, args.mesh_token_file.read_text().strip()).serve_forever()
                return 0
            if args.source is None:
                raise ValueError("Protocol requires --source")
            catalogue = compile_catalogue(args.source)
            if args.action == "catalogue":
                result = catalogue
            else:
                if args.vfs_token_file is None or args.mesh_token_file is None:
                    raise ValueError("Deploy requires existing VFS and mesh credential files")
                hub = HubSubscription(JSONTransport(args.vfs_url, args.vfs_token_file.read_text().strip()))
                mesh = JSONTransport(args.mesh_url, args.mesh_token_file.read_text().strip())
                result = InstanceManager(args.state_dir / "instances", hub, mesh).deploy(
                    catalogue, ("core", "cli", "ide", "ci") if args.sector == "all" else (args.sector,))
        elif args.command == "ci":
            from braink_ci.runner import CIRunner, sector_pipeline
            runner = CIRunner(args.state_dir / "ci", store)
            if args.action in {"run", "submit"}:
                if args.source is None:
                    raise ValueError("CI run/submit requires --source")
                pipeline = json.loads(args.pipeline.read_text()) if args.pipeline else sector_pipeline(args.sector)
                queued = runner.submit(args.source, pipeline)
                if args.action == "submit":
                    result = queued
                else:
                    while runner.get(queued["id"])["status"] == "queued":
                        runner.execute_next()
                    result = runner.get(queued["id"])
                    print(json.dumps(result, indent=2))
                    return 0 if result["status"] == "passed" else 1
            elif args.action == "list":
                result = runner.list()
            elif args.action == "show":
                result = runner.get(args.job)
            elif args.action == "worker":
                try:
                    runner.worker(threading.Event())
                except KeyboardInterrupt:
                    pass
                return 0
            else:
                if args.source is None:
                    raise ValueError("CI relay requires --source")
                from braink_ci.relay import WebsiteRelay
                WebsiteRelay(runner, args.source, args.website).serve()
                return 0
        elif args.command == "verify-ledger":
            result = store.verify()
        else:
            from braink_ide.ide import serve
            serve(paths=paths, store=store, artifacts_dir=artifacts, host=args.host, port=args.port)
            return 0
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "reason": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
