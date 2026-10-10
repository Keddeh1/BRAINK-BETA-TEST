from __future__ import annotations
import argparse, hashlib, json, shutil, sqlite3, tarfile, tempfile, time, os, re
from pathlib import Path

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def create_backup(root, output):
    root=Path(root); output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); dbcopy=td/"vfs.sqlite3"
        src=sqlite3.connect(root/"vfs.sqlite3"); dst=sqlite3.connect(dbcopy)
        try:
            with dst: src.backup(dst)
            digests=[r[0] for r in dst.execute("SELECT digest FROM artifacts ORDER BY digest")]
        finally:src.close(); dst.close()
        manifest={"created_at":time.time(),"database_sha256":sha256(dbcopy),"objects":[],"scope":"committed database snapshot carriers only"}
        for digest in digests:
            if re.fullmatch("[0-9a-f]{64}",digest) is None:raise ValueError("invalid_snapshot_digest")
            relative=Path("objects")/digest[:2]/digest[2:4]/digest
            target=td/relative;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(root/relative,target)
            if sha256(target)!=digest:raise ValueError("snapshot_carrier_digest_mismatch")
            manifest["objects"].append({"path":str(relative),"sha256":digest,"size":target.stat().st_size})
        (td/"backup-manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2))
        fd,tmp=tempfile.mkstemp(prefix=".backup-",dir=output.parent);os.close(fd)
        try:
            with tarfile.open(tmp,"w:gz") as tar:
                tar.add(dbcopy,arcname="vfs.sqlite3")
                tar.add(td/"backup-manifest.json",arcname="backup-manifest.json")
                if (td/"objects").exists():tar.add(td/"objects",arcname="objects")
            with open(tmp,"rb") as f:os.fsync(f.fileno())
            os.replace(tmp,output)
            directory=os.open(output.parent,os.O_RDONLY)
            try:os.fsync(directory)
            finally:os.close(directory)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    return output

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",required=True); ap.add_argument("--output",required=True)
    a=ap.parse_args(); print(create_backup(a.root,a.output))
if __name__=="__main__": main()
