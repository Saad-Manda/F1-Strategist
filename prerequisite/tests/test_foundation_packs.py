"""Exercise correctness and self-contained delivery of the six M2 labs."""
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / 'site/labs/downloads'
IDS = ('p1-state','p1-return','p1-values','p35-backward','p35-stochastic','p35-markov')


def run(folder, *args):
    return subprocess.run([sys.executable,*args],cwd=folder,capture_output=True,text=True,timeout=30)


@pytest.mark.parametrize('lab_id',IDS)
def test_extracted_pack_is_independent_and_deliberate_failures_are_visible(lab_id,tmp_path):
    with zipfile.ZipFile(PACKS/f'{lab_id}.zip') as archive:
        assert len(archive.namelist())==8
        assert all(name.startswith(lab_id+'/') for name in archive.namelist())
        archive.extractall(tmp_path)
    folder=tmp_path/lab_id
    reference=run(folder,'checks.py','--candidate','solution.py')
    assert reference.returncode==0,reference.stdout+reference.stderr
    demo=run(folder,'solution.py')
    assert demo.returncode==0,demo.stderr
    json.loads(demo.stdout)
    broken=run(folder,'broken.py')
    assert broken.returncode==0,broken.stderr
    json.loads(broken.stdout)
    failed=run(folder,'checks.py','--candidate','broken.py')
    assert failed.returncode==1 and 'FAIL: AssertionError:' in failed.stdout
    starter=run(folder,'starter.py')
    assert starter.returncode==1 and 'Exercise incomplete:' in starter.stdout
    assert run(folder,'checks.py','--candidate','starter.py').returncode==1


def test_forward_return_implementation_passes_without_reference_import(tmp_path):
    with zipfile.ZipFile(PACKS/'p1-return.zip') as archive: archive.extractall(tmp_path)
    folder=tmp_path/'p1-return'
    (folder/'alternate.py').write_text('''from exercise_common import validate_distribution
import math
def returns(rewards,gamma):
    validate_distribution([gamma,1-gamma])
    if any(not math.isfinite(r) for r in rewards): raise ValueError('invalid reward')
    return [sum(gamma**(k-t)*rewards[k] for k in range(t,len(rewards))) for t in range(len(rewards))]
''',encoding='utf-8')
    # Removing the solution ensures the checker does not use it as an oracle.
    (folder/'solution.py').unlink()
    result=run(folder,'checks.py','--candidate','alternate.py')
    assert result.returncode==0,result.stdout+result.stderr


def test_generated_foundation_sources_have_no_drift():
    for script in ('build_foundation_pages.py','build_foundation_packs.py','build_lab_downloads.py'):
        result=run(ROOT,f'scripts/{script}')
        assert result.returncode==0,result.stdout+result.stderr
