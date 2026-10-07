# Source API inventory

This catalog records each source function/method and its actual signature, source line and call relationships. Supported owner journeys are documented separately in action/process contracts; internal methods are implementation interfaces.

## _web4_exec.main

`()`

Apply actual Linux process file bounds before executing an owner package.

Source: `src/keddeh_namespace/_web4_exec.py:7`. Calls: `SystemExit`, `len`, `os.execvpe`, `resource.setrlimit`.

## bilateral_runtime.BilateralRuntime.__init__

`(self, controller)`

Durable bidirectional workstation-to-R36 execution loop.

Source: `src/keddeh_namespace/bilateral_runtime.py:10`. Calls: `json.loads`, `self.path.exists`, `self.path.read_text`, `threading.RLock`.

## bilateral_runtime.BilateralRuntime.save

`(self)`

Durable bidirectional workstation-to-R36 execution loop.

Source: `src/keddeh_namespace/bilateral_runtime.py:19`. Calls: `write_json`.

## bilateral_runtime.BilateralRuntime.configure

`(self, enabled)`

Durable bidirectional workstation-to-R36 execution loop.

Source: `src/keddeh_namespace/bilateral_runtime.py:23`. Calls: `ValueError`, `dict`, `self.save`, `type`.

## bilateral_runtime.BilateralRuntime.tick

`(self)`

Durable bidirectional workstation-to-R36 execution loop.

Source: `src/keddeh_namespace/bilateral_runtime.py:31`. Calls: `DynamicHealingAgent`, `RuntimeError`, `StochasticKuramotoPLL`, `actor.get`, `all`, `any`, `commands.append`, `d['live'].get`, `enumerate`, `float`, `hasattr`, `hashlib.sha256`, `hashlib.sha256(material).digest`, `healer.resolve_drift`, `http_json`, `int.from_bytes`, `json.dumps`, `json.dumps({'left': left, 'right': peer, 'domain_feedback': domain_feedback, 'returned': returned, 'owner_phase': self.data['phase']['theta'][i], 'owner_healing': healer.resolve_drift([float(not left['ok']), float(not peer['ok'])])}, sort_keys=True).encode`, `len`, `np.array`, `observed['services'].values`, `pending['actors'].append`, `pll.omega.tolist`, `pll.step`, `pll.theta.tolist`, `range`, `self.controller.domains.control`, `self.controller.receipt`, `self.controller.status`, `self.data.get`, `self.data.update`, `self.save`, `str`, `time.monotonic`, `type`, `urlencode`.

## bootstrap.read_private_artifact

`(root, path, *, max_bytes=1024 ** 2)`

Fail-closed preflight using authenticated gate bundles and measured prerequisites.

Source: `src/keddeh_namespace/bootstrap.py:21`. Calls: `Path`, `ValueError`, `current.is_symlink`, `len`, `logical_path`, `os.fdopen`, `os.fstat`, `os.open`, `stat.S_ISREG`, `stream.fileno`, `stream.read`.

## bootstrap.verify_gate_bundles

`(config, ledger, *, now=None)`

Fail-closed preflight using authenticated gate bundles and measured prerequisites.

Source: `src/keddeh_namespace/bootstrap.py:38`. Calls: `'; '.join`, `Path`, `Path(config['evidence_root']).resolve`, `ValueError`, `config.get`, `datetime.fromisoformat`, `datetime.fromisoformat(envelope['observed_at'].replace('Z', '+00:00')).timestamp`, `envelope['observed_at'].replace`, `envelope_digest`, `hashlib.sha256`, `hashlib.sha256(artifact).hexdigest`, `json.loads`, `len`, `read_private_artifact`, `seen.add`, `set`, `time.time`, `type`, `validate`, `verify_assessment`, `verify_chain`, `verify_observation`.

## bootstrap.preflight

`(config, ledger)`

Fail-closed preflight using authenticated gate bundles and measured prerequisites.

Source: `src/keddeh_namespace/bootstrap.py:74`. Calls: `Path`, `Path(config['archive_mount']).resolve`, `Path(node['vfs_mount']).resolve`, `ValueError`, `authority_probe`, `config.get`, `mounts.append`, `type`, `validate_nodes`, `verify_gate_bundles`, `verify_volume`, `volumes.append`, `zone_name`, `{'zone', 'nodes', 'evidence_root', 'trust_store', 'trusted_heads', 'archive_mount', 'dnskey_sha256'}.issubset`.

## bootstrap.main

`()`

Fail-closed preflight using authenticated gate bundles and measured prerequisites.

Source: `src/keddeh_namespace/bootstrap.py:94`. Calls: `argparse.ArgumentParser`, `json.dumps`, `json.load`, `open`, `parser.add_argument`, `parser.exit`, `parser.parse_args`, `preflight`, `print`.

## compile_zones.zone_name

`(value)`

Compile a complete custody inventory deterministically; no live DNS mutation.

Source: `src/keddeh_namespace/compile_zones.py:15`. Calls: `ValueError`, `any`, `dns.name.from_text`, `len`, `name.to_text`, `name.to_text().lower`, `re.fullmatch`, `type`.

## compile_zones.validate_nodes

`(config, zone)`

Compile a complete custody inventory deterministically; no live DNS mutation.

Source: `src/keddeh_namespace/compile_zones.py:23`. Calls: `ValueError`, `config.get`, `ipaddress.ip_address`, `len`, `name.endswith`, `node.get`, `result.append`, `str`, `type`, `zip`, `zone_name`, `{'role', 'name', 'public_ip'}.issubset`.

## compile_zones.compile_zone

`(inventory, config)`

Compile a complete custody inventory deterministically; no live DNS mutation.

Source: `src/keddeh_namespace/compile_zones.py:40`. Calls: `'\n'.join`, `ValueError`, `canonical_bytes`, `config.get`, `datetime.fromisoformat`, `dns.name.from_text`, `dns.rdata.from_text`, `dns.rdatatype.from_text`, `dns.zone.from_text`, `hashlib.sha256`, `hashlib.sha256(canonical_bytes(inventory)).hexdigest`, `hashlib.sha256(text.encode()).hexdigest`, `inventory['authority'].strip`, `inventory['captured_at'].replace`, `kind.upper`, `len`, `lines.append`, `owner.is_subdomain`, `owner.to_text`, `seen.add`, `set`, `sorted`, `text.encode`, `timestamp.utcoffset`, `type`, `validate_nodes`, `zone_name`.

## compile_zones.main

`()`

Compile a complete custody inventory deterministically; no live DNS mutation.

Source: `src/keddeh_namespace/compile_zones.py:83`. Calls: `argparse.ArgumentParser`, `compile_zone`, `json.dumps`, `json.load`, `open`, `parser.add_argument`, `parser.exit`, `parser.parse_args`, `prepare_authority_generation`, `print`, `stream.write`.

## compile_zones.prepare_authority_generation

`(inventory, config)`

Explicit staged authority change; retains every non-authority record.

This produces a reviewed desired zone, never mutates hosted DNS or delegation.

Source: `src/keddeh_namespace/compile_zones.py:100`. Calls: `ValueError`, `canonical_bytes`, `compile_zone`, `config.get`, `copy.deepcopy`, `dict`, `dns.name.from_text`, `dns.rdata.from_text`, `dns.serial.Serial`, `hashlib.sha256`, `hashlib.sha256(canonical_bytes(desired)).hexdigest`, `ipaddress.ip_address`, `owner.to_text`, `owner.to_text().lower`, `record['type'].upper`, `removed.append`, `retained.append`, `soa.rname.to_text`, `type`, `validate_nodes`, `zone_name`.

## domain_mesh.DomainMesh.__init__

`(self, controller)`

Owned recursive dual-network domains carrying owner workstation execution.

Source: `src/keddeh_namespace/domain_mesh.py:15`. Calls: `hashlib.sha256`, `hashlib.sha256(str(controller.root).encode()).hexdigest`, `json.loads`, `self.path.exists`, `self.path.read_text`, `self.root.mkdir`, `str`, `str(controller.root).encode`.

## domain_mesh.DomainMesh.run

`(self, *args)`

Owned recursive dual-network domains carrying owner workstation execution.

Source: `src/keddeh_namespace/domain_mesh.py:22`. Calls: `RuntimeError`, `p.stderr.strip`, `p.stdout.strip`, `subprocess.run`.

