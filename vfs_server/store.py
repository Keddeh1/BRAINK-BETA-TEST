from __future__ import annotations
import hashlib,json,os,sqlite3,tempfile,time,re
from contextlib import contextmanager
from pathlib import Path,PurePosixPath
from .model import ArtifactWrite,ArtifactRecord,Receipt

MAX_ARTIFACT_BYTES=64*1024*1024

def canonical_json(obj): return json.dumps(obj,sort_keys=True,separators=(",",":")).encode()
def sha256_bytes(data): return hashlib.sha256(data).hexdigest()
def normalize_vfs_path(value):
    if not isinstance(value,str) or not value or len(value)>4096 or "\x00" in value: raise ValueError("invalid_path")
    p=PurePosixPath("/"+value.lstrip("/"))
    if ".." in p.parts: raise ValueError("path_traversal")
    return str(p)

class VFSStore:
    def __init__(self,root):
        self.root=Path(root); self.objects=self.root/"objects"; self.objects.mkdir(parents=True,exist_ok=True)
        self.db_path=self.root/"vfs.sqlite3"; self._init_db()
    @contextmanager
    def _connect(self):
        db=sqlite3.connect(self.db_path,timeout=30,isolation_level=None)
        db.execute("PRAGMA journal_mode=WAL"); db.execute("PRAGMA synchronous=FULL"); db.row_factory=sqlite3.Row
        try:yield db
        finally:db.close()
    def _init_db(self):
        with self._connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS artifacts(digest TEXT PRIMARY KEY,path TEXT NOT NULL,source TEXT NOT NULL,predecessor TEXT,media_type TEXT NOT NULL,size INTEGER NOT NULL,created_at REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS paths(path TEXT PRIMARY KEY,digest TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS bindings(path TEXT PRIMARY KEY,digest TEXT NOT NULL,source TEXT NOT NULL,predecessor TEXT,media_type TEXT NOT NULL,size INTEGER NOT NULL,created_at REAL NOT NULL);
            INSERT OR IGNORE INTO bindings SELECT p.path,a.digest,a.source,a.predecessor,a.media_type,a.size,a.created_at FROM paths p JOIN artifacts a ON a.digest=p.digest;
            CREATE TABLE IF NOT EXISTS lineage(child_digest TEXT NOT NULL,parent_digest TEXT NOT NULL,relation TEXT NOT NULL,PRIMARY KEY(child_digest,parent_digest,relation));
            CREATE TABLE IF NOT EXISTS receipts(seq INTEGER PRIMARY KEY AUTOINCREMENT,receipt_id TEXT UNIQUE NOT NULL,kind TEXT NOT NULL,status TEXT NOT NULL,artifact_digest TEXT,path TEXT,previous_receipt_digest TEXT,receipt_digest TEXT UNIQUE NOT NULL,at REAL NOT NULL,detail_json TEXT NOT NULL);
            """)
    def _object_path(self,d):
        if not isinstance(d,str) or re.fullmatch("[0-9a-f]{64}",d) is None:raise ValueError("invalid_digest")
        return self.objects/d[:2]/d[2:4]/d
    def _write_object_atomic(self,digest,content):
        target=self._object_path(digest)
        if target.exists():
            if sha256_bytes(target.read_bytes())!=digest: raise RuntimeError("object_digest_conflict")
            return
        target.parent.mkdir(parents=True,exist_ok=True)
        fd,tmp=tempfile.mkstemp(prefix=".write-",dir=target.parent)
        try:
            with os.fdopen(fd,"wb") as f: f.write(content); f.flush(); os.fsync(f.fileno())
            os.replace(tmp,target)
            dirfd=os.open(target.parent,os.O_RDONLY)
            try: os.fsync(dirfd)
            finally: os.close(dirfd)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
    def _last_receipt(self,db):
        r=db.execute("SELECT receipt_digest FROM receipts ORDER BY seq DESC LIMIT 1").fetchone()
        return r["receipt_digest"] if r else None
    def _receipt(self,db,kind,status,digest,path,detail):
        prev=self._last_receipt(db); at=time.time()
        body={"kind":kind,"status":status,"artifact_digest":digest,"path":path,"previous_receipt_digest":prev,"at":at,"detail":detail}
        rd=sha256_bytes(canonical_json(body)); rid=f"{kind}:{rd[:24]}"
        db.execute("INSERT INTO receipts(receipt_id,kind,status,artifact_digest,path,previous_receipt_digest,receipt_digest,at,detail_json) VALUES(?,?,?,?,?,?,?,?,?)",(rid,kind,status,digest,path,prev,rd,at,json.dumps(detail,sort_keys=True)))
        return Receipt(rid,kind,status,digest,path,prev,rd,at,detail)
    def write(self,req:ArtifactWrite):
        path=normalize_vfs_path(req.path)
        if len(req.content)>MAX_ARTIFACT_BYTES: raise ValueError("artifact_too_large")
        if not isinstance(req.content,bytes):raise ValueError("content_must_be_bytes")
        if not isinstance(req.source,str) or not req.source:raise ValueError("source_required")
        if not isinstance(req.media_type,str) or not req.media_type:raise ValueError("media_type_required")
        if req.predecessor is not None:self._object_path(req.predecessor)
        digest=sha256_bytes(req.content); self._write_object_atomic(digest,req.content); created=time.time()
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("INSERT OR IGNORE INTO artifacts VALUES(?,?,?,?,?,?,?)",(digest,path,req.source,req.predecessor,req.media_type,len(req.content),created))
                if req.predecessor:
                    if not db.execute("SELECT 1 FROM artifacts WHERE digest=?",(req.predecessor,)).fetchone(): raise ValueError("unknown_predecessor")
                    db.execute("INSERT OR IGNORE INTO lineage VALUES(?,?,'predecessor')",(digest,req.predecessor))
                db.execute("INSERT INTO paths(path,digest) VALUES(?,?) ON CONFLICT(path) DO UPDATE SET digest=excluded.digest",(path,digest))
                db.execute("INSERT INTO bindings VALUES(?,?,?,?,?,?,?) ON CONFLICT(path) DO UPDATE SET digest=excluded.digest,source=excluded.source,predecessor=excluded.predecessor,media_type=excluded.media_type,size=excluded.size,created_at=excluded.created_at",(path,digest,req.source,req.predecessor,req.media_type,len(req.content),created))
                receipt=self._receipt(db,"VFS_ARTIFACT_WRITE","COMMITTED",digest,path,{"source":req.source,"size":len(req.content),"predecessor":req.predecessor})
                db.execute("COMMIT")
            except Exception: db.execute("ROLLBACK"); raise
        return ArtifactRecord(digest,path,req.source,req.predecessor,req.media_type,len(req.content),created),receipt
    def get_artifact(self,digest):
        with self._connect() as db:r=db.execute("SELECT * FROM artifacts WHERE digest=?",(digest,)).fetchone()
        return ArtifactRecord(**dict(r)) if r else None
    def read_content(self,digest):
        if not self.get_artifact(digest): raise KeyError("artifact_not_found")
        data=self._object_path(digest).read_bytes()
        if sha256_bytes(data)!=digest: raise RuntimeError("readback_digest_mismatch")
        return data
    def resolve_path(self,path):
        path=normalize_vfs_path(path)
        with self._connect() as db:r=db.execute("SELECT * FROM bindings WHERE path=?",(path,)).fetchone()
        return ArtifactRecord(**dict(r)) if r else None
    def lineage(self,digest):
        with self._connect() as db:rs=db.execute("SELECT parent_digest,relation FROM lineage WHERE child_digest=? ORDER BY parent_digest",(digest,)).fetchall()
        return [dict(x) for x in rs]
    def verify(self,digest):
        rec=self.get_artifact(digest)
        if not rec: raise KeyError("artifact_not_found")
        data=self.read_content(digest); observed=sha256_bytes(data); ok=observed==digest
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                receipt=self._receipt(db,"OBSERVER_VFS_READBACK","VISIBLE" if ok else "CONTRADICTION",digest,rec.path,{"expected_digest":digest,"observed_digest":observed,"size":len(data)})
                db.execute("COMMIT")
            except Exception: db.execute("ROLLBACK"); raise
        return {"verified":ok,"artifact":rec.as_dict(),"receipt":receipt.as_dict()}
    def verify_receipt_chain(self):
        with self._connect() as db:
            rows=db.execute("SELECT * FROM receipts ORDER BY seq").fetchall()
        previous=None
        for row in rows:
            detail=json.loads(row["detail_json"])
            body={"kind":row["kind"],"status":row["status"],"artifact_digest":row["artifact_digest"],
                  "path":row["path"],"previous_receipt_digest":row["previous_receipt_digest"],
                  "at":row["at"],"detail":detail}
            observed=sha256_bytes(canonical_json(body))
            if row["previous_receipt_digest"] != previous or observed != row["receipt_digest"]:
                return {"verified":False,"failed_seq":row["seq"],"count":len(rows)}
            previous=row["receipt_digest"]
        return {"verified":True,"count":len(rows),"head":previous}

    def status(self):
        with self._connect() as db:
            vals=[db.execute(f"SELECT COUNT(*) n FROM {t}").fetchone()["n"] for t in ("artifacts","paths","lineage","receipts")]
        return {"server":"VFS_SERVER","module":"WM.DEPLOY_VIRTUAL_SPACE.R1","adapter":"adapter://vfs/artifact-write","artifacts":vals[0],"paths":vals[1],"lineage_edges":vals[2],"receipts":vals[3]}
