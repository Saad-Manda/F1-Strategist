"""Verify the exercise, independent witnesses, and extracted download pack."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import gymnasium as gym
from gymnasium.utils.env_checker import check_env

PACK = Path(__file__).resolve().parents[1] / 'site' / 'labs' / 'downloads' / 'p1-loop'
spec = importlib.util.spec_from_file_location('p1_checks', PACK / 'checks.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def test_solution_obeys_contract_and_gymnasium():
    candidate = checks.load_candidate(PACK / 'solution.py')
    assert checks.run_checks(candidate) == []
    env = candidate.ChainEnv()
    try:
        check_env(env, skip_render_check=True)
    finally:
        env.close()


def test_browser_witnesses_match_python_scripted_actions():
    candidate = checks.load_candidate(PACK / 'solution.py')
    fixtures = json.loads((PACK / 'fixtures.json').read_text())
    for name in ('right_right', 'left_boundary', 'cap_one'):
        fixture = fixtures[name]
        env = gym.wrappers.TimeLimit(candidate.ChainEnv(), max_episode_steps=1 if name == 'cap_one' else 6)
        try:
            env.reset(seed=7)
            rows = [env.step(action) for action in fixture['actions']]
            for key, index in [('observations', 0), ('rewards', 1), ('terminated', 2), ('truncated', 3)]:
                assert [row[index] for row in rows] == fixture[key]
            assert sum(row[1] for row in rows) == fixture['total']
        finally:
            env.close()


def test_broken_variant_runs_but_fails_collection_check():
    candidate = checks.load_candidate(PACK / 'broken.py')
    assert checks.run_checks(candidate) == ['Episode collection']


def test_untouched_starter_fails_with_clear_incomplete_message():
    result = subprocess.run([sys.executable, str(PACK / 'starter.py')], capture_output=True, text=True)
    assert result.returncode == 1
    assert 'Exercise incomplete: Implement collect_episode' in result.stdout


def test_checker_accepts_different_correct_implementation():
    class TableEnv(gym.Env):
        def __init__(self):
            self.observation_space = gym.spaces.Discrete(3)
            self.action_space = gym.spaces.Discrete(2)
            self.node = None

        def reset(self, **kwargs):
            super().reset(seed=kwargs.get('seed'))
            self.node, self.count = 0, 0
            return 0, {'steps': 0}

        def step(self, action):
            if self.node is None or self.node == 2:
                raise RuntimeError('boundary')
            table = {(0, 0): (0, -1), (0, 1): (1, -1), (1, 0): (0, -1), (1, 1): (2, 5)}
            if (self.node, action) not in table:
                raise ValueError('invalid action')
            self.node, reward = table[self.node, action]
            self.count += 1
            return self.node, reward, self.node == 2, False, {'steps': self.count}

    def alternate_collector(env, policy, *, seed=None):
        obs, _ = env.reset(seed=seed)
        results = []
        done = False
        while not done:
            before, action = obs, policy(obs)
            obs, reward, terminal, cut, info = env.step(action)
            results += [dict(before=before, action=action, observation=obs, reward=reward,
                             terminated=terminal, truncated=cut, info=info)]
            done = terminal or cut
        return results

    assert checks.run_checks(SimpleNamespace(ChainEnv=TableEnv, collect_episode=alternate_collector)) == []


def test_download_runs_independently_after_extraction(tmp_path):
    with zipfile.ZipFile(PACK.with_suffix('.zip')) as archive:
        assert set(archive.namelist()) == {f'p1-loop/{name}' for name in
            ('README.md', 'starter.py', 'broken.py', 'solution.py', 'exercise_common.py', 'checks.py', 'requirements.txt', 'fixtures.json')}
        archive.extractall(tmp_path)
    extracted = tmp_path / 'p1-loop'
    result = subprocess.run([sys.executable, 'checks.py', '--candidate', 'solution.py'],
                            cwd=extracted, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
