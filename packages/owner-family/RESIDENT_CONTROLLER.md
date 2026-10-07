# Complete owner-family controller deployment

The resident controller packages the qualified wheel, unchanged frozen dependency
versions and hashes, Node, Python and the Docker client into an owner-operated
image. Official Python and Node base images are pinned by digest. Dependency
wheels are read from `uv.lock`, downloaded with TLS and verified against the lock's
SHA-256. Package installation and image building run without build network access.

Build from a successful qualification:

```sh
python scripts/build_resident_image.py --qualification /path/to/qualification --output /path/to/image-context
```

The image context contains exact dependencies, Dockerfile and `CONTROLLER_IMAGE.json`.
Preserve its content-addressed image ID on the current host. For another host,
build and qualify there; a local image ID is not a published image registry.

Copy the admitted image metadata into the family's `.keddeh` directory and launch:

```sh
python scripts/launch_resident_controller.py --manifest /path/to/repository/.keddeh/family.json
```

The launcher preserves keys, cursor, agreement, disconnect, phase, journals and
application state. It refuses a root outside the admitted deployment space or a
foreign owner label. Only its exact named owned container can be replaced during
an image upgrade. It waits for ten healthy host workstations, completed boot and
matching qualified source digest. Existing boot leases are retained on restart.

Each controller uses Docker `unless-stopped`, read-only image and package mounts,
private writable runtime state, 1 GiB memory, one CPU, 256 PIDs, dropped capabilities,
no-new-privileges and a bounded temporary filesystem. A named UID 1000 account
supports the supplied host agent's home-directory lookup without changing HOME.
The separate domain containers retain their dual-network boundaries and smaller
resource policy. The controller uses host networking to preserve existing local
service ports and the authenticated VFS binding.

## Authority and user-space boundaries

The controller is a trusted **owner orchestrator**: its mounted Docker socket
permits host-level Docker operations. Resource flags do not make that authority a
security sandbox. Do not run customer or untrusted tenant code inside it. Owner
runtime credentials, operational agreements and customer registration records
remain separate. No Docker socket is exposed through the public frontage.

Off-site deployment requires a host, scoped credentials, transfer agreement,
network fence and independent readiness checks. The current account bindings do
not provide a usable off-site deployment target. A same-host resident container
is not an off-site security boundary. Software disconnect fences new gateway and
bilateral admissions; it does not firewall a host or revoke already committed work.

A deliberately stopped controller remains stopped. An unexpected controller exit
is restarted by Docker. Cloud task completion no longer requires the task's Python
process to supervise an admitted resident controller, provided the underlying Docker
host and retained mounts remain available. Host loss, daemon loss and mount loss
still require infrastructure recovery; no cloud-provider durability SLA is claimed.

## Qualification

Run the installed-image suite and owner integration checks, then inject one
unexpected controller process exit. Confirm a new host PID, Docker restart count,
healthy workstations, retained boot identity, advancing bilateral cycle and
unchanged disconnect/agreement records. Recheck exact wheel and VFS mirrored bundle
bytes for all nine families. Record actual results separately from this procedure.
