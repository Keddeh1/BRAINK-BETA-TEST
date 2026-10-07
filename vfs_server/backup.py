from __future__ import annotations
import argparse, hashlib, json, shutil, sqlite3, tarfile, tempfile, time
from pathlib import Path

def sha256(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def create_backup(root, output):
    root=Path(root); output=Path(output)
    with tempfile.TemporaryDirectory() as td:
        td=Path(td); dbcopy=td/"vfs.sqlite3"
        src=sqlite3.connect(root/"vfs.sqlite3"); dst=sqlite3.connect(dbcopy)
        with dst: src.backup(dst)
        src.close(); dst.close()
        manifest={"created_at":time.time(),"database_sha256":sha256(dbcopy),"objects":[]}
        objects=root/"objects"
        if objects.exists():
            for p in sorted(x for x in objects.rglob("*") if x.is_file()):
                manifest["objects"].append({"path":str(p.relative_to(root)),"sha256":sha256(p),"size":p.stat().st_size})
        (td/"backup-manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2))
        with tarfile.open(output,"w:gz") as tar:
            tar.add(dbcopy,arcname="vfs.sqlite3")
            tar.add(td/"backup-manifest.json",arcname="backup-manifest.json")
            if objects.exists(): tar.add(objects,arcname="objects")
    return output

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--root",required=True); ap.add_argument("--output",required=True)
    a=ap.parse_args(); print(create_backup(a.root,a.output))
if __name__=="__main__": main()
