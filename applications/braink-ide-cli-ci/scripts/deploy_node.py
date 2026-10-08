"""Install the four sector wheels and start this independent node on a Linux host.

Run with --runtime-root outside Git. The IDE binds to loopback by default.
The node survives the deploying command, but needs a host supervisor for reboot.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import venv


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    root = args.runtime_root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    pid_file = root / "node.pid"
    if pid_file.exists():
        pid = int(pid_file.read_text())
        cmdline = Path(f"/proc/{pid}/cmdline")
        if cmdline.exists() and b"braink_cli.cli" in cmdline.read_bytes():
            raise SystemExit("Node already running; use its current service before redeploying")
    # Avoid starting on a port used by another application.
    import socket
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", args.port))
    venv.create(root / "venv", with_pip=True)
    python = root / "venv/bin/python"
    subprocess.run([str(python), "-m", "pip", "install", "--no-deps", *[str(p.resolve()) for p in args.artifacts_dir.glob("*/*.whl")]], check=True)
    common = [str(python), "-m", "braink_cli.cli", "--workspace", str(root / "workspace"),
              "--state-dir", str(root / "state")]
    subprocess.run(common + ["init"], check=True)
    with (root / "node.log").open("ab") as log:
        process = subprocess.Popen(common + ["serve", "--port", str(args.port)],
                                    stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                    start_new_session=True)
    pid_file.write_text(str(process.pid))
    try:
        for _ in range(50):
            if process.poll() is not None:
                raise RuntimeError("Node failed to start; inspect node.log")
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{args.port}/health", timeout=1) as response:
                    health = json.load(response)
                    if response.status == 200 and health.get("node") == "braink-ide-cli-ci":
                        result = {"node": health["node"], "health": health,
                                  "runtime_root": str(root), "pid": process.pid,
                                  "url": f"http://127.0.0.1:{args.port}",
                                  "scope": "private cloud-host process; no public ingress or reboot supervisor"}
                        (root / "deployment.json").write_text(json.dumps(result, indent=2))
                        print(json.dumps(result, indent=2))
                        return
            except OSError:
                pass
            time.sleep(0.1)
        raise RuntimeError("Node health check timed out")
    except Exception:
        process.terminate()
        process.wait(timeout=10)
        pid_file.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    main()