## domain_mesh.DomainMesh.save

`(self)`

Owned recursive dual-network domains carrying owner workstation execution.

Source: `src/keddeh_namespace/domain_mesh.py:26`. Calls: `write_json`.

## domain_mesh.DomainMesh.network

`(self, name)`

Owned recursive dual-network domains carrying owner workstation execution.

Source: `src/keddeh_namespace/domain_mesh.py:29`. Calls: `fcntl.flock`, `open`, `self._network_locked`.

## domain_mesh.DomainMesh._network_locked

`(self, name)`

Owned recursive dual-network domains carrying owner workstation execution.

Source: `src/keddeh_namespace/domain_mesh.py:33`. Calls: `RuntimeError`, `ValueError`, `any`, `c.get`, `ipaddress.ip_network`, `ipaddress.ip_network(f'10.240.{i}.0/24').overlaps`, `json.loads`, `n.get`, `n.get('IPAM', {}).get`, `next`, `obj.get`, `obj.get('Labels', {}).get`, `range`, `self.run`, `self.run('network', 'ls', '-q').split`, `str`.

## domain_mesh.DomainMesh.container

`(self, domain)`

Owned recursive dual-network domains carrying owner workstation execution.

Source: `src/keddeh_namespace/domain_mesh.py:45`. Calls: .

## domain_mesh.DomainMesh.spawn

`(self, parent=None)`

Owned recursive dual-network domains carrying owner workstation execution.

Source: `src/keddeh_namespace/domain_mesh.py:46`. Calls: `(code / 'bridge.mjs').read_bytes`, `(state / 'token').chmod`, `Path`, `Path(__file__).with_name`, `RuntimeError`, `ValueError`, `code.mkdir`, `directory.mkdir`, `hashlib.sha256`, `hashlib.sha256((code / 'bridge.mjs').read_bytes()).hexdigest`, `hashlib.sha256(owner.read_bytes()).hexdigest`, `len`, `owner.read_bytes`, `result.get`, `secrets.token_hex`, `self.container`, `self.create_domain`, `self.data['domains'].append`, `self.network`, `self.read`, `self.save`, `shutil.copyfile`, `state.mkdir`, `str`, `time.monotonic`, `time.sleep`, `token.chmod`, `token.exists`, `token.write_text`, `write_json`.

## domain_mesh.DomainMesh.create_domain

`(self, row)`

Owned recursive dual-network domains carrying owner workstation execution.

Source: `src/keddeh_namespace/domain_mesh.py:76`. Calls: `os.getgid`, `os.getuid`, `self.container`, `self.network`, `self.run`.

## domain_mesh.DomainMesh.read

`(self, ident)`

Owned recursive dual-network domains carrying owner workstation execution.

Source: `src/keddeh_namespace/domain_mesh.py:87`. Calls: `ValueError`, `json.loads`, `self.container`, `self.run`.

## domain_mesh.DomainMesh.resume

`(self)`

Owned recursive dual-network domains carrying owner workstation execution.

Source: `src/keddeh_namespace/domain_mesh.py:91`. Calls: `Path`, `Path(__file__).with_name`, `Path(__file__).with_name('web4_domain.mjs').read_bytes`, `ValueError`, `code.read_bytes`, `code.write_bytes`, `hashlib.sha256`, `hashlib.sha256(desired).hexdigest`, `info['Config']['Labels'].get`, `json.loads`, `self.container`, `self.create_domain`, `self.run`, `self.save`, `str`.

## domain_mesh.DomainMesh.reanchor

`(self, ident, parent)`

Owned recursive dual-network domains carrying owner workstation execution.

Source: `src/keddeh_namespace/domain_mesh.py:107`. Calls: `ValueError`, `row.update`, `self.container`, `self.run`, `self.save`, `write_json`.

## domain_mesh.DomainMesh.control

`(self, body)`

Owned recursive dual-network domains carrying owner workstation execution.

Source: `src/keddeh_namespace/domain_mesh.py:121`. Calls: `ValueError`, `body.get`, `result.append`, `self.read`, `self.reanchor`, `self.spawn`.

## envelope.canonical_bytes

`(value)`

Project encoding: sorted keys, UTF-8, no floats; not RFC 8785 JCS.

Source: `src/keddeh_namespace/envelope.py:14`. Calls: `ValueError`, `all`, `check`, `item.values`, `json.dumps`, `json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode`, `type`.

## envelope.content_root

`(kind, payload)`

Versioned canonical observation envelopes; hashes do not authenticate authors.

Source: `src/keddeh_namespace/envelope.py:33`. Calls: `ValueError`, `canonical_bytes`, `hashlib.sha256`, `hashlib.sha256(canonical_bytes({'schema': 'keddeh.root.v1', 'kind': kind, 'payload': payload})).hexdigest`.

## envelope.validate

`(envelope)`

Versioned canonical observation envelopes; hashes do not authenticate authors.

Source: `src/keddeh_namespace/envelope.py:40`. Calls: `DIGEST.fullmatch`, `ValueError`, `canonical_bytes`, `datetime.fromisoformat`, `envelope[field].strip`, `parsed.astimezone`, `parsed.astimezone(timezone.utc).isoformat`, `parsed.astimezone(timezone.utc).isoformat(timespec='microseconds').replace`, `parsed.utcoffset`, `set`, `timestamp.replace`, `type`.

## envelope.envelope_digest

`(envelope)`

Versioned canonical observation envelopes; hashes do not authenticate authors.

Source: `src/keddeh_namespace/envelope.py:72`. Calls: `canonical_bytes`, `hashlib.sha256`, `hashlib.sha256(canonical_bytes(envelope)).hexdigest`, `validate`.

## envelope.verify_chain

`(envelopes, *, trusted_head)`

Verify all links including genesis against an externally retained head digest.

A matching head provides integrity relative to that checkpoint, not signature
authentication or proof that the represented command actually ran.

Source: `src/keddeh_namespace/envelope.py:77`. Calls: `DIGEST.fullmatch`, `ValueError`, `envelope_digest`, `type`.

## evidence.validate

`(ledger)`

Return errors; no submitted assertion is executed or authenticated here.

Source: `src/keddeh_namespace/evidence.py:18`. Calls: `HASH.fullmatch`, `ValueError`, `datetime.fromisoformat`, `errors.append`, `isinstance`, `ledger.get`, `ledger[key].strip`, `receipt.get`, `receipt[key].strip`, `receipts.get`, `timestamp.utcoffset`.

## evidence.main

`()`

Check submitted ledger shape; live and cryptographic verification is external.

Source: `src/keddeh_namespace/evidence.py:65`. Calls: `'\n'.join`, `argparse.ArgumentParser`, `args.ledger.read_text`, `json.loads`, `parser.add_argument`, `parser.exit`, `parser.parse_args`, `print`, `validate`.

## frontage_service.make_server

`(source, root, port=0)`

Same-origin customer frontage with scoped live readbacks and durable consent.

Source: `src/keddeh_namespace/frontage_service.py:17`. Calls: `(root / 'launch.json').read_text`, `(root / 'state/token').read_text`, `(source / 'claims.json').read_text`, `(source / (path.lstrip('/') or 'index.html')).resolve`, `FrontageServer`, `Path`, `Path(source).resolve`, `ValueError`, `connect`, `data.get`, `data.get(key, '').strip`, `database.chmod`, `datetime.now`, `datetime.now(timezone.utc).isoformat`, `db.close`, `db.commit`, `db.execute`, `db.execute('SELECT receipt,digest FROM interests WHERE request_id=?', (stored['request_id'],)).fetchone`, `db.rollback`, `file.is_dir`, `file.is_file`, `file.is_relative_to`, `file.read_bytes`, `hashlib.sha256`, `hashlib.sha256(raw.encode()).hexdigest`, `http_json`, `initial.close`, `initial.execute`, `int`, `isinstance`, `json.dumps`, `json.dumps(data).encode`, `json.loads`, `len`, `live.get`, `mimetypes.guess_type`, `path.lstrip`, `path.split`, `rates.get`, `raw.encode`, `re.fullmatch`, `recent.append`, `secrets.token_hex`, `secrets.token_hex(12).upper`, `self.end_headers`, `self.headers.get`, `self.reply`, `self.rfile.read`, `self.send_header`, `self.send_response`, `self.wfile.write`, `sqlite3.connect`, `state.chmod`, `state.mkdir`, `str`, `time.monotonic`, `time.time`, `unquote`, `urlsplit`.

