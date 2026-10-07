"""M6 extracted exercises, source provenance and independent boundary witnesses."""
import hashlib,json,subprocess,sys,zipfile
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
LABS=ROOT/'site'/'labs'
sys.path.insert(0,str(ROOT/'scripts'))

@pytest.mark.parametrize('key',('p9-reinforce','p9-advantage','p9-gae','p9-ppo'))
def test_extracted_candidates(key,tmp_path):
    with zipfile.ZipFile(LABS/'downloads'/f'{key}.zip') as z:z.extractall(tmp_path)
    folder=tmp_path/key
    def run(*args):return subprocess.run([sys.executable,*args],cwd=folder,capture_output=True,text=True,timeout=90)
    ref=run('checks.py','--candidate','solution.py');assert ref.returncode==0,ref.stdout+ref.stderr
    demo=run('broken.py');assert demo.returncode==0,demo.stdout+demo.stderr
    broken=run('checks.py','--candidate','broken.py');assert broken.returncode==1 and 'AssertionError' in broken.stdout
    incomplete=run('starter.py');assert incomplete.returncode==1 and 'Exercise incomplete' in incomplete.stdout
    (folder/'solution.py').rename(folder/'learner.py')
    assert run('checks.py','--candidate','learner.py').returncode==0

def test_generated_policy_content():
    import build_policy_pages,build_policy_packs
    for generator in (build_policy_pages,build_policy_packs):
        for path,source in generator.outputs().items():assert path.read_text(encoding='utf-8')==source

def test_real_integration_provenance():
    d=json.loads((LABS/'fixtures'/'p9-ppo-integration.json').read_text(encoding='utf-8'))
    assert d['platform']=='Windows' and d['device']=='cpu' and d['schemaVersion']==1
    assert d['actual_transitions']==d['requested_transitions']==sum(d['worker_transition_counts'])==128
    assert d['rollout_transitions']==d['settings']['n_envs']*d['settings']['n_steps']==32
    assert d['factories']['sb3_cloudpickle_lambda_spawn']=='passed'
    assert 'lock' in d['factories']['captured_lock_failure'] and d['factories']['ordinary_pickle_lambda']!='unexpected success'
    assert d['auto_reset_boundary']==dict(done=True,time_limit_truncated=True,final_observation=[2.],reset_observation=[0.])
    assert len(d['evaluation'])==4 and all(1<=e['transitions']<=8 for e in d['evaluation'])
    for name,digest in d['sourceHashes'].items():assert hashlib.sha256((LABS/'downloads'/'p9-ppo'/name).read_bytes()).hexdigest()==digest

def test_alternative_forward_sum_gae(tmp_path):
    with zipfile.ZipFile(LABS/'downloads'/'p9-gae.zip') as z:z.extractall(tmp_path)
    folder=tmp_path/'p9-gae';reference=(folder/'solution.py').read_text(encoding='utf-8')
    # Keep input validation; independently sum residuals forward instead of a reverse scan.
    start=reference.index('    a=np.zeros');end=reference.index('    return a,a+v',start)
    alternate='''    a=np.zeros(len(r),dtype=float)
    for i in range(len(r)):
        weight=1.
        for j in range(i,len(r)):
            a[i]+=weight*delta[j]
            if not c[j]:break
            weight*=gamma*lam
'''
    (folder/'alternative.py').write_text(reference[:start]+alternate+reference[end:],encoding='utf-8')
    (folder/'solution.py').unlink()
    run=subprocess.run([sys.executable,'checks.py','--candidate','alternative.py'],cwd=folder,capture_output=True,text=True,timeout=30)
    assert run.returncode==0,run.stdout+run.stderr

def test_reading_toy_ppo_differentiates_both_advantage_signs():
    import html,re,torch
    course=json.loads((ROOT/'content/course-registry.json').read_text(encoding='utf-8'))
    scope={}
    for reading in course['readings']:
        if reading['module']!='policy-gradients':continue
        source=(ROOT/reading['source']).read_text(encoding='utf-8')
        for block in re.findall(r'<pre><code>(.*?)</code></pre>',source,re.S):
            exec(html.unescape(block),scope)
    old=torch.zeros(4,dtype=torch.float64,requires_grad=True)
    new=torch.tensor([1.3,.7,.7,1.3],dtype=torch.float64).log().requires_grad_()
    advantages=torch.tensor([1.,1.,-1.,-1.],dtype=torch.float64,requires_grad=True)
    loss=scope['ppo_loss'](new,old,advantages)
    loss.backward()
    assert torch.allclose(loss,torch.tensor(.05,dtype=torch.float64))
    assert torch.allclose(new.grad,torch.tensor([0.,-.175,0.,.325],dtype=torch.float64))
    assert old.grad is None and advantages.grad is None
