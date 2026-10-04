"""Explicit author command: generate real versioned CPU ablations, never synthetic curves."""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import platform
import sys
import numpy as np
import torch
from build_catalog import LABS

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true',required=True)
    parser.parse_args()
    folder=LABS/'downloads'/'p5-stability'
    sys.path.insert(0,str(folder))
    spec=importlib.util.spec_from_file_location('ablation',folder/'compare.py')
    ablation=importlib.util.module_from_spec(spec);spec.loader.exec_module(ablation)
    learner=ablation.load_candidate(folder/'solution.py')
    hashes={name:hashlib.sha256((folder/name).read_bytes()).hexdigest() for name in ('solution.py','exercise_common.py','compare.py')}
    fixture=dict(schemaVersion=1,modelVersion='chain-advance-reset-v1',recordedAt=datetime.now(timezone.utc).isoformat(),generator='scripts/record_neural_fixtures.py --write',sourceHashes=hashes,python=platform.python_version(),numpy=np.__version__,torch=torch.__version__,device='cpu',dtype='float64',seeds=[7,19,31],settings=ablation.SETTINGS,evaluation='Frozen greedy policy, four identical starts at state 0, cap 8, no RNG or optimizer updates. Repeated starts are not independent uncertainty estimates.',interpretation='Paired budgets and initialization; policies collect different trajectories. Tiny runs are contextual evidence, not score-order correctness gates.',runs=[ablation.experiment(learner,seed,v) for seed in (7,19,31) for v in ablation.VARIANTS])
    target=LABS/'fixtures'/'p5-stability-ablation.json';target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(fixture,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(f'Recorded {len(fixture["runs"])} actual CPU runs with source hashes: {target}')

if __name__=='__main__':main()
