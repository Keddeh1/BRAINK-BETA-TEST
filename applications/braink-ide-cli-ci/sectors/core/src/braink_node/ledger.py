"""Transactional local event ledger implementing the uploaded append interface.

This is an application adapter, not an implementation of the owner KEX ledger.
The hash chain detects edits when verified; it is not externally anchored.
"""
import sqlite3
from pathlib import Path
from typing import Any, Dict
import json

from .canonical import canonical_bytes, sha256_hex


class LedgerStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS events (sequence INTEGER PRIMARY KEY, "
                       "event_ref TEXT UNIQUE NOT NULL, body TEXT NOT NULL)")

    def _connect(self):
        return sqlite3.connect(self.path, timeout=30)

    def append(self, *, event_type: str, route: str, payload: Dict[str, Any]) -> str:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT sequence, event_ref FROM events "
                                  "ORDER BY sequence DESC LIMIT 1").fetchone()
            sequence = previous[0] + 1 if previous else 1
            body = {"sequence": sequence, "previous_ref": previous[1] if previous else None,
                    "event_type": event_type, "route": route, "payload": payload}
            data = canonical_bytes(body)
            ref = sha256_hex(data)
            db.execute("INSERT INTO events VALUES (?, ?, ?)", (sequence, ref, data.decode()))
        return ref

    def verify(self) -> Dict[str, Any]:
        previous = None
        count = 0
        with self._connect() as db:
            for sequence, ref, raw in db.execute("SELECT * FROM events ORDER BY sequence"):
                body = json.loads(raw)
                if (sequence != count + 1 or body.get("sequence") != sequence or
                        body.get("previous_ref") != previous or
                        sha256_hex(canonical_bytes(body)) != ref):
                    raise ValueError(f"Ledger integrity failure at sequence {sequence}")
                previous = ref
                count += 1
        return {"ok": True, "event_count": count, "head": previous}