## frontage_service.main

`()`

Same-origin customer frontage with scoped live readbacks and durable consent.

Source: `src/keddeh_namespace/frontage_service.py:104`. Calls: `ap.add_argument`, `ap.parse_args`, `argparse.ArgumentParser`, `make_server`, `make_server(a.source, a.root, a.port).serve_forever`.

## genesis.validate_topology

`(participant, children)`

Bounded topology policy and signed challenge/readback on actual return sockets.

Source: `src/keddeh_namespace/genesis.py:11`. Calls: `ValueError`, `connection_id.strip`, `connection_ids.add`, `endpoints.add`, `host.strip`, `identities.add`, `identity.strip`, `len`, `participant.strip`, `set`, `type`.

## genesis.LeaseController.__init__

`(self, database, *, max_active=3, cooldown=30, max_lease=300)`

Bounded topology policy and signed challenge/readback on actual return sockets.

Source: `src/keddeh_namespace/genesis.py:37`. Calls: `ValueError`, `db.executescript`, `self.connect`, `type`.

## genesis.LeaseController.connect

`(self)`

Bounded topology policy and signed challenge/readback on actual return sockets.

Source: `src/keddeh_namespace/genesis.py:47`. Calls: `db.execute`, `sqlite3.connect`.

## genesis.LeaseController.admit

`(self, identity, nonce, *, seconds, now=None)`

Bounded topology policy and signed challenge/readback on actual return sockets.

Source: `src/keddeh_namespace/genesis.py:49`. Calls: `ValueError`, `db.execute`, `db.execute('SELECT 1 FROM leases WHERE identity=? AND expires>?', (identity, now)).fetchone`, `db.execute('SELECT 1 FROM nonces WHERE nonce=?', (nonce,)).fetchone`, `db.execute('SELECT COUNT(*) FROM leases WHERE expires>?', (now,)).fetchone`, `db.execute('SELECT last_spawn,frozen FROM state WHERE id=1').fetchone`, `identity.strip`, `int`, `nonce.strip`, `self.connect`, `time.time`, `type`.

## genesis.LeaseController.freeze

`(self)`

Bounded topology policy and signed challenge/readback on actual return sockets.

Source: `src/keddeh_namespace/genesis.py:67`. Calls: `db.execute`, `self.connect`.

## genesis.LeaseController.reanchor

`(self, verified_recovery)`

Bounded topology policy and signed challenge/readback on actual return sockets.

Source: `src/keddeh_namespace/genesis.py:69`. Calls: `ValueError`, `db.execute`, `self.connect`.

## genesis.probe_returns

`(participant, children, trust, *, timeout=3)`

Bounded topology policy and signed challenge/readback on actual return sockets.

Source: `src/keddeh_namespace/genesis.py:74`. Calls: `ValueError`, `canonical_bytes`, `data.endswith`, `json.loads`, `len`, `list`, `min`, `receipts.append`, `resolved.add`, `secrets.token_hex`, `set`, `socket.create_connection`, `stream.getpeername`, `stream.recv`, `stream.sendall`, `validate_topology`, `verify_observation`.

## hci_contract.KEDDEHHCIContract.__init__

`(self, project_name, secure_context=True)`

Operational adapter of the owner's Shared KEDDEH HCI contract.

Source: owner upload SHA256 recorded in docs/OWNER_ENVIRONMENT.md.
Supplied layout's fixed hardware/quorum assertions are replaced by readbacks.

Source: `src/keddeh_namespace/hci_contract.py:8`. Calls: `project_name.upper`.

## hci_contract.KEDDEHHCIContract.render_iso_compliant_header

`(self, contextual_action_label)`

Operational adapter of the owner's Shared KEDDEH HCI contract.

Source: owner upload SHA256 recorded in docs/OWNER_ENVIRONMENT.md.
Supplied layout's fixed hardware/quorum assertions are replaced by readbacks.

Source: `src/keddeh_namespace/hci_contract.py:11`. Calls: `'\n'.join`.

## hci_contract.KEDDEHHCIContract.render_iso_compliant_footer

`(self, action_mapping)`

Operational adapter of the owner's Shared KEDDEH HCI contract.

Source: owner upload SHA256 recorded in docs/OWNER_ENVIRONMENT.md.
Supplied layout's fixed hardware/quorum assertions are replaced by readbacks.

Source: `src/keddeh_namespace/hci_contract.py:14`. Calls: `' | '.join`, `'\n'.join`, `action_mapping.items`.

## hci_contract.KEDDEHHCIContract.commit_evidence_trace

`(self, input_action, processing_digest)`

Operational adapter of the owner's Shared KEDDEH HCI contract.

Source: owner upload SHA256 recorded in docs/OWNER_ENVIRONMENT.md.
Supplied layout's fixed hardware/quorum assertions are replaced by readbacks.

Source: `src/keddeh_namespace/hci_contract.py:16`. Calls: `f'{self.project_name}:{input_action}:{processing_digest}'.encode`, `hashlib.sha256`, `hashlib.sha256(f'{self.project_name}:{input_action}:{processing_digest}'.encode()).hexdigest`.

## hci_contract.KEDDEHHCIContract.render

`(self, readback)`

Operational adapter of the owner's Shared KEDDEH HCI contract.

Source: owner upload SHA256 recorded in docs/OWNER_ENVIRONMENT.md.
Supplied layout's fixed hardware/quorum assertions are replaced by readbacks.

Source: `src/keddeh_namespace/hci_contract.py:20`. Calls: `'\n'.join`, `hashlib.sha256`, `hashlib.sha256(payload.encode()).hexdigest`, `json.dumps`, `payload.encode`, `readback['bilateral']['status'].upper`, `self.commit_evidence_trace`, `self.render_iso_compliant_footer`, `self.render_iso_compliant_header`.

## healthcheck.authority_probe

`(address, zone, *, port=53, timeout=3, pinned_dnskey_sha256=None)`

Direct DNS UDP/TCP readback; never infer authoritative health from a PID.

Source: `src/keddeh_namespace/healthcheck.py:16`. Calls: `'\n'.join`, `'\n'.join(sorted((key.to_text() for key in keys[0]))).encode`, `ValueError`, `dns.dnssec.validate`, `dns.message.make_query`, `dns.name.from_text`, `dns.query.tcp`, `dns.query.udp`, `hashlib.sha256`, `hashlib.sha256('\n'.join(sorted((key.to_text() for key in keys[0]))).encode()).hexdigest`, `key.to_text`, `len`, `response.rcode`, `result.update`, `serials.append`, `set`, `sorted`, `transport`.

## healthcheck.main

`()`

Direct DNS UDP/TCP readback; never infer authoritative health from a PID.

Source: `src/keddeh_namespace/healthcheck.py:56`. Calls: `ValueError`, `argparse.ArgumentParser`, `authority_probe`, `json.dumps`, `parser.add_argument`, `parser.exit`, `parser.parse_args`, `print`.

## hydrate_service_volumes.archive_snapshot

`(source, snapshot, expected)`

Verify a private archive snapshot and publish bounded regular files write-once.

Source: `src/keddeh_namespace/hydrate_service_volumes.py:19`. Calls: `ValueError`, `any`, `expected.get`, `hasher.hexdigest`, `hasher.update`, `hashlib.sha256`, `len`, `open`, `os.fdopen`, `os.fstat`, `os.fsync`, `os.open`, `output.fileno`, `output.flush`, `output.write`, `stat.S_ISREG`, `stream.fileno`, `stream.read`, `type`.

## hydrate_service_volumes.verify_admission

`(destination, expected)`

Verify a private archive snapshot and publish bounded regular files write-once.

Source: `src/keddeh_namespace/hydrate_service_volumes.py:39`. Calls: `(destination / RECEIPT).read_text`, `Path`, `ValueError`, `destination.rglob`, `hashlib.sha256`, `hashlib.sha256(path.read_bytes()).hexdigest`, `json.loads`, `path.is_dir`, `path.is_file`, `path.is_symlink`, `path.read_bytes`, `path.relative_to`, `path.stat`, `receipt.get`, `stat.S_IMODE`, `str`.

