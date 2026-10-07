from __future__ import annotations
import json,tempfile
from .model import ArtifactWrite
from .store import VFSStore,sha256_bytes

def qualify():
    checks=[]
    def record(name,ok,detail=None):
        checks.append({"name":name,"status":"PASS" if ok else "FAIL","detail":detail})
        if not ok: raise AssertionError(name)
    with tempfile.TemporaryDirectory() as root:
        s=VFSStore(root)
        a,actor=s.write(ArtifactWrite("/qualification/a",b"alpha","qualification"))
        record("write_digest",a.digest==sha256_bytes(b"alpha"))
        record("actor_not_verifier",actor.kind=="VFS_ARTIFACT_WRITE")
        obs=s.verify(a.digest)
        record("observer_readback",obs["verified"] and obs["receipt"]["kind"]=="OBSERVER_VFS_READBACK")
        b,_=s.write(ArtifactWrite("/qualification/b",b"beta","qualification",a.digest))
        record("lineage",s.lineage(b.digest)[0]["parent_digest"]==a.digest)
        s2=VFSStore(root)
        record("restart_readback",s2.read_content(a.digest)==b"alpha")
        record("path_readback",s2.resolve_path("/qualification/b").digest==b.digest)
        chain=s2.verify_receipt_chain()
        record("receipt_chain",chain["verified"],chain)
    return {"server":"VFS_SERVER","status":"PASS","checks":checks}

def main():
    print(json.dumps(qualify(),sort_keys=True))
if __name__=="__main__": main()
