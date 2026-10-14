"""Execute the triad contract on the owner's CI, retaining a failed SLA receipt."""
import argparse
import json
from pathlib import Path
import sys
from braink_ci.runner import CIRunner
from braink_node.ledger import LedgerStore


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--config',type=Path,required=True);p.add_argument('--address',required=True);args=p.parse_args()
    source=Path(__file__).resolve().parent
    pipeline={'schema':'braink.ci.pipeline.v1','name':'triad-grpc-calibrated-contract','sector':'triad-mesh','stages':[
      {'name':'syntax','command':['{python}','-m','compileall','-q','.']},
      {'name':'protobuf','command':['{python}','-m','grpc_tools.protoc','-I','.','--python_out={artifacts}','--grpc_python_out={artifacts}','triad_mesh.proto']},
      {'name':'calibration-regression','command':['{python}','-m','unittest','discover','-s','.','-p','test_calibration.py','-v']},
      {'name':'live-contract','command':['{python}','qualify_live.py','--config',str(args.config.resolve()),'--address',args.address,'--output','{artifacts}/live.json'],'timeout':120},
      {'name':'latency-acceptance','command':['{python}','-c',"import json,sys; r=json.load(open(sys.argv[1])); print(json.dumps(r['latency'])); sys.exit(0 if r['latency']['acceptance']=='PASS' else 1)",'{artifacts}/live.json']} ]}
    runner=CIRunner(args.root/'ci',LedgerStore(args.root/'ledger.sqlite3'),python=sys.executable)
    job=runner.submit(source,pipeline)
    while runner.get(job['id'])['status']=='queued':runner.execute_next()
    report=runner.get(job['id']);runner.verify_report(report)
    print(json.dumps(report,indent=2));return 0 if report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