## hydrate_service_volumes.hydrate

`(source, root, expected, *, max_bytes=1024 ** 3, max_files=10000)`

Verify a private archive snapshot and publish bounded regular files write-once.

Source: `src/keddeh_namespace/hydrate_service_volumes.py:55`. Calls: `(output / RECEIPT).chmod`, `(output / RECEIPT).open`, `Path`, `Path(root).resolve`, `ValueError`, `any`, `archive.extractfile`, `archive.infolist`, `archive.open`, `archive_snapshot`, `canonical_bytes`, `declared.add`, `destination.chmod`, `destination.exists`, `destination.is_symlink`, `entry`, `fcntl.flock`, `hasher.hexdigest`, `hasher.update`, `hashlib.sha256`, `info.is_dir`, `info.isdir`, `info.isfile`, `len`, `logical_path`, `name.rstrip`, `normalized.split`, `open`, `os.fsync`, `os.rename`, `output.mkdir`, `output.rglob`, `path.chmod`, `path.is_dir`, `root.mkdir`, `set`, `sink.fileno`, `sink.flush`, `sink.write`, `sorted`, `stat.S_IFMT`, `stream.fileno`, `stream.flush`, `stream.read`, `stream.write`, `sync_directory`, `tarfile.open`, `target.chmod`, `target.mkdir`, `target.open`, `target.parent.mkdir`, `tempfile.TemporaryDirectory`, `type`, `verify_admission`, `write_file`, `zipfile.ZipFile`, `zipfile.is_zipfile`.

## hydrate_service_volumes.main

`()`

Verify a private archive snapshot and publish bounded regular files write-once.

Source: `src/keddeh_namespace/hydrate_service_volumes.py:132`. Calls: `argparse.ArgumentParser`, `hydrate`, `json.dumps`, `json.load`, `open`, `parser.add_argument`, `parser.exit`, `parser.parse_args`, `print`.

## logical_vfs.logical_path

`(value)`

Local content-addressed VFS with SQLite version journal and readback integrity.

Source: `src/keddeh_namespace/logical_vfs.py:15`. Calls: `PurePosixPath`, `ValueError`, `any`, `path.is_absolute`, `type`, `value.split`.

## logical_vfs.sync_directory

`(path)`

Local content-addressed VFS with SQLite version journal and readback integrity.

Source: `src/keddeh_namespace/logical_vfs.py:24`. Calls: `os.close`, `os.fsync`, `os.open`.

## logical_vfs.LogicalVFS.__init__

`(self, root)`

Local content-addressed VFS with SQLite version journal and readback integrity.

Source: `src/keddeh_namespace/logical_vfs.py:34`. Calls: `Path`, `Path(root).resolve`, `db.executescript`, `self.connect`, `self.objects.mkdir`, `self.root.mkdir`.

## logical_vfs.LogicalVFS.connect

`(self)`

Local content-addressed VFS with SQLite version journal and readback integrity.

Source: `src/keddeh_namespace/logical_vfs.py:53`. Calls: `db.close`, `db.execute`, `sqlite3.connect`.

## logical_vfs.LogicalVFS.put_object

`(self, payload)`

Local content-addressed VFS with SQLite version journal and readback integrity.

Source: `src/keddeh_namespace/logical_vfs.py:64`. Calls: `Path`, `Path(staging).unlink`, `ValueError`, `hashlib.sha256`, `hashlib.sha256(payload).hexdigest`, `os.chmod`, `os.fdopen`, `os.fsync`, `os.link`, `self.read_object`, `stream.fileno`, `stream.flush`, `stream.write`, `sync_directory`, `tempfile.mkstemp`, `type`.

## logical_vfs.LogicalVFS.read_object

`(self, digest)`

Local content-addressed VFS with SQLite version journal and readback integrity.

Source: `src/keddeh_namespace/logical_vfs.py:87`. Calls: `ValueError`, `any`, `hashlib.sha256`, `hashlib.sha256(payload).hexdigest`, `len`, `os.fdopen`, `os.open`, `stream.read`, `type`.

## logical_vfs.LogicalVFS.write

`(self, path, payload, *, expected_version)`

Local content-addressed VFS with SQLite version journal and readback integrity.

Source: `src/keddeh_namespace/logical_vfs.py:98`. Calls: `Conflict`, `ValueError`, `canonical_bytes`, `db.execute`, `db.execute('SELECT * FROM heads WHERE path=?', (path,)).fetchone`, `db.execute('SELECT sequence, receipt FROM events ORDER BY sequence DESC LIMIT 1').fetchone`, `dict`, `event.values`, `hashlib.sha256`, `hashlib.sha256(canonical_bytes(event)).hexdigest`, `logical_path`, `self.connect`, `self.put_object`, `type`.

## logical_vfs.LogicalVFS.read

`(self, path)`

Local content-addressed VFS with SQLite version journal and readback integrity.

Source: `src/keddeh_namespace/logical_vfs.py:120`. Calls: `KeyError`, `db.execute`, `db.execute('SELECT * FROM heads WHERE path=?', (path,)).fetchone`, `dict`, `logical_path`, `self.connect`, `self.read_object`.

## logical_vfs.LogicalVFS.history

`(self)`

Local content-addressed VFS with SQLite version journal and readback integrity.

Source: `src/keddeh_namespace/logical_vfs.py:128`. Calls: `ValueError`, `canonical_bytes`, `db.execute`, `dict`, `enumerate`, `event.items`, `hashlib.sha256`, `hashlib.sha256(canonical_bytes(raw)).hexdigest`, `heads.get`, `heads.get(event['path'], {}).get`, `self.connect`, `self.read_object`.

## native_labels.displacement

`(label: int)`

Map occupied labels ..., -3, -2, 1, 2, 3, ... to integer displacement.

Source: `src/keddeh_namespace/native_labels.py:4`. Calls: `ValueError`, `type`.

## native_labels.native_label

`(offset: int)`

Map measurement displacement back to an occupied native label.

Source: `src/keddeh_namespace/native_labels.py:11`. Calls: `ValueError`, `type`.

## native_labels.add_labels

`(left: int, right: int)`

REV-002 research adapter; native labels do not alter protocol integers.

Source: `src/keddeh_namespace/native_labels.py:18`. Calls: `displacement`, `native_label`.

## owner_kernel.SovereignHardgate.__init__

`(self)`

Owner-authored K-Cloud kernel selected from notebook exports.

Exact class bodies: k_cloud_substrate_master_daemon.py lines 734-826,
bilateral_discrepancy_solver.py lines 54-121. Notebook installation cells
and simulated startup demonstrations are not executed by this module.

Source: `src/keddeh_namespace/owner_kernel.py:14`. Calls: .

## owner_kernel.SovereignHardgate._fold

`(self, a: int, b: int)`

Owner-authored K-Cloud kernel selected from notebook exports.

Exact class bodies: k_cloud_substrate_master_daemon.py lines 734-826,
bilateral_discrepancy_solver.py lines 54-121. Notebook installation cells
and simulated startup demonstrations are not executed by this module.

Source: `src/keddeh_namespace/owner_kernel.py:17`. Calls: .

## owner_kernel.SovereignHardgate.authenticate

`(self, payload: str)`

Owner-authored K-Cloud kernel selected from notebook exports.

Exact class bodies: k_cloud_substrate_master_daemon.py lines 734-826,
bilateral_discrepancy_solver.py lines 54-121. Notebook installation cells
and simulated startup demonstrations are not executed by this module.

Source: `src/keddeh_namespace/owner_kernel.py:20`. Calls: `len`, `ord`, `self._fold`, `sum`.

## owner_kernel.ZeroLessIndexEngine.route

`(self, index: int, payload: str)`

Owner-authored K-Cloud kernel selected from notebook exports.

Exact class bodies: k_cloud_substrate_master_daemon.py lines 734-826,
bilateral_discrepancy_solver.py lines 54-121. Notebook installation cells
and simulated startup demonstrations are not executed by this module.

Source: `src/keddeh_namespace/owner_kernel.py:34`. Calls: `print`, `self._wired_fat_mapping`.

## owner_kernel.ZeroLessIndexEngine._wired_fat_mapping

`(self, index: int, payload: str)`

