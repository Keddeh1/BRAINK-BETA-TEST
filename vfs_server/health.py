from __future__ import annotations
import os, sqlite3
from .store import VFSStore

def readiness(store: VFSStore):
    checks={}
    try:
        store.root.mkdir(parents=True,exist_ok=True)
        probe=store.root/".readiness"
        probe.write_bytes(b"ready")
        fd=os.open(probe,os.O_RDONLY)
        try: os.fsync(fd)
        finally: os.close(fd)
        probe.unlink()
        checks["root_writable"]=True
    except Exception as e:
        checks["root_writable"]=False; checks["root_error"]=type(e).__name__
    try:
        with store._connect() as db: db.execute("SELECT 1").fetchone()
        checks["sqlite"]=True
    except Exception as e:
        checks["sqlite"]=False; checks["sqlite_error"]=type(e).__name__
    try:
        chain=store.verify_receipt_chain()
        checks["receipt_chain"]=bool(chain["verified"])
    except Exception as e:
        checks["receipt_chain"]=False; checks["receipt_error"]=type(e).__name__
    return {"ready":all(v is True for k,v in checks.items() if not k.endswith("_error")),"checks":checks}
