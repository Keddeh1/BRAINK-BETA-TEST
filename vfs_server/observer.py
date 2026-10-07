import argparse,json
from .store import VFSStore
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("digest"); ap.add_argument("--root",default=".vfs-server")
    a=ap.parse_args(); result=VFSStore(a.root).verify(a.digest)
    print(json.dumps(result,sort_keys=True)); raise SystemExit(0 if result["verified"] else 1)
if __name__=="__main__":main()