Owner-authored K-Cloud kernel selected from notebook exports.

Exact class bodies: k_cloud_substrate_master_daemon.py lines 734-826,
bilateral_discrepancy_solver.py lines 54-121. Notebook installation cells
and simulated startup demonstrations are not executed by this module.

Source: `src/keddeh_namespace/owner_kernel.py:42`. Calls: `hashlib.sha256`, `hashlib.sha256(payload.encode()).hexdigest`, `payload.encode`.

## owner_kernel.DynamicHealingAgent.__init__

`(self, d: float=0.12, lam_o: float=0.35, lam_e: float=0.25, iterations: int=5)`

Owner-authored K-Cloud kernel selected from notebook exports.

Exact class bodies: k_cloud_substrate_master_daemon.py lines 734-826,
bilateral_discrepancy_solver.py lines 54-121. Notebook installation cells
and simulated startup demonstrations are not executed by this module.

Source: `src/keddeh_namespace/owner_kernel.py:50`. Calls: `np.array`.

## owner_kernel.DynamicHealingAgent.resolve_drift

`(self, error_vector: list)`

Owner-authored K-Cloud kernel selected from notebook exports.

Exact class bodies: k_cloud_substrate_master_daemon.py lines 734-826,
bilateral_discrepancy_solver.py lines 54-121. Notebook installation cells
and simulated startup demonstrations are not executed by this module.

Source: `src/keddeh_namespace/owner_kernel.py:62`. Calls: `Z_n.tolist`, `np.array`, `range`, `self.A.dot`.

## owner_kernel.KCloudNode.__init__

`(self)`

Owner-authored K-Cloud kernel selected from notebook exports.

Exact class bodies: k_cloud_substrate_master_daemon.py lines 734-826,
bilateral_discrepancy_solver.py lines 54-121. Notebook installation cells
and simulated startup demonstrations are not executed by this module.

Source: `src/keddeh_namespace/owner_kernel.py:71`. Calls: `DynamicHealingAgent`, `SovereignHardgate`, `ZeroLessIndexEngine`.

## owner_kernel.KCloudNode.execute_26_node_traversal

`(self)`

Owner-authored K-Cloud kernel selected from notebook exports.

Exact class bodies: k_cloud_substrate_master_daemon.py lines 734-826,
bilateral_discrepancy_solver.py lines 54-121. Notebook installation cells
and simulated startup demonstrations are not executed by this module.

Source: `src/keddeh_namespace/owner_kernel.py:79`. Calls: `print`, `range`, `time.sleep`.

## owner_kernel.KCloudNode.process_request

`(self, index: int, payload: str)`

Owner-authored K-Cloud kernel selected from notebook exports.

Exact class bodies: k_cloud_substrate_master_daemon.py lines 734-826,
bilateral_discrepancy_solver.py lines 54-121. Notebook installation cells
and simulated startup demonstrations are not executed by this module.

Source: `src/keddeh_namespace/owner_kernel.py:86`. Calls: `datetime.now`, `datetime.now().isoformat`, `self.gate.authenticate`, `self.healer.resolve_drift`, `self.ledger.append`, `self.router.route`.

## owner_kernel.StochasticKuramotoPLL.__init__

`(self, num_nodes=3, omega_star=0.297, dt=0.01)`

Owner-authored K-Cloud kernel selected from notebook exports.

Exact class bodies: k_cloud_substrate_master_daemon.py lines 734-826,
bilateral_discrepancy_solver.py lines 54-121. Notebook installation cells
and simulated startup demonstrations are not executed by this module.

Source: `src/keddeh_namespace/owner_kernel.py:105`. Calls: `np.random.uniform`.

## owner_kernel.StochasticKuramotoPLL.step

`(self, t, parent_phase, parent_available, reanchor_time, Tr=2.0)`

Integrates one step of the SDE using Euler-Maruyama

Source: `src/keddeh_namespace/owner_kernel.py:123`. Calls: `max`, `np.abs`, `np.angle`, `np.exp`, `np.mean`, `np.random.normal`, `np.sin`, `np.sqrt`, `np.zeros`, `range`.

## propagation_runtime.archive_registry

`(registry, archive_root)`

Archive verified signed history and rehydrate by replaying actual object bytes.

Source: `src/keddeh_namespace/propagation_runtime.py:10`. Calls: `LogicalVFS`, `ValueError`, `archive.put_object`, `canonical_bytes`, `db.execute`, `entries.append`, `len`, `registry.replay`, `registry.vfs.connect`, `registry.vfs.read_object`.

## propagation_runtime.restore_registry

`(archive_root, manifest_digest, target_root, trust)`

Archive verified signed history and rehydrate by replaying actual object bytes.

Source: `src/keddeh_namespace/propagation_runtime.py:27`. Calls: `LogicalVFS`, `Registry`, `ValueError`, `archive.read_object`, `assessed.add`, `assessment.get`, `assessments.append`, `canonical_bytes`, `content_root`, `dict`, `enumerate`, `hashlib.sha256`, `hashlib.sha256(canonical_bytes(event)).hexdigest`, `heads.get`, `json.loads`, `logical_path`, `registry.assess`, `registry.commit`, `registry.replay`, `requests.append`, `seen.add`, `set`, `type`, `verify_assessment`, `verify_observation`, `versions.get`.

## propagation_runtime.backward_lineage

`(registry, path)`

Archive verified signed history and rehydrate by replaying actual object bytes.

Source: `src/keddeh_namespace/propagation_runtime.py:76`. Calls: `db.execute`, `json.loads`, `registry.replay`, `registry.vfs.connect`, `registry.vfs.read`, `result.append`, `verify_observation`.

## registry_service.Registry.__init__

`(self, root, trust)`

Loopback-only registry with authenticated writes and durable signed observations.

Source: `src/keddeh_namespace/registry_service.py:19`. Calls: `LogicalVFS`, `db.execute`, `self.vfs.connect`.

## registry_service.Registry.commit

`(self, request)`

Loopback-only registry with authenticated writes and durable signed observations.

Source: `src/keddeh_namespace/registry_service.py:32`. Calls: `Conflict`, `ValueError`, `canonical_bytes`, `content_root`, `db.execute`, `db.execute('SELECT * FROM heads WHERE path=?', (path,)).fetchone`, `db.execute('SELECT * FROM requests WHERE request_id=?', (request_id,)).fetchone`, `db.execute('SELECT 1 FROM observations WHERE digest=?', (digest,)).fetchone`, `db.execute('SELECT digest FROM observation_heads WHERE runtime_id=?', (runtime,)).fetchone`, `db.execute('SELECT sequence,receipt FROM events ORDER BY sequence DESC LIMIT 1').fetchone`, `dict`, `event.values`, `hashlib.sha256`, `hashlib.sha256(canonical_bytes(event)).hexdigest`, `hashlib.sha256(raw).hexdigest`, `json.loads`, `len`, `logical_path`, `request_id.strip`, `self.vfs.connect`, `self.vfs.put_object`, `set`, `type`, `verify_observation`.

## registry_service.Registry.assess

`(self, assessment)`

Loopback-only registry with authenticated writes and durable signed observations.

Source: `src/keddeh_namespace/registry_service.py:83`. Calls: `Conflict`, `ValueError`, `assessment.get`, `canonical_bytes`, `db.execute`, `db.execute('SELECT signed FROM assessments WHERE digest=?', (digest,)).fetchone`, `db.execute('SELECT signed FROM observations WHERE digest=?', (digest,)).fetchone`, `json.loads`, `self.vfs.connect`, `type`, `verify_assessment`.

## registry_service.Registry.replay

`(self)`

Loopback-only registry with authenticated writes and durable signed observations.

Source: `src/keddeh_namespace/registry_service.py:99`. Calls: `ValueError`, `canonical_bytes`, `chain_heads.get`, `content_root`, `db.execute`, `dict`, `json.loads`, `observations.get`, `observations.get(digest, {}).get`, `seen.add`, `self.vfs.connect`, `self.vfs.history`, `self.vfs.read_object`, `set`, `verify_assessment`, `verify_observation`.

## registry_service.make_server

`(registry, token, host='127.0.0.1', port=0)`

Loopback-only registry with authenticated writes and durable signed observations.

