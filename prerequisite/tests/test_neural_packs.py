"""Verify extracted M4 packs and provenance independently of chart score ordering."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile
import pytest

ROOT=Path(__file__).resolve().parents[1]
LABS=ROOT/'site'/'labs'
sys.path.insert(0,str(ROOT/'scripts'))
KEYS=('p5-network','p5-stability','p5-double-dueling','p5-per')

@pytest.mark.parametrize('key',KEYS)
def test_extracted_reference_broken_and_incomplete_candidates(key,tmp_path):
    with zipfile.ZipFile(LABS/'downloads'/f'{key}.zip') as z:z.extractall(tmp_path)
    folder=tmp_path/key
    def run(*args):return subprocess.run([sys.executable,*args],cwd=folder,capture_output=True,text=True,timeout=90)
    assert run('checks.py','--candidate','solution.py').returncode==0
    # Broken demo must run; a failing check must reflect a defect, not syntax/import failure.
    demo=run('broken.py');assert demo.returncode==0,demo.stdout+demo.stderr
    fail=run('checks.py','--candidate','broken.py');assert fail.returncode==1 and 'AssertionError' in fail.stdout
    incomplete=run('starter.py');assert incomplete.returncode==1 and 'Exercise incomplete' in incomplete.stdout
    # Checks remain usable after the reference is unavailable.
    (folder/'solution.py').rename(folder/'learner.py')
    passed=run('checks.py','--candidate','learner.py');assert passed.returncode==0,passed.stdout+passed.stderr

def test_generated_neural_artifacts_are_current():
    import build_neural_pages,build_neural_packs,build_neural_readings
    for generator in (build_neural_pages,build_neural_packs,build_neural_readings):
        for path,source in generator.outputs().items():assert path.read_text(encoding='utf-8')==source

def test_recorded_fixture_has_matching_sources_and_equal_budgets():
    d=json.loads((LABS/'fixtures'/'p5-stability-ablation.json').read_text(encoding='utf-8'))
    assert d['schemaVersion']==1 and d['device']=='cpu' and d['settings']['threads']==1
    for name,digest in d['sourceHashes'].items():assert hashlib.sha256((LABS/'downloads'/'p5-stability'/name).read_bytes()).hexdigest()==digest
    assert {(r['seed'],r['variant']) for r in d['runs']}=={(s,v) for s in (7,19,31) for v in ('replay+target','latest+target','replay+online')}
    for r in d['runs']:
        assert r['transitions']==192 and r['optimizer_steps']==48
        assert [c['transitions'] for c in r['checkpoints']]==[32,64,96,128,160,192]
        for c in r['checkpoints']:
            assert c['optimizer_steps']==c['transitions']//4 and c['evaluation_episodes']==4
            assert 0<=c['td_mse']<float('inf') and 0<=c['evaluation_return']<=1

def test_ablation_reproduces_a_recorded_run():
    folder=LABS/'downloads'/'p5-stability'
    # Isolate module names because every standalone pack has its own helpers.
    code='''import json,compare
from checks import load_candidate
print(json.dumps(compare.experiment(load_candidate("solution.py"),7,"replay+target")))'''
    result=subprocess.run([sys.executable,'-c',code],cwd=folder,capture_output=True,text=True,timeout=90)
    assert result.returncode==0,result.stderr
    fixture=json.loads((LABS/'fixtures'/'p5-stability-ablation.json').read_text(encoding='utf-8'))
    expected=next(r for r in fixture['runs'] if r['seed']==7 and r['variant']=='replay+target')
    assert json.loads(result.stdout)==expected

def test_supervised_fit_reports_disjoint_holdout_and_reproducible_budget():
    folder=LABS/'downloads'/'p5-network'
    result=subprocess.run([sys.executable,'compare.py','--candidate','solution.py','--seed','7'],cwd=folder,capture_output=True,text=True,timeout=90)
    assert result.returncode==0,result.stderr
    d=json.loads(result.stdout)
    assert set(d['train_indices']).isdisjoint(d['heldout_indices']) and d['optimizer_steps']==200
    # Fixed supervised labels are exactly representable: unlike RL ablations,
    # a broad fit threshold detects a missing update without seed-score comparisons.
    assert d['final_heldout_mse']<.01 and d['final_heldout_mse']<d['initial_heldout_mse']
