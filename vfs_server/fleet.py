"""VFS_SERVER allocator with per-instance reversible A/B binary graph entries."""
from __future__ import annotations
import re,secrets,sqlite3,time,uuid
from pathlib import Path
from .model import ArtifactWrite
from .store import VFSStore
from .codec import CODEC,encode,decode,graph,proof

ID_PATTERN=re.compile(r"[0-9a-f]{64}\Z")
ENTRY_PATTERN=re.compile(r"[0-9a-f]{32}\Z")

def _id(value):
    if not isinstance(value,str) or not ID_PATTERN.fullmatch(value): raise ValueError("invalid_vfs_id")
    return value

class VFSFleet:
    def __init__(self,root):
        self.root=Path(root)
        self.root.mkdir(parents=True,exist_ok=True)
        self.db_path=self.root/"fleet.sqlite3"
        with self._connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS allocations(
                vfs_id TEXT PRIMARY KEY,label TEXT NOT NULL,source_ref TEXT NOT NULL,
                quota_bytes INTEGER NOT NULL,state TEXT NOT NULL,created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS ab_entries(
                entry_id TEXT PRIMARY KEY,vfs_id TEXT NOT NULL,source_ref TEXT NOT NULL,
                codec TEXT NOT NULL,bits_count INTEGER NOT NULL,object_digest TEXT NOT NULL,
                packed_bytes INTEGER NOT NULL,created_at REAL NOT NULL,
                FOREIGN KEY(vfs_id) REFERENCES allocations(vfs_id));
            CREATE INDEX IF NOT EXISTS ab_by_vfs ON ab_entries(vfs_id,created_at);
            """)
    def _connect(self):
        db=sqlite3.connect(self.db_path,timeout=30,isolation_level=None)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA synchronous=FULL")
        db.execute("PRAGMA foreign_keys=ON")
        db.row_factory=sqlite3.Row
        return db
    def allocate(self,label,source_ref,quota_bytes=1024*1024):
        if not isinstance(label,str) or not label.strip() or len(label)>160: raise ValueError("invalid_label")
        if not isinstance(source_ref,str) or not source_ref.strip() or len(source_ref)>512: raise ValueError("invalid_source_ref")
        if type(quota_bytes) is not int or not 1<=quota_bytes<=1024*1024*1024: raise ValueError("invalid_quota")
        vfs_id=secrets.token_hex(32)
        with self._connect() as db:
            db.execute("INSERT INTO allocations VALUES(?,?,?,?,?,?)",
                       (vfs_id,label.strip(),source_ref.strip(),quota_bytes,"ALLOCATED",time.time()))
        return self.get(vfs_id)
    def get(self,vfs_id):
        _id(vfs_id)
        with self._connect() as db:
            row=db.execute("SELECT * FROM allocations WHERE vfs_id=?",(vfs_id,)).fetchone()
        if row is None: raise KeyError("vfs_not_found")
        return dict(row)
    def list(self):
        with self._connect() as db:
            rows=db.execute("SELECT * FROM allocations ORDER BY created_at,vfs_id").fetchall()
        return [dict(row) for row in rows]
    def store(self,vfs_id):
        self.get(vfs_id)
        return VFSStore(self.root/"instances"/vfs_id)
    def entries(self,vfs_id):
        self.get(vfs_id)
        with self._connect() as db:
            rows=db.execute("SELECT * FROM ab_entries WHERE vfs_id=? ORDER BY created_at,entry_id",(vfs_id,)).fetchall()
        return [dict(row) for row in rows]
    def admit_ab(self,vfs_id,bits,source_ref):
        allocation=self.get(vfs_id)
        if allocation["state"]!="ALLOCATED": raise ValueError("vfs_not_active")
        if not isinstance(source_ref,str) or not source_ref.strip() or len(source_ref)>512: raise ValueError("invalid_source_ref")
        if source_ref.strip()!=allocation["source_ref"]: raise ValueError("source_ref_mismatch")
        packed=encode(bits)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                used=db.execute("SELECT COALESCE(SUM(packed_bytes),0) AS n FROM ab_entries WHERE vfs_id=?",(vfs_id,)).fetchone()["n"]
                if used+len(packed)>allocation["quota_bytes"]: raise ValueError("vfs_quota_exceeded")
                entry_id=uuid.uuid4().hex
                store=self.store(vfs_id)
                artifact,receipt=store.write(ArtifactWrite(f"/ab/{entry_id}/states.bin",packed,source_ref,media_type="application/vnd.keddeh.ab-binary-v1"))
                observed=store.read_content(artifact.digest)
                if decode(observed,len(bits))!=bits: raise RuntimeError("ab_reverse_roundtrip_failed")
                db.execute("INSERT INTO ab_entries VALUES(?,?,?,?,?,?,?,?)",
                           (entry_id,vfs_id,source_ref,CODEC,len(bits),artifact.digest,len(packed),time.time()))
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise
        return {"entry":self.entry(vfs_id,entry_id),"actor_receipt":receipt.as_dict(),
                "graph":graph(packed,len(bits)),"verification":"PENDING_OBSERVER_READBACK"}
    def entry(self,vfs_id,entry_id):
        self.get(vfs_id)
        if not isinstance(entry_id,str) or not ENTRY_PATTERN.fullmatch(entry_id): raise ValueError("invalid_ab_entry_id")
        with self._connect() as db:
            row=db.execute("SELECT * FROM ab_entries WHERE vfs_id=? AND entry_id=?",(vfs_id,entry_id)).fetchone()
        if row is None: raise KeyError("ab_entry_not_found")
        return dict(row)
    def read_ab(self,vfs_id,entry_id,observe=False):
        entry=self.entry(vfs_id,entry_id)
        if entry["codec"]!=CODEC: raise ValueError("unsupported_ab_codec")
        store=self.store(vfs_id)
        packed=store.read_content(entry["object_digest"])
        if len(packed)!=entry["packed_bytes"]: raise RuntimeError("ab_frame_length_mismatch")
        evidence=proof(packed,entry["bits_count"])
        if evidence["sha256"]!=entry["object_digest"]: raise RuntimeError("ab_digest_mismatch")
        result={"entry":entry,"proof":evidence,"graph":graph(packed,entry["bits_count"]),
                "verified":True}
        if observe: result["observer_receipt"]=store.verify(entry["object_digest"])["receipt"]
        return result
    def status(self):
        with self._connect() as db:
            vfs=db.execute("SELECT COUNT(*) AS n FROM allocations").fetchone()["n"]
            entries=db.execute("SELECT COUNT(*) AS n FROM ab_entries").fetchone()["n"]
        return {"server":"VFS_SERVER","role":"VFS_ALLOCATOR","instances":vfs,"ab_entries":entries,
                "codec":CODEC,"classification":"KEDDEH_SERVICE"}
