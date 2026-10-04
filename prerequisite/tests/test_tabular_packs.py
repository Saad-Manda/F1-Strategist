"""Validate M3 behaviour, cache lifecycle, isolated packs, and evaluation contracts."""
import json
from pathlib import Path
import subprocess
import sys
import zipfile
import pytest

ROOT=Path(__file__).resolve().parents[1]
PACKS=ROOT/'site/labs/downloads'
IDS=('p4-td','p4-explore','p4-sarsa','p4-bins')

def run(folder,*args):
    return subprocess.run([sys.executable,*args],cwd=folder,capture_output=True,text=True,timeout=30)

def extract(lab_id,tmp_path):
    with zipfile.ZipFile(PACKS/f'{lab_id}.zip') as archive:
        assert len(archive.namelist())==(8 if lab_id=='p4-td' else 9)
        assert all(name.startswith(lab_id+'/') and '__pycache__' not in name for name in archive.namelist())
        archive.extractall(tmp_path)
    return tmp_path/lab_id

@pytest.mark.parametrize('lab_id',IDS)
def test_standalone_solution_passes_and_broken_and_starter_fail(lab_id,tmp_path):
    folder=extract(lab_id,tmp_path)
    reference=run(folder,'checks.py','--candidate','solution.py')
    assert reference.returncode==0,reference.stdout+reference.stderr
    for candidate in ('solution.py','broken.py'):
        result=run(folder,candidate)
        assert result.returncode==0,result.stdout+result.stderr
        json.loads(result.stdout)
    broken=run(folder,'checks.py','--candidate','broken.py')
    assert broken.returncode==1 and 'FAIL: AssertionError:' in broken.stdout
    starter=run(folder,'starter.py')
    assert starter.returncode==1 and 'Exercise incomplete:' in starter.stdout
    assert run(folder,'checks.py','--candidate','starter.py').returncode==1

@pytest.mark.parametrize('lab_id',IDS[1:])
def test_seeded_comparison_has_separate_frozen_evaluation_and_visible_budgets(lab_id,tmp_path):
    folder=extract(lab_id,tmp_path)
    args=('compare.py','--candidate','solution.py','--episodes','200','--seeds','7,31','--epsilon','0.2','--alpha','0.1')
    a,b=run(folder,*args),run(folder,*args)
    assert a.returncode==b.returncode==0,a.stdout+a.stderr
    assert a.stdout==b.stdout,'same local seeds must reproduce the entire run'
    result=json.loads(a.stdout)
    assert result['training']['episodes']==200 and result['training']['epsilon']==0.2
    assert result['training']['transitions_per_seed']==(400 if lab_id=='p4-sarsa' else 200)
    assert result['evaluation']['epsilon']==0 and result['evaluation']['frozen_q'] is True
    assert len(result['runs'])==(6 if lab_id=='p4-bins' else 4)
    for sample in result['runs']:
        assert sample['seed'] in (7,31)
        lo,hi=(-10,6) if lab_id=='p4-sarsa' else (0,1)
        assert lo<=sample['training_mean']<=hi and lo<=sample['evaluation_mean']<=hi
        if lab_id=='p4-explore':
            assert sum(sample['visits'])==200 and sample['visits'][2]==0
            assert sum(sample['eval_visits'])==200 and sample['eval_visits'][2]==0
        if lab_id=='p4-bins':
            assert sample['evaluation_mean']<=sample['representation_ceiling']+1e-9
            if sample['variant']=='coarse':assert sample['evaluation_mean']==0.5
    for label,summary in result['summary'].items():
        records=[r for r in result['runs'] if r['variant']==label]
        assert summary['evaluation_mean']==sum(r['evaluation_mean'] for r in records)/len(records)
    failed=run(folder,'compare.py','--candidate','solution.py','--epsilon','1.1')
    assert failed.returncode==1 and 'invalid settings' in failed.stdout
    incomplete=run(folder,'compare.py','--candidate','starter.py')
    assert incomplete.returncode==1 and 'Exercise incomplete' in incomplete.stdout

def test_alternative_td_implementation_passes_without_solution(tmp_path):
    folder=extract('p4-td',tmp_path)
    (folder/'solution.py').unlink()
    (folder/'alternate.py').write_text('''from exercise_common import validate_distribution, legal_indices
import math
def update(q,reward,next_values,legal,alpha,gamma,terminated,truncated=False):
    validate_distribution([alpha,1-alpha]);validate_distribution([gamma,1-gamma])
    if not math.isfinite(q) or not math.isfinite(reward):raise ValueError('invalid scalar')
    target=reward
    if not terminated:
        allowed=sorted(next_values[i] for i in legal_indices(next_values,legal))
        target+=gamma*allowed[-1]
    return {'target':target,'error':target-q,'value':(1-alpha)*q+alpha*target}
''',encoding='utf-8')
    result=run(folder,'checks.py','--candidate','alternate.py')
    assert result.returncode==0,result.stdout+result.stderr

def test_m3_authoring_drift():
    for script in ('build_tabular_pages.py','build_tabular_packs.py'):
        result=run(ROOT,f'scripts/{script}')
        assert result.returncode==0,result.stdout+result.stderr