Source: `src/keddeh_namespace/registry_service.py:133`. Calls: `('Bearer ' + token).encode`, `ThreadingHTTPServer`, `ValueError`, `canonical_bytes`, `hmac.compare_digest`, `int`, `ipaddress.ip_address`, `json.loads`, `len`, `registry.assess`, `registry.commit`, `registry.replay`, `registry.vfs.read`, `self.authorized`, `self.connection.settimeout`, `self.end_headers`, `self.headers.get`, `self.headers.get('Authorization', '').encode`, `self.reply`, `self.rfile.read`, `self.send_header`, `self.send_response`, `self.wfile.write`, `set`, `str`, `super`, `super().setup`, `type`, `urllib.parse.parse_qs`, `urllib.parse.urlsplit`.

## registry_service.main

`()`

Loopback-only registry with authenticated writes and durable signed observations.

Source: `src/keddeh_namespace/registry_service.py:181`. Calls: `Registry`, `argparse.ArgumentParser`, `json.load`, `make_server`, `open`, `os.environ.get`, `parser.add_argument`, `parser.error`, `parser.parse_args`, `registry.replay`, `server.serve_forever`, `server.server_close`.

## render_knot_config.render

`(config, role, *, zone_file='/state/zone.zone', key_include='/secrets/transfer.conf', storage='/state', port=53)`

Role-bound Knot 3.4 configuration; key values are supplied through external includes.

Source: `src/keddeh_namespace/render_knot_config.py:9`. Calls: `'\n\n'.join`, `PurePosixPath`, `PurePosixPath(path).is_absolute`, `ValueError`, `any`, `config.get`, `quote`, `type`, `validate_nodes`, `zone_name`.

## render_knot_config.main

`()`

Role-bound Knot 3.4 configuration; key values are supplied through external includes.

Source: `src/keddeh_namespace/render_knot_config.py:32`. Calls: `argparse.ArgumentParser`, `json.load`, `open`, `parser.add_argument`, `parser.exit`, `parser.parse_args`, `render`, `stream.write`.

## service_stack.render_stack

`(manifests, source_manifest, proxy)`

Render deployment files only from admitted exact sources and explicit pinned images.

Source: `src/keddeh_namespace/service_stack.py:13`. Calls: `'\n'.join`, `IMAGE.fullmatch`, `Path`, `Path(manifest['volume']).resolve`, `Path(proxy.get('config_path', '')).resolve`, `ROUTE.fullmatch`, `ValueError`, `any`, `canonical_bytes`, `config_path.is_file`, `config_path.is_symlink`, `hashlib.sha256`, `hashlib.sha256(canonical_bytes(receipt)).hexdigest`, `json.dumps`, `proxy.get`, `r.startswith`, `route.startswith`, `routes.add`, `set`, `str`, `type`, `verify_admission`, `zip`.

## signatures.sign_observation

`(envelope, private_key)`

Ed25519 envelopes and independently signed assessments with explicit trust roles.

Source: `src/keddeh_namespace/signatures.py:12`. Calls: `base64.b64encode`, `base64.b64encode(private_key.sign(DOMAIN + canonical_bytes(payload))).decode`, `canonical_bytes`, `envelope_digest`, `json.loads`, `private_key.sign`.

## signatures.trusted_key

`(trust, identity, role)`

Ed25519 envelopes and independently signed assessments with explicit trust roles.

Source: `src/keddeh_namespace/signatures.py:20`. Calls: `Ed25519PublicKey.from_public_bytes`, `ValueError`, `base64.b64decode`, `entry.get`, `isinstance`, `trust.get`, `type`.

## signatures.verify_signature

`(key, signature, payload)`

Ed25519 envelopes and independently signed assessments with explicit trust roles.

Source: `src/keddeh_namespace/signatures.py:32`. Calls: `ValueError`, `base64.b64decode`, `key.verify`.

## signatures.verify_observation

`(signed, trust)`

Ed25519 envelopes and independently signed assessments with explicit trust roles.

Source: `src/keddeh_namespace/signatures.py:39`. Calls: `ValueError`, `canonical_bytes`, `envelope_digest`, `set`, `trust[envelope['generator_id']].get`, `trusted_key`, `type`, `verify_signature`.

## signatures.sign_assessment

`(signed, verifier_id, private_key)`

Ed25519 envelopes and independently signed assessments with explicit trust roles.

Source: `src/keddeh_namespace/signatures.py:52`. Calls: `ValueError`, `base64.b64encode`, `base64.b64encode(private_key.sign(ASSESSMENT_DOMAIN + canonical_bytes(payload))).decode`, `canonical_bytes`, `dict`, `envelope_digest`, `private_key.sign`.

## signatures.verify_assessment

`(signed, assessment, trust)`

Ed25519 envelopes and independently signed assessments with explicit trust roles.

Source: `src/keddeh_namespace/signatures.py:60`. Calls: `ValueError`, `assessment.items`, `canonical_bytes`, `generator_key.public_bytes_raw`, `set`, `trusted_key`, `type`, `verifier_key.public_bytes_raw`, `verify_observation`, `verify_signature`.

## source_custody.verify_archive

`(path, expected)`

Verify exact archive bytes without extracting or executing their contents.

Source: `src/keddeh_namespace/source_custody.py:11`. Calls: `Path`, `ValueError`, `expected.get`, `hasher.hexdigest`, `hasher.update`, `hashlib.sha256`, `isinstance`, `iter`, `len`, `os.close`, `os.fdopen`, `os.fstat`, `os.open`, `re.fullmatch`, `stat.S_ISREG`, `stream.fileno`, `stream.read`, `type`.

## source_custody.main

`()`

Verify exact archive bytes without extracting or executing their contents.

Source: `src/keddeh_namespace/source_custody.py:44`. Calls: `argparse.ArgumentParser`, `args.manifest.read_text`, `json.dumps`, `json.loads`, `parser.add_argument`, `parser.exit`, `parser.parse_args`, `print`, `verify_archive`.

## universal_propagation.finite

`(value)`

Directed delayed propagation and explicitly scoped topology experiments.

Units are caller-defined but consistent: decay/time, weight state/time,
threshold and scale in state units. History before t=0 is initial state.

Source: `src/keddeh_namespace/universal_propagation.py:16`. Calls: `ValueError`, `float`, `math.isfinite`.

## universal_propagation.sigmoid

`(z)`

Directed delayed propagation and explicitly scoped topology experiments.

Units are caller-defined but consistent: decay/time, weight state/time,
threshold and scale in state units. History before t=0 is initial state.

Source: `src/keddeh_namespace/universal_propagation.py:23`. Calls: `finite`, `math.exp`.

## universal_propagation.Topology.__post_init__

`(self)`

Directed delayed propagation and explicitly scoped topology experiments.

Units are caller-defined but consistent: decay/time, weight state/time,
threshold and scale in state units. History before t=0 is initial state.

Source: `src/keddeh_namespace/universal_propagation.py:44`. Calls: `ValueError`, `finite`, `isinstance`, `len`, `pairs.add`, `set`.

## universal_propagation.Topology.adjacency

`(cls, matrix)`

Rows are sources; columns are destinations, including signed weights.

Source: `src/keddeh_namespace/universal_propagation.py:61`. Calls: `Edge`, `ValueError`, `any`, `cls`, `enumerate`, `finite`, `len`, `range`, `str`, `tuple`.

## universal_propagation.Topology.graphml

`(cls, path)`

Directed delayed propagation and explicitly scoped topology experiments.

Units are caller-defined but consistent: decay/time, weight state/time,
threshold and scale in state units. History before t=0 is initial state.

Source: `src/keddeh_namespace/universal_propagation.py:70`. Calls: `ET.fromstring`, `Edge`, `Path`, `Path(path).read_bytes`, `ValueError`, `cls`, `datum.get`, `edges.append`, `element.findall`, `element.get`, `enumerate`, `finite`, `graph.findall`, `graphs[0].get`, `int`, `key.find`, `key.get`, `keys.values`, `len`, `raw.upper`, `root.findall`, `tuple`, `values.get`.

## universal_propagation.PropagationRuntime.__init__

`(self, topology, *, dt=0.1, decay=1.0, threshold=0.0, scale=1.0, initial=None, dropout=0.0, seed=0)`

Directed delayed propagation and explicitly scoped topology experiments.

