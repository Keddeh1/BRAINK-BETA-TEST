import sys
import os
import json
import socket
import threading
import time
from enum import Enum, auto

class ClientState(Enum):
    UNINITIALIZED = auto()
    DISCONNECTED = auto()
    CONNECTING = auto()
    ESTABLISHED = auto()
    SUBSCRIBED = auto()
    AUTHORIZED = auto()
    TERMINATED = auto()

class FullyEngineeredStratumClient:
    def __init__(self, host: str, port: int, worker_username: str, worker_password: str = "x"):
        self._host = host
        self._port = port
        self._worker_username = worker_username
        self._worker_password = worker_password
        
        self._buffer_size = 8192
        self._socket_timeout = 15.0
        self._max_retry_backoff = 60.0
        self._initial_retry_backoff = 2.0
        self._ping_interval_seconds = 45.0
        
        self._state = ClientState.UNINITIALIZED
        self._socket = None
        self._state_lock = threading.Lock()
        self._shutdown_event = threading.Event()
        
        self._receiver_thread = None
        self._heartbeat_thread = None
        
        self._rpc_id = 0
        self._rpc_lock = threading.Lock()
        self._pending_submissions = {}
        
        self._start_time = time.monotonic()
        self._metrics_lock = threading.Lock()
        self._metrics = {
            "packets_received": 0,
            "shares_submitted": 0,
            "shares_accepted": 0,
            "shares_rejected": 0,
            "network_timeouts": 0,
            "accumulated_latency_ms": 0.0,
            "last_latency_ms": 0.0,
            "current_difficulty": 16384.0
        }
        
        self._update_state(ClientState.DISCONNECTED)

    def _update_state(self, target_state: ClientState):
        with self._state_lock:
            old_state = self._state
            self._state = target_state
            sys.stdout.write(f"[STATE_ENGINE] Transitioned from {old_state.name} -> {self._state.name}\n")
            sys.stdout.flush()

    def _get_next_rpc_id(self) -> int:
        with self._rpc_lock:
            self._rpc_id += 1
            return self._rpc_id

    def force_network_reconnect(self):
        sys.stdout.write("[CONTROL_ACTION] Manual socket reset triggered via HTTPS control command.\n")
        sys.stdout.flush()
        self._cleanup_socket_layer()

    def get_live_diagnostics(self) -> dict:
        with self._metrics_lock:
            m = self._metrics.copy()
        
        elapsed = max(time.monotonic() - self._start_time, 1.0)
        avg_latency = (m["accumulated_latency_ms"] / m["shares_accepted"]) if m["shares_accepted"] > 0 else 0.0
        hash_rate_bps = (m["shares_accepted"] * m["current_difficulty"] * (2**32)) / elapsed
        total_resolved = m["shares_accepted"] + m["shares_rejected"]
        efficiency = (m["shares_accepted"] / total_resolved * 100.0) if total_resolved > 0 else 100.0
        
        return {
            "status": self._state.name,
            "target_host": self._host,
            "target_port": self._port,
            "difficulty": m["current_difficulty"],
            "hash_rate_ghs": hash_rate_bps / 1000000000.0,
            "efficiency_pct": efficiency,
            "frames_io": m["packets_received"],
            "dispatched": m["shares_submitted"],
            "accepted": m["shares_accepted"],
            "rejected": m["shares_rejected"],
            "timeouts": m["network_timeouts"],
            "latency_ms": m["last_latency_ms"],
            "avg_latency_ms": avg_latency,
            "uptime_seconds": elapsed
        }

    def bootstrap_pipeline(self):
        current_backoff = self._initial_retry_backoff
        while not self._shutdown_event.is_set():
            try:
                self._update_state(ClientState.CONNECTING)
                self._establish_raw_socket()
                self._negotiate_stratum_handshakes()
                current_backoff = self._initial_retry_backoff
                self._lifecycle_barrier()
                
            except socket.timeout:
                with self._metrics_lock:
                    self._metrics["network_timeouts"] += 1
                self._cleanup_socket_layer()
                
            except (socket.error, ConnectionError, TimeoutError):
                self._cleanup_socket_layer()
                if self._shutdown_event.is_set():
                    break
                self._update_state(ClientState.DISCONNECTED)
                self._shutdown_event.wait(current_backoff)
                current_backoff = min(current_backoff * 2, self._max_retry_backoff)
                
        self._update_state(ClientState.TERMINATED)

    def _establish_raw_socket(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.settimeout(self._socket_timeout)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        self._socket.connect((self._host, self._port))
        self._update_state(ClientState.ESTABLISHED)

    def _negotiate_stratum_handshakes(self):
        subscribe_id = self._get_next_rpc_id()
        sub_payload = {
            "id": subscribe_id,
            "method": "mining.subscribe",
            "params": ["EngineeredStratumClient/2.0.0", None, self._host, self._port]
        }
        self._transmit_frame(sub_payload)
        
        raw_response = self._read_blocking_frame()
        if not raw_response or ("error" in raw_response and raw_response["error"] is not None):
            raise ConnectionError("Subscription negotiation rejected by target cluster.")
        self._update_state(ClientState.SUBSCRIBED)

        auth_id = self._get_next_rpc_id()
        auth_payload = {
            "id": auth_id,
            "method": "mining.authorize",
            "params": [self._worker_username, self._worker_password]
        }
        self._transmit_frame(auth_payload)
        
        raw_auth_response = self._read_blocking_frame()
        if not raw_auth_response or not raw_auth_response.get("result"):
            raise ConnectionError("User authentication authorization mapping denied.")
        self._update_state(ClientState.AUTHORIZED)

        self._receiver_thread = threading.Thread(target=self._stream_receiver_loop, daemon=True)
        self._heartbeat_thread = threading.Thread(target=self._keepalive_heartbeat_loop, daemon=True)
        self._receiver_thread.start()
        self._heartbeat_thread.start()

    def _transmit_frame(self, payload: dict):
        serialized = (json.dumps(payload) + "\n").encode('utf-8')
        if self._socket:
            self._socket.sendall(serialized)

    def _read_blocking_frame(self) -> dict:
        buffer = b""
        while b"\n" not in buffer:
            chunk = self._socket.recv(self._buffer_size)
            if not chunk:
                return {}
            buffer += chunk
        line, _ = buffer.split(b"\n", 1)
        return json.loads(line.decode('utf-8'))

    def submit_share(self, job_id: str, extranonce2: str, ntime: str, nonce: str):
        if self._state != ClientState.AUTHORIZED:
            return
        submission_id = self._get_next_rpc_id()
        submit_payload = {
            "id": submission_id,
            "method": "mining.submit",
            "params": [self._worker_username, job_id, extranonce2, ntime, nonce]
        }
        with self._rpc_lock:
            self._pending_submissions[submission_id] = (job_id, time.perf_counter())
        with self._metrics_lock:
            self._metrics["shares_submitted"] += 1
        self._transmit_frame(submit_payload)

    def _stream_receiver_loop(self):
        stream_remainder = ""
        while not self._shutdown_event.is_set() and self._state == ClientState.AUTHORIZED:
            try:
                raw_bytes = self._socket.recv(self._buffer_size)
                if not raw_bytes:
                    break
                with self._metrics_lock:
                    self._metrics["packets_received"] += 1
                stream_data = stream_remainder + raw_bytes.decode('utf-8')
                lines = stream_data.split('\n')
                stream_remainder = lines.pop()
                for single_line in lines:
                    if single_line.strip():
                        self._process_inbound_json(single_line)
            except (socket.timeout, socket.error):
                break
        if not self._shutdown_event.is_set():
            self._cleanup_socket_layer()

    def _process_inbound_json(self, raw_line: str):
        payload = json.loads(raw_line)
        msg_id = payload.get("id")
        
        if payload.get("method") == "mining.notify":
            job_parameters = payload.get("params", [])
            if len(job_parameters) > 0:
                sys.stdout.write(f"[WORK_DISPATCH] Job Template Received ID: {job_parameters[0]}\n")
                sys.stdout.flush()
        elif payload.get("method") == "mining.set_difficulty":
            difficulty = payload.get("params", [16384.0])
            with self._metrics_lock:
                self._metrics["current_difficulty"] = float(difficulty[0])
        elif msg_id is not None:
            is_tracked_submission = False
            dispatch_time = 0.0
            with self._rpc_lock:
                if msg_id in self._pending_submissions:
                    is_tracked_submission = True
                    _, dispatch_time = self._pending_submissions.pop(msg_id)
            if is_tracked_submission:
                latency = (time.perf_counter() - dispatch_time) * 1000.0
                error_block = payload.get("error")
                result_success = payload.get("result", False)
                with self._metrics_lock:
                    self._metrics["last_latency_ms"] = latency
                    self._metrics["accumulated_latency_ms"] += latency
                    if result_success and error_block is None:
                        self._metrics["shares_accepted"] += 1
                    else:
                        self._metrics["shares_rejected"] += 1

    def _keepalive_heartbeat_loop(self):
        while not self._shutdown_event.is_set() and self._state == ClientState.AUTHORIZED:
            self._shutdown_event.wait(self._ping_interval_seconds)
            if self._shutdown_event.is_set() or self._state != ClientState.AUTHORIZED:
                break
            try:
                ping_id = self._get_next_rpc_id()
                ping_payload = {"id": ping_id, "method": "mining.ping", "params": []}
                self._transmit_frame(ping_payload)
            except socket.error:
                break

    def _lifecycle_barrier(self):
        while not self._shutdown_event.is_set() and self._state == ClientState.AUTHORIZED:
            time.sleep(0.5)

    def _cleanup_socket_layer(self):
        with self._state_lock:
            if self._socket:
                try:
                    self._socket.shutdown(socket.SHUT_RDWR)
                except socket.error:
                    pass
                self._socket.close()
                self._socket = None
            if self._state not in [ClientState.DISCONNECTED, ClientState.TERMINATED]:
                self._state = ClientState.DISCONNECTED

    def terminate_gracefully(self):
        self._shutdown_event.set()
        self._cleanup_socket_layer()
        if self._receiver_thread and self._receiver_thread.is_alive():
            self._receiver_thread.join(timeout=2.0)
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            self._heartbeat_thread.join(timeout=2.0)
