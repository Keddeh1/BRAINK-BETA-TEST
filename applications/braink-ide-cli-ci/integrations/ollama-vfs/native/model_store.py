"""Attach Ollama's actual content-addressed model store to a native VFS vault."""
import hashlib,json,re
from pathlib import Path
from braink_node.owner_vfs.store import VFSStore
from ollama_node import index_model_file,verify_model_file,retain


def attach_model_store(vault_root,models_root,manifest_path,model,actor):
    root=Path(models_root).resolve(strict=True)
    manifest=(root/manifest_path).resolve(strict=True)
    if not manifest.is_relative_to(root):raise ValueError('Manifest is outside its backing store')
    raw=manifest.read_bytes();document=json.loads(raw)
    if document.get('manifests'):
        raise ValueError('Select the runnable child manifest before indexing its backing blobs')
    layers=[document['config'],*document['layers']]
    verified={}
    for layer in layers:
        digest=layer['digest']
        if not re.fullmatch(r'sha256:[0-9a-fA-F]{64}',digest):raise ValueError('Invalid backing digest')
        digest=digest.lower()
        path=(root/'blobs'/digest.replace(':','-')).resolve(strict=True)
        if not path.is_relative_to(root):raise ValueError('Blob resolves outside its backing store')
        blob_model=model+'@'+digest
        receipt=index_model_file(vault_root,path,blob_model,
            {'source':'OLLAMA_MANIFEST','license_assessment':'NOT_ASSESSED'},actor)
        observed=verify_model_file(vault_root,blob_model)
        if observed['sha256']!=digest.split(':',1)[1] or observed['size']!=layer['size']:
            raise RuntimeError('Ollama manifest blob integrity differs')
        verified[digest]={'model_reference':blob_model,'media_type':layer['mediaType'],
            'size':observed['size'],'receipt_digest':receipt['digest']}
    # Publish complete custody only after every referenced blob has been read back.
    if manifest.read_bytes()!=raw:raise RuntimeError('Model manifest changed during attachment')
    report={'model':model,'manifest_path':str(manifest),'manifest_sha256':hashlib.sha256(raw).hexdigest(),
        'blobs':verified,'unique_backing_bytes':sum(row['size'] for row in verified.values()),
        'custody':'BACKING_VERIFIED','inference_qualification':'NOT_EXECUTED',
        'license_assessment':'NOT_ASSESSED'}
    receipt=retain(vault_root,'/model-stores/'+hashlib.sha256(model.encode()).hexdigest()+'.json',report,actor)
    return {**report,'receipt':receipt}


def verify_model_store(vault_root,model):
    store=VFSStore(vault_root)
    record=store.resolve_path('/model-stores/'+hashlib.sha256(model.encode()).hexdigest()+'.json')
    if record is None:raise ValueError('Model store attachment absent')
    report=json.loads(store.read_content(record.digest))
    if hashlib.sha256(Path(report['manifest_path']).read_bytes()).hexdigest()!=report['manifest_sha256']:
        raise RuntimeError('Attached model manifest changed')
    for digest,row in report['blobs'].items():
        observed=verify_model_file(vault_root,row['model_reference'])
        if observed['sha256']!=digest.split(':',1)[1]:raise RuntimeError('Attached model blob changed')
    return report