Units are caller-defined but consistent: decay/time, weight state/time,
threshold and scale in state units. History before t=0 is initial state.

Source: `src/keddeh_namespace/universal_propagation.py:107`. Calls: `ValueError`, `finite`, `len`, `map`, `max`, `random.Random`, `tuple`.

## universal_propagation.PropagationRuntime.tick

`(self)`

Directed delayed propagation and explicitly scoped topology experiments.

Units are caller-defined but consistent: decay/time, weight state/time,
threshold and scale in state units. History before t=0 is initial state.

Source: `src/keddeh_namespace/universal_propagation.py:121`. Calls: `finite`, `len`, `self.history.append`, `self.rng.random`, `sigmoid`, `tuple`, `zip`.

## universal_propagation.topology_experiment

`(*, nodes=20, rounds=20, trials=200, seed=20260930)`

SI attempts to every outgoing neighbor per round; NOT the ODE or LIF.

Mesh has extra edges/attempts: this is a redundancy experiment, not a
communication-budget-matched comparison. Persistent retry permits recovery.

Source: `src/keddeh_namespace/universal_propagation.py:136`. Calls: `ValueError`, `coverage.append`, `informed.update`, `len`, `math.sqrt`, `min`, `new.add`, `random.Random`, `range`, `results.append`, `rng.random`, `set`, `sorted`, `sum`.

## universal_propagation.main

`()`

Directed delayed propagation and explicitly scoped topology experiments.

Units are caller-defined but consistent: decay/time, weight state/time,
threshold and scale in state units. History before t=0 is initial state.

Source: `src/keddeh_namespace/universal_propagation.py:170`. Calls: `Path`, `Path(args.adjacency_json).read_text`, `PropagationRuntime`, `Topology.adjacency`, `Topology.graphml`, `argparse.ArgumentParser`, `bool`, `json.dumps`, `json.loads`, `len`, `parser.add_argument`, `parser.error`, `parser.parse_args`, `print`, `range`, `runtime.tick`, `topology_experiment`.

## verify_vfs.verify_volume

`(path, *, required_bytes, require_mount=True)`

Measure mounted storage and execute fsync/readback without claiming remote durability.

Source: `src/keddeh_namespace/verify_vfs.py:12`. Calls: `Path`, `Path(path).resolve`, `Path(probe).read_bytes`, `Path(probe).unlink`, `ValueError`, `dict`, `hashlib.sha256`, `hashlib.sha256(payload).hexdigest`, `os.fdopen`, `os.fsync`, `os.path.ismount`, `os.statvfs`, `secrets.token_bytes`, `str`, `stream.fileno`, `stream.flush`, `stream.write`, `sync_directory`, `tempfile.mkstemp`, `type`.

## verify_vfs.main

`()`

Measure mounted storage and execute fsync/readback without claiming remote durability.

Source: `src/keddeh_namespace/verify_vfs.py:39`. Calls: `argparse.ArgumentParser`, `json.dumps`, `parser.add_argument`, `parser.exit`, `parser.parse_args`, `print`, `verify_volume`.

## vfs_subscription.VFSSubscription.__init__

`(self, controller)`

Durable family subscription to the owner's VFS_SERVER artifact graph.

Source: `src/keddeh_namespace/vfs_subscription.py:11`. Calls: `controller.config.get`, `json.loads`, `self.path.exists`, `self.path.read_text`, `self.root.mkdir`.

## vfs_subscription.VFSSubscription.request

`(self, path, body=None)`

Durable family subscription to the owner's VFS_SERVER artifact graph.

Source: `src/keddeh_namespace/vfs_subscription.py:16`. Calls: `Path`, `Path(self.config['token_file']).read_text`, `Path(self.config['token_file']).read_text().strip`, `ValueError`, `json.dumps`, `json.dumps(body).encode`, `json.loads`, `reply.read`, `urllib.parse.urlsplit`, `urllib.request.Request`, `urllib.request.urlopen`.

## vfs_subscription.VFSSubscription.save

`(self)`

Durable family subscription to the owner's VFS_SERVER artifact graph.

Source: `src/keddeh_namespace/vfs_subscription.py:23`. Calls: `write_json`.

## vfs_subscription.VFSSubscription.tick

`(self)`

Durable family subscription to the owner's VFS_SERVER artifact graph.

Source: `src/keddeh_namespace/vfs_subscription.py:26`. Calls: `LogicalVFS`, `ValueError`, `base64.b64decode`, `base64.b64encode`, `base64.b64encode(raw).decode`, `event.get`, `hashlib.sha256`, `hashlib.sha256(raw).hexdigest`, `json.dumps`, `json.dumps(view, sort_keys=True).encode`, `len`, `local.put_object`, `path.startswith`, `self.controller.status`, `self.request`, `self.save`, `self.state.get`, `self.state.update`, `self.state['objects'].get`, `str`, `time.monotonic`, `type`, `urllib.parse.urlencode`, `view.update`.

## web4_runtime.digest

`(path)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:47`. Calls: `Path`, `Path(path).read_bytes`, `hashlib.sha256`, `hashlib.sha256(Path(path).read_bytes()).hexdigest`.

## web4_runtime.write_json

`(path, value, private=True)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:51`. Calls: `Path`, `json.dump`, `os.chmod`, `os.close`, `os.fsync`, `os.open`, `os.replace`, `path.parent.mkdir`, `path.with_name`, `secrets.token_hex`, `stream.fileno`, `stream.flush`, `stream.write`, `temp.open`.

## web4_runtime.copy_files

`(source, target)`

Mutable launch derivation; immutable admitted source remains separate.

Source: `src/keddeh_namespace/web4_runtime.py:63`. Calls: `Path`, `Path(source).rglob`, `out.chmod`, `out.parent.mkdir`, `path.is_file`, `path.relative_to`, `shutil.copyfile`, `sorted`, `target.mkdir`.

## web4_runtime.harden_broker_source

`(text)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:73`. Calls: `text.replace`.

## web4_runtime._prepare

`(root, library, offset=0)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:100`. Calls: `(estate / 'data_runtime/live_state.json').unlink`, `(root / 'packages').rglob`, `(state / 'generator.key').chmod`, `(state / 'generator.key').write_bytes`, `(state / 'pairing-code').chmod`, `(state / 'pairing-code').write_text`, `(state / 'token').chmod`, `(state / 'token').write_text`, `(target / name).chmod`, `Ed25519PrivateKey.generate`, `PINS.items`, `Path`, `Path(library).read_text`, `Path(root).absolute`, `ValueError`, `any`, `base64.b64encode`, `base64.b64encode(key.public_key().public_bytes_raw()).decode`, `broker.read_text`, `broker.write_text`, `copy_files`, `core.read_text`, `core.write_text`, `digest`, `harden_broker_source`, `harness.read_text`, `harness.write_text`, `hydrate`, `json.loads`, `key.private_bytes_raw`, `key.public_key`, `key.public_key().public_bytes_raw`, `len`, `list`, `name.endswith`, `p.is_file`, `p.relative_to`, `provenance.append`, `range`, `registry_path.read_text`, `root.chmod`, `root.exists`, `root.iterdir`, `root.mkdir`, `secrets.token_urlsafe`, `shutil.copyfile`, `source.stat`, `state.mkdir`, `str`, `target.mkdir`, `text.replace`, `write_json`, `zip`.

## web4_runtime.prepare

`(root, library, offset=0)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:166`. Calls: `(staging / 'launch.json').read_text`, `Path`, `Path(config['estate']).relative_to`, `Path(root).absolute`, `Path(value).relative_to`, `ValueError`, `_prepare`, `any`, `config['packages'].items`, `destination.exists`, `destination.iterdir`, `destination.parent.mkdir`, `json.loads`, `os.replace`, `str`, `tempfile.TemporaryDirectory`, `write_json`.

## web4_runtime.verify_launch

`(root)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:183`. Calls: `(root / 'launch.json').read_text`, `(root / 'packages').resolve`, `Path`, `ValueError`, `config['files'].items`, `digest`, `json.loads`, `original.is_symlink`, `original.resolve`, `path.is_relative_to`.

## web4_runtime.http_json

`(port, path, body=None, token=None)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:192`. Calls: `ValueError`, `json.dumps`, `json.dumps(body).encode`, `json.loads`, `len`, `response.read`, `urllib.request.Request`, `urllib.request.urlopen`.

