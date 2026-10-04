"""Verify M5 independently extracted exercises, source drift and real API lifecycle."""
import json
from pathlib import Path
import subprocess,sys,zipfile
import pytest

ROOT=Path(__file__).resolve().parents[1]
LABS=ROOT/'site'/'labs'
sys.path.insert(0,str(ROOT/'scripts'))
IDS=('p6-credit','p6-shaping','p6-opponent','p8-game','p8-pool','p8-audit')
def run(folder,*args):return subprocess.run([sys.executable,*args],cwd=folder,capture_output=True,text=True,timeout=90)

@pytest.mark.parametrize('key',IDS)
def test_extracted_candidates_and_independent_checks(key,tmp_path):
    with zipfile.ZipFile(LABS/'downloads'/f'{key}.zip') as z:
        assert len(z.namelist())==(9 if key in ('p8-game','p8-audit') else 8)
        assert all(n.startswith(key+'/') and '__pycache__' not in n for n in z.namelist())
        z.extractall(tmp_path)
    folder=tmp_path/key
    good=run(folder,'checks.py','--candidate','solution.py');assert good.returncode==0,good.stdout+good.stderr
    for file in ('broken.py','solution.py'):
        demo=run(folder,file);assert demo.returncode==0,demo.stdout+demo.stderr;json.loads(demo.stdout)
    broken=run(folder,'checks.py','--candidate','broken.py');assert broken.returncode==1 and 'AssertionError' in broken.stdout
    starter=run(folder,'starter.py');assert starter.returncode==1 and 'Exercise incomplete' in starter.stdout
    (folder/'solution.py').rename(folder/'learner.py')
    good=run(folder,'checks.py','--candidate','learner.py');assert good.returncode==0,good.stdout+good.stderr

def test_generated_multiagent_artifacts_are_current():
    import build_multiagent_pages,build_multiagent_packs
    for generator in (build_multiagent_pages,build_multiagent_packs):
        for path,source in generator.outputs().items():assert path.read_text(encoding='utf-8')==source

def test_fixed_opponent_training_budget_and_heldout_coverage(tmp_path):
    with zipfile.ZipFile(LABS/'downloads'/'p8-game.zip') as z:z.extractall(tmp_path)
    result=run(tmp_path/'p8-game','compare.py','--candidate','solution.py','--seed','7')
    assert result.returncode==0,result.stderr
    data=json.loads(result.stdout)
    assert len(data['runs'])==3
    for row in data['runs']:
        assert row['training_joint_transitions']==sum(row['counts'])==1000
        assert row['exploration']=='uniform' and len(row['coverage'])==3
        assert sum(row['coverage'])==0
    again=run(tmp_path/'p8-game','compare.py','--candidate','solution.py','--seed','7')
    assert json.loads(again.stdout)==data

def test_actual_pettingzoo_official_checks_and_dead_cleanup(tmp_path):
    with zipfile.ZipFile(LABS/'downloads'/'p8-audit.zip') as z:z.extractall(tmp_path)
    result=run(tmp_path/'p8-audit','compare.py','--candidate','solution.py')
    assert result.returncode==0,result.stdout+result.stderr
    assert 'Passed Parallel API test' in result.stdout and 'Passed API test' in result.stdout
    decoder=json.JSONDecoder();data,_=decoder.raw_decode(result.stdout)
    assert data['parallel']['agents']==[] and data['aec_live_agents']==[]
    assert [r['action'] for r in data['aec']]==[1,0,None,None]
    assert data['aec'][0]['observation']==data['aec'][1]['observation']==[0]
    assert data['aec'][2]['reward']==1 and data['aec'][3]['reward']==-1
    assert data['versions']['pettingzoo'].startswith('1.')
