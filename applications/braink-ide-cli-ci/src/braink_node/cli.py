"""The independent node's command entry point."""
import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path

from .align import align_project_into_dekstop
from .indexer import ledger_index
from .ingest import ingest_directory, ingest_file
from .ledger import LedgerStore
from .paths import default_dekstop_paths
from .pass_runner import run_dekstop_pass
from .registry import store_registry
from .result import ExecutionResult
from .storage import atomic_write


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
        elif args.command == "verify-ledger":
            result = store.verify()
        else:
            from .ide import serve
            serve(paths=paths, store=store, artifacts_dir=artifacts, host=args.host, port=args.port)
            return 0
        print(json.dumps(result, indent=2))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "reason": str(error)}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
