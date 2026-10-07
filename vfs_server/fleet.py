"""VFS_SERVER allocator and A/B structural compression carrier."""
from __future__ import annotations
import hashlib,json,re,sqlite3,time,uuid,zlib
from pathlib import Path
from .model import ArtifactWrite
from .store import VFSStore

MAX_SIDE_BYTES=32*1024*1024
MAX_LABEL=160
ID_PATTERN=re.compile(r"[0-9a-f]{32}\Z")

def digest(data): return hashlib.sha256(data).hexdigest()

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
                vfs_id TEXT PRIMARY KEY, label TEXT NOT NULL, source_ref TEXT NOT NULL,
                quota_bytes INTEGER NOT NULL, state TEXT NOT NULL, created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS ab_entries(
                entry_id TEXT PRIMARY KEY, vfs_id TEXT NOT NULL, source_ref TEXT NOT NULL,
                a_digest TEXT NOT NULL, b_digest TEXT NOT NULL,
                a_object_digest TEXT NOT NULL, b_object_digest TEXT NOT NULL,
                b_codec TEXT NOT NULL, a_bytes INTEGER NOT NULL, b_bytes INTEGER NOT NULL,
                stored_bytes INTEGER NOT NULL, created_at REAL NOT NULL,
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
    def allocate(self,label,source_ref,quota_bytes=64*1024*1024):
        if not isinstance(label,str) or not label.strip() or len(label)>MAX_LABEL: raise ValueError("invalid_label")
        if not isinstance(source_ref,str) or not source_ref.strip() or len(source_ref)>512: raise ValueError("invalid_source_ref")
        if type(quota_bytes) is not int or not MAX_SIDE_BYTES<=quota_bytes<=1024*1024*1024: raise ValueError("invalid_quota")
        vfs_id=uuid.uuid4().hex
        at=time.time()
        with self._connect() as db:
            db.execute("INSERT INTO allocations VALUES(?,?,?,?,?,?)",
                       (vfs_id,label.strip(),source_ref.strip(),quota_bytes,"ALLOCATED",at))
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
    def _unpack(self,packed,expected_length):
        if expected_length>MAX_SIDE_BYTES: raise ValueError("side_too_large")
        decoder=zlib.decompressobj()
        raw=decoder.decompress(packed,expected_length+1)
        if len(raw)!=expected_length or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
            raise ValueError("invalid_ab_frame")
        return raw
    def admit_ab(self,vfs_id,a,b,source_ref):
        allocation=self.get(vfs_id)
        if allocation["state"]!="ALLOCATED": raise ValueError("vfs_not_active")
        if not isinstance(source_ref,str) or not source_ref.strip() or len(source_ref)>512: raise ValueError("invalid_source_ref")
        if not isinstance(a,bytes) or not isinstance(b,bytes): raise ValueError("bytes_required")
        if len(a)>MAX_SIDE_BYTES or len(b)>MAX_SIDE_BYTES: raise ValueError("side_too_large")
        a_digest,b_digest=digest(a),digest(b)
        # A is a compressed baseline. B is a reference when identical, otherwise a compressed candidate.
        a_frame=zlib.compress(a,level=9)
        b_codec="reference:A" if a_digest==b_digest else "zlib"
        b_frame=b"" if b_codec=="reference:A" else zlib.compress(b,level=9)
        if b_codec=="zlib" and len(a)==len(b):
            delta=zlib.compress(bytes(x ^ y for x,y in zip(a,b)),level=9)
            if len(delta)<len(b_frame): b_codec,b_frame="xor+zlib",delta
        stored_bytes=len(a_frame)+len(b_frame)
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                used=db.execute("SELECT COALESCE(SUM(stored_bytes),0) AS n FROM ab_entries WHERE vfs_id=?",(vfs_id,)).fetchone()["n"]
                if used+stored_bytes>allocation["quota_bytes"]: raise ValueError("vfs_quota_exceeded")
                entry_id=uuid.uuid4().hex
                store=self.store(vfs_id)
                a_rec,a_receipt=store.write(ArtifactWrite(f"/ab/{entry_id}/A.zlib",a_frame,source_ref,media_type="application/zlib"))
                if b_codec=="reference:A":
                    b_rec,b_receipt=a_rec,a_receipt
                else:
                    b_rec,b_receipt=store.write(ArtifactWrite(f"/ab/{entry_id}/B.zlib",b_frame,source_ref,media_type="application/zlib"))
                # Verify both frames before the allocation registry exposes the admission.
                if self._unpack(store.read_content(a_rec.digest),len(a))!=a: raise RuntimeError("a_readback_mismatch")
                if b_codec!="reference:A":
                    decoded=self._unpack(store.read_content(b_rec.digest),len(b))
                    recovered=bytes(x ^ y for x,y in zip(a,decoded)) if b_codec=="xor+zlib" else decoded
                    if recovered!=b: raise RuntimeError("b_readback_mismatch")
                at=time.time()
                db.execute("INSERT INTO ab_entries VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                           (entry_id,vfs_id,source_ref,a_digest,b_digest,a_rec.digest,b_rec.digest,b_codec,len(a),len(b),stored_bytes,at))
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise
        return {"entry":self.entry(vfs_id,entry_id),"actor_receipts":[a_receipt.as_dict()]+([] if b_codec=="reference:A" else [b_receipt.as_dict()]),
                "verification":"PENDING_OBSERVER_READBACK"}
    def entry(self,vfs_id,entry_id):
        self.get(vfs_id)
        _id(entry_id)
        with self._connect() as db:
            row=db.execute("SELECT * FROM ab_entries WHERE vfs_id=? AND entry_id=?",(vfs_id,entry_id)).fetchone()
        if row is None: raise KeyError("ab_entry_not_found")
        return dict(row)
    def read_ab(self,vfs_id,entry_id,observe=False):
        entry=self.entry(vfs_id,entry_id)
        store=self.store(vfs_id)
        a=self._unpack(store.read_content(entry["a_object_digest"]),entry["a_bytes"])
        if entry["b_codec"]=="reference:A": b=a
        else:
            decoded=self._unpack(store.read_content(entry["b_object_digest"]),entry["b_bytes"])
            b=bytes(x ^ y for x,y in zip(a,decoded)) if entry["b_codec"]=="xor+zlib" else decoded
        if digest(a)!=entry["a_digest"] or digest(b)!=entry["b_digest"]: raise RuntimeError("ab_digest_mismatch")
        result={"entry":entry,"a_b64":__import__("base64").b64encode(a).decode(),"b_b64":__import__("base64").b64encode(b).decode(),
                "verified":True,"compression":{"source_bytes":len(a)+len(b),"stored_bytes":entry["stored_bytes"],"b_codec":entry["b_codec"]}}
        if observe:
            result["observer_receipts"]=[store.verify(entry["a_object_digest"])["receipt"]]
            if entry["b_object_digest"]!=entry["a_object_digest"]:
                result["observer_receipts"].append(store.verify(entry["b_object_digest"])["receipt"])
        return result
    def status(self):
        with self._connect() as db:
            vfs=db.execute("SELECT COUNT(*) AS n FROM allocations").fetchone()["n"]
            entries=db.execute("SELECT COUNT(*) AS n FROM ab_entries").fetchone()["n"]
        return {"server":"VFS_SERVER","role":"VFS_ALLOCATOR","instances":vfs,"ab_entries":entries,
                "classification":"KEDDEH_SERVICE"}
