"""Owner-enrolled Ed25519 identities for the local ServerSpace UDS handshake.

These are transport credentials, not KEX state seeds or numeric identities.
Each runtime retains separate server/client keys and a pinned enrollment record.
"""
import json
import os
from pathlib import Path
import struct
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey,Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import Encoding,PrivateFormat,PublicFormat,NoEncryption

MAGIC=b'KXA2'
NONCE_BYTES=32
SIGNATURE_BYTES=64
HELLO_BYTES=100

def public(key):return key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw).hex()

def enroll(root,identity):
    root=Path(root).resolve();root.chmod(0o700)
    record=root/'handshake-enrollment.json'
    if record.exists():
        pinned=load(root,identity)
        for role in ('server','client'):
            if public(private(root,role))!=pinned[role+'_public']:raise ValueError('Enrolled credential mismatch')
        return pinned
    keys={}
    for role in ('server','client'):
        path=root/('handshake-'+role+'.key')
        if not path.exists():
            value=Ed25519PrivateKey.generate().private_bytes(Encoding.Raw,PrivateFormat.Raw,NoEncryption())
            with os.fdopen(os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as stream:
                stream.write(value);stream.flush();os.fsync(stream.fileno())
        keys[role+'_public']=public(private(root,role))
    value={'schema':'keddeh.uds-enrollment.v1','identity':identity,'runtime':str(root),**keys}
    with os.fdopen(os.open(record,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'w') as stream:
        json.dump(value,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
    fd=os.open(root,os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return value

def private(root,role):
    path=Path(root)/('handshake-'+role+'.key');stat=path.stat()
    if stat.st_uid!=os.getuid() or stat.st_mode&0o077:raise ValueError('Credential owner or permissions differ')
    return Ed25519PrivateKey.from_private_bytes(path.read_bytes())

def load(root,identity):
    root=Path(root).resolve();value=json.loads((root/'handshake-enrollment.json').read_text())
    if value['identity']!=identity or value['runtime']!=str(root):raise ValueError('Independent runtime context differs')
    return value

def context(identity,client_pid,server_pid,uid):
    return b'KEDDEH-UDS-AUTH-v1\0'+identity.encode()+b'\0'+struct.pack('>QQQ',client_pid,server_pid,uid)

def verify(public_hex,signature,message):
    Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_hex)).verify(signature,message)
