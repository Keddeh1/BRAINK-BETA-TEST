"""Owner-local transport enrollment; these credentials are not KEX state seeds."""
import datetime
import ipaddress
import json
import os
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import rsa,ed25519
from cryptography.x509.oid import NameOID,ExtendedKeyUsageOID


def enroll(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True,mode=0o700)
    if (root/'authority.public').exists():
        private=ed25519.Ed25519PrivateKey.from_private_bytes((root/'authority.key').read_bytes())
        if private.public_key().public_bytes_raw().hex()!=(root/'authority.public').read_text():raise ValueError('Enrolled authority differs')
        return (root/'authority.public').read_text()
    if any(root.iterdir()):raise ValueError('Partial enrollment retained; reconcile rather than overwrite credentials')
    now=datetime.datetime.now(datetime.timezone.utc)
    ca_key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    ca_name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Keddeh triad local transport CA')])
    ca=x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name).public_key(ca_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=1)).not_valid_after(now+datetime.timedelta(days=30)).add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True).sign(ca_key,hashes.SHA256())
    values={'ca.key':ca_key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption()),'ca.pem':ca.public_bytes(serialization.Encoding.PEM)}
    for role in ['server','client']:
        key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'localhost' if role=='server' else 'triad-owner-client')])
        builder=x509.CertificateBuilder().subject_name(name).issuer_name(ca_name).public_key(key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(now-datetime.timedelta(minutes=1)).not_valid_after(now+datetime.timedelta(days=7)).add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True).add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH if role=='server' else ExtendedKeyUsageOID.CLIENT_AUTH]),critical=False)
        if role=='server':builder=builder.add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost'),x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]),critical=False)
        cert=builder.sign(ca_key,hashes.SHA256())
        values[role+'.key']=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption());values[role+'.pem']=cert.public_bytes(serialization.Encoding.PEM)
    authority=ed25519.Ed25519PrivateKey.generate()
    values['authority.key']=authority.private_bytes_raw();values['authority.public']=authority.public_key().public_bytes_raw().hex().encode()
    for name,value in values.items():
        with os.fdopen(os.open(root/name,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600),'wb') as stream:stream.write(value);stream.flush();os.fsync(stream.fileno())
    fd=os.open(root,os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    return values['authority.public'].decode()
