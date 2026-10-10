"""Observed same-host language parity and live service measurements."""
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import subprocess
import tempfile
import time

from consilience import aggregate
from diagnostic_probe import probe
from hci import RuntimePanel, render


def stats(values):
    ordered = sorted(values)
    return {'samples':len(values),'min_ns':ordered[0], 'max_ns':ordered[-1],
            'p95_ns':ordered[math.ceil(.95*len(ordered))-1],
            'mean_ns':sum(ordered)//len(ordered)}


def parity():
    root=Path(__file__).parent
    randomizer=random.Random(9241110)
    vectors=[[],[1],[2],[3],[4],[1,2,3,4]] + [
        [randomizer.randint(1,4) for _ in range(randomizer.randint(1,150))] for _ in range(24)]
    with tempfile.TemporaryDirectory() as temporary:
        binary=str(Path(temporary)/'consilience')
        subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(root/'consilience.cpp'),'-o',binary],check=True)
        results=[]
        for levels in vectors:
            expected=aggregate(levels)['raw_q32']
            js=int(subprocess.check_output(['node',str(root/'consilience.mjs'),json.dumps(levels)],text=True))
            cpp=int(subprocess.check_output([binary,*map(str,levels)],text=True))
            assert expected==js==cpp
            results.append({'levels':levels,'raw_q32':str(expected)})
    return {'cases':len(results),'implementations':['Python int','Node BigInt','C++ int64_t'],
            'host_machine':platform.machine(),'host_system':platform.system(),
            'scope':'Same-host integer parity; does not establish ARM64/WASM or independent attestation',
            'vectors':results}


def performance(name):
    root=Path('/workspace/braink-setup/families/SERVERSPACE/runtime/substrate-'+name)
    panel=RuntimePanel(root,'serverspace/substrate-'+name)
    initial=panel.read()
    api=json.loads((root/'api.json').read_text())
    handshake_times=[];api_times=[];render_times=[]
    for _ in range(32):
        start=time.perf_counter_ns(); frame=panel.read(); handshake_times.append(time.perf_counter_ns()-start)
        start=time.perf_counter_ns(); result=probe('http://127.0.0.1:'+str(api['port'])+'/api/substrate'); api_times.append(time.perf_counter_ns()-start)
        assert result['http_status']==200 and result['response_json']['readiness_mask']==7
        start=time.perf_counter_ns(); text=render(frame,83);render_times.append(time.perf_counter_ns()-start)
        assert all(len(line)==83 for line in text.splitlines())
        assert frame['peer_identity']['pid']==initial['peer_identity']['pid']
        assert {k:v['pid'] for k,v in frame['state']['workers'].items()}=={
            k:v['pid'] for k,v in initial['state']['workers'].items()}
    final=panel.read()
    rss={}
    for name, worker in final['state']['workers'].items():
        lines=Path('/proc/'+str(worker['pid'])+'/status').read_text().splitlines()
        rss[name]=int(next(line for line in lines if line.startswith('VmRSS:')).split()[1])*1024
        assert rss[name]<worker['resource_limits']['address_space_bytes']
    return {'identity':final['state']['I'],'samples':32,'readiness_mask':7,
            'daemon_and_worker_pids_unchanged':True,
            'handshake':stats(handshake_times),'api_roundtrip':stats(api_times),
            'python_frame_composition':stats(render_times),'worker_rss_bytes':rss,
            'sampled_api_roundtrip_under_50ms':max(api_times)<=50_000_000,
            'sampled_frame_composition_under_16_6ms':max(render_times)<=16_600_000,
            'before_q':initial['state']['q'],'after_q':final['state']['q'],
            'limits':'No DMA, browser paint, global process-spawn trace, power-loss or latency-guarantee claim'}


if __name__=='__main__':
    root=Path(__file__).parent
    print(json.dumps({'schema':'keddeh.six-phase-observations.v1','observed_at':time.time(),
        'guide_sha256':hashlib.sha256((root/'reference/supplied-six-phase-guide.txt').read_bytes()).hexdigest(),
        'timer':'Python perf_counter_ns; monotonic host timer, not a claimed hardware cycle counter',
        'parity':parity(),'performance':[performance(name) for name in ('auth-canary','replica','primary')]},indent=2))