## web4_runtime.encode_readback

`(value)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:202`. Calls: `ValueError`, `encode_readback`, `isinstance`, `math.isfinite`, `type`, `value.hex`, `value.items`.

## web4_runtime.load_module

`(path, name)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:212`. Calls: `importlib.util.module_from_spec`, `importlib.util.spec_from_file_location`, `spec.loader.exec_module`.

## web4_runtime.LaunchController.__init__

`(self, root)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:217`. Calls: `(self.state / 'generator.key').read_bytes`, `(self.state / 'token').read_text`, `(self.state / 'trust.json').read_text`, `BilateralRuntime`, `DomainMesh`, `Ed25519PrivateKey.from_private_bytes`, `KCloudNode`, `Path`, `Registry`, `VFSSubscription`, `base.rglob`, `canonical_bytes`, `code.iterdir`, `digest`, `hashlib.sha256`, `hashlib.sha256(canonical_bytes(self.source_manifest)).hexdigest`, `json.loads`, `p.is_file`, `p.relative_to`, `queue.Queue`, `self.config.get`, `sorted`, `str`, `threading.Event`, `threading.Lock`, `threading.RLock`, `verify_launch`, `version`, `write_json`.

## web4_runtime.LaunchController.env

`(self)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:243`. Calls: `(self.state / 'pairing-code').read_text`, `os.environ.items`, `str`, `values.update`.

## web4_runtime.LaunchController.spawn

`(self, name, argv, cwd, extra=None, stdio=False)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:248`. Calls: `(logs / (name + '.log')).open`, `Path`, `Path(__file__).with_name`, `env.update`, `iter`, `json.loads`, `logs.mkdir`, `proc.stdout.readline`, `self.env`, `self.rpc_responses.put`, `str`, `subprocess.Popen`, `threading.Thread`, `threading.Thread(target=reader, daemon=True).start`.

## web4_runtime.LaunchController.wait_health

`(self, name, port, path, timeout=8)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:263`. Calls: `RuntimeError`, `http_json`, `self.processes[name].poll`, `self.stop_event.wait`, `time.monotonic`.

## web4_runtime.LaunchController.estate_rpc

`(self, method, params=None)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:271`. Calls: `(json.dumps({'jsonrpc': '2.0', 'id': ident, 'method': method, 'params': params or {}}) + '\n').encode`, `RuntimeError`, `json.dumps`, `max`, `proc.stdin.flush`, `proc.stdin.write`, `reply.get`, `self.rpc_responses.get`, `str`, `time.monotonic`.

## web4_runtime.LaunchController.start

`(self)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:283`. Calls: `(self.estate / 'mesh/nodes' / candidate).is_file`, `(self.estate / 'mesh/registry.json').read_text`, `Path`, `RuntimeError`, `ValueError`, `health.get`, `json.loads`, `next`, `self.config.get`, `self.estate_rpc`, `self.pair_agent`, `self.spawn`, `self.wait_health`, `sock.bind`, `sock.setsockopt`, `socket.socket`, `str`.

## web4_runtime.LaunchController.pair_agent

`(self)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:320`. Calls: `(self.state / 'pairing-code').read_text`, `agent.pair`, `contextlib.redirect_stdout`, `io.StringIO`, `load_module`, `statefile.exists`.

## web4_runtime.LaunchController.status

`(self)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:328`. Calls: `broker.get`, `command.get`, `health.get`, `http_json`, `nodes.append`, `proc.poll`, `self.config.get`, `self.processes.items`, `self.restarts.get`, `sum`, `telemetry.get`, `type`.

## web4_runtime.LaunchController.receipt

`(self, event, readback)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:340`. Calls: `content_root`, `datetime.now`, `datetime.now(timezone.utc).isoformat`, `datetime.now(timezone.utc).isoformat(timespec='microseconds').replace`, `dict`, `encode_readback`, `envelope_digest`, `json.loads`, `secrets.token_hex`, `self.registry.commit`, `self.registry.vfs.read`, `sign_observation`.

## web4_runtime.LaunchController.queue_boot

`(self)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:354`. Calls: `ValueError`, `broker.queue_command`, `existing.get`, `http_json`, `http_json(self.ports['broker'], '/api/self-host/status').get`, `load_module`, `secrets.token_hex`.

## web4_runtime.LaunchController.restart

`(self, name)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:364`. Calls: `ValueError`, `self.estate_rpc`, `self.restarts.get`, `self.rpc_responses.empty`, `self.rpc_responses.get_nowait`, `self.spawn`, `self.terminate`.

## web4_runtime.LaunchController.terminate

`(proc)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:376`. Calls: `os.killpg`, `proc.poll`, `proc.wait`.

## web4_runtime.LaunchController.close

`(self)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:389`. Calls: `list`, `reversed`, `self.processes.values`, `self.stop_event.set`, `self.terminate`.

## web4_runtime.LaunchController.control

`(self, body)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:393`. Calls: `KEDDEHHCIContract`, `KEDDEHHCIContract('KEDDEH').render`, `PropagationRuntime`, `RuntimeError`, `Topology.adjacency`, `ValueError`, `body.get`, `dict`, `enumerate`, `http_json`, `json.dumps`, `len`, `load_module`, `max`, `min`, `module.diagnostic_run`, `module.make_node`, `output.update`, `range`, `receipts.append`, `record.get`, `round`, `rt.tick`, `self.bilateral.configure`, `self.domains.control`, `self.estate_rpc`, `self.owner_kernel.process_request`, `self.queue_boot`, `self.receipt`, `self.restart`, `self.status`, `self.stop_event.set`, `str`, `type`, `urlencode`, `write_json`, `{'boot': 1, 'restart': -2, 'stop': -3, 'commit': 2, 'propagate': 2, 'bilateral': 2, 'domains': 3, 'vfs': 3, 'hci': 3, 'workbook': 3, 'observer': 3, 'estate': 3}.get`.

## web4_runtime.serve

`(root)`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:456`. Calls: `('Bearer ' + controller.token).encode`, `(Path(__file__).parent / assets[path]).read_bytes`, `(root / '.controller.lock').open`, `(root / 'controller.json').unlink`, `LaunchController`, `Path`, `ThreadingHTTPServer`, `ValueError`, `controller.bilateral.tick`, `controller.close`, `controller.control`, `controller.domains.resume`, `controller.processes.items`, `controller.queue_boot`, `controller.receipt`, `controller.recovery_errors.pop`, `controller.registry.replay`, `controller.registry.vfs.read`, `controller.restart`, `controller.restarts.get`, `controller.retry_after.get`, `controller.start`, `controller.status`, `controller.stop_event.set`, `controller.stop_event.wait`, `controller.vfs.tick`, `directory.rglob`, `fcntl.flock`, `files[0].read_bytes`, `int`, `isinstance`, `json.dumps`, `json.dumps(value).encode`, `json.loads`, `len`, `list`, `lock.close`, `min`, `os.getpid`, `print`, `proc.poll`, `raw.replace`, `secrets.compare_digest`, `self.auth`, `self.connection.settimeout`, `self.end_headers`, `self.headers.get`, `self.rfile.read`, `self.send`, `self.send_header`, `self.send_response`, `self.wfile.write`, `server.server_close`, `server.shutdown`, `signal.signal`, `str`, `super`, `super().setup`, `threading.Thread`, `threading.Thread(target=server.serve_forever, daemon=True).start`, `time.monotonic`, `type`, `urlsplit`, `value.encode`, `write_json`.

## web4_runtime.main

`()`

Launch owner-supplied WEB4 packages with pinned custody and real readbacks.

Source: `src/keddeh_namespace/web4_runtime.py:529`. Calls: `(root / '.controller.lock').open`, `(root / 'controller.log').open`, `(root / 'launch.json').read_text`, `(root / 'state/token').read_text`, `LaunchController.terminate`, `Path`, `RuntimeError`, `argparse.ArgumentParser`, `fcntl.flock`, `http_json`, `json.dumps`, `json.loads`, `parser.add_argument`, `parser.parse_args`, `prepare`, `print`, `proc.poll`, `serve`, `str`, `subprocess.Popen`, `time.monotonic`, `time.sleep`, `verify_launch`.

