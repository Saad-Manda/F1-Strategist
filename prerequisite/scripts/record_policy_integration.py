"""Record actual local optional M6 verification; explicitly run with --write."""
import argparse,datetime,hashlib,json,subprocess,sys
from build_catalog import LABS

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true',required=True);p.parse_args()
    folder=LABS/'downloads'/'p9-ppo'
    run=subprocess.run([sys.executable,'compare.py','--candidate','solution.py','--integration'],cwd=folder,capture_output=True,text=True,timeout=180)
    if run.returncode:raise SystemExit(run.stdout+run.stderr)
    data=json.loads(run.stdout)
    data.update(schemaVersion=1,recordedAt=datetime.datetime.now(datetime.timezone.utc).isoformat(),sourceHashes={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in ('compare.py','solution.py','exercise_common.py')})
    target=LABS/'fixtures'/'p9-ppo-integration.json';target.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    print(f'Recorded {data["actual_transitions"]} training transitions and actual spawn results on {data["platform"]}.')
