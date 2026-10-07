"""Independent witnesses for R4 teaching code and unchanged practice contracts."""
import copy
import itertools
import random

import numpy as np
import pytest

from test_foundations_readings import code, pack


def namespace(paths):
    ns = {}
    for path in ['readings/p1-probability/probability-outcomes.html', *paths]:
        for block in code(path):
            exec(block, ns)
    return ns


@pytest.fixture(scope='module')
def planning():
    return namespace([
        'readings/p35-backward/planning-learning.html',
        'readings/p35-backward/verify-solver.html',
        'readings/p35-backward/value-iteration.html',
        'readings/p35-stochastic/weighted-backups.html',
        'readings/p35-stochastic/stochastic-solver.html',
        'readings/p35-markov/transition-matrix.html',
        'readings/p35-markov/sampling-not-foresight.html',
        'readings/p35-markov/rollout-variability.html',
        'applications/planning/oracle-model.html',
        'applications/planning/oracle-bound.html',
    ])


@pytest.fixture(scope='module')
def tabular():
    return namespace([
        'readings/p4-td/terminal-masked-targets.html',
        'readings/p4-explore/epsilon-probabilities.html',
        'readings/p4-explore/exploration-schedules.html',
        'readings/p4-sarsa/sampled-sarsa.html',
        'readings/p4-sarsa/expected-sarsa.html',
        'readings/p4-sarsa/algorithm-comparison.html',
        'readings/p4-bins/table-representation.html',
        'readings/p4-bins/interval-boundaries.html',
        'readings/p4-bins/encoder-checks.html',
        'applications/tabular-learning/tabular-contract.html',
    ])


class Draw:
    def __init__(self, value):
        self.value, self.calls = value, 0

    def random(self):
        self.calls += 1
        return self.value


def test_backward_values_match_independent_enumeration_and_pack(planning):
    for horizon in range(6):
        costs, _ = planning['race_dp'](horizon)
        assert costs[1, 1] == planning['brute_race'](horizon)
    costs, policy = planning['race_dp'](4)
    assert [costs[4, age] for age in range(1, 5)] == [10, 13, 16, 19]
    assert costs[3, 2] == 29 and policy[3, 2] == 'STAY'
    age, total = 1, 0
    for lap in range(1, 5):
        action = policy[lap, age]
        total += 10 + 3*(age-1) + (6 if action == 'PIT' else 0)
        age = 1 if action == 'PIT' else age+1
    assert total == costs[1, 1] == 52
    reference = pack('p35-backward')
    for horizon in (0, 1, 2, 5):
        for gamma in (0, .5, 1):
            assert planning['solve'](horizon, gamma) == reference.solve(horizon, gamma)
    for invalid in (-1, True, 1.5, 11):
        with pytest.raises(ValueError):
            planning['race_dp'](invalid)


def test_stochastic_adaptive_policy_enumeration_and_constraints(planning):
    weather = ((.6, .3, .1), (.2, .6, .2), (.1, .2, .7))
    hazard = .25
    successors = [(sc, w) for sc in (0, 1) for w in range(3)]
    # Enumerate action choices for EACH observed successor, not fixed schedules.
    for required in (False, True):
        candidates = []
        for first_pit in (False, True):
            for decisions in itertools.product((False, True), repeat=6):
                if required and not first_pit and not all(decisions):
                    continue
                expected = 10 + 6*first_pit
                age = 1 if first_pit else 2
                for (sc, w), pit in zip(successors, decisions):
                    weight = (hazard if sc else 1-hazard)*weather[0][w]
                    cost = 20 if sc else 10+3*(age-1)+(0, 1.5, 4)[w]
                    expected += weight*(cost + (2.4 if sc else 6)*pit)
                candidates.append(expected)
        costs, policy = planning['uncertain_race'](2, hazard=hazard, weather=weather,
                                                   require_pit=required)
        assert costs[1, 1, False, 0, 0] == pytest.approx(min(candidates))
        if required:
            assert all(policy[2, 2, False, sc, w] == 'PIT' for sc, w in successors)
    costs, _ = planning['uncertain_race'](4, hazard=0, continuation=0)
    assert costs[1, 1, False, 0, 0] == 52
    free, _ = planning['uncertain_race'](4, weather=weather)
    constrained, _ = planning['uncertain_race'](4, weather=weather, require_pit=True)
    assert constrained[1, 1, False, 0, 0] >= free[1, 1, False, 0, 0]
    costs, _ = planning['uncertain_race'](8)
    assert costs[8, 8, True, 1, 0] == 20 < costs[8, 8, True, 0, 0] == 31
    for kwargs in ({'hazard': 1.1}, {'weather': ((1, 0, 0),)*2},
                   {'weather': ((.7, .1, .1),)*3}):
        with pytest.raises(ValueError):
            planning['uncertain_race'](2, **kwargs)


def test_weather_estimation_boundaries_and_pack_contracts(planning):
    counts, matrix = planning['fit_weather'](planning['weather_logs'])
    assert counts == [[5, 3, 0], [2, 2, 1], [0, 1, 1]]
    assert np.array(matrix) == pytest.approx(np.array([[.625, .375, 0], [.4, .4, .2], [0, .5, .5]]))
    for traces in ([[0, 0], [1, 1]], [[0, 3]], [[0, True]]):
        with pytest.raises(ValueError):
            planning['fit_weather'](traces)
    reference = pack('p35-markov')
    two = [[.8, .2], [.3, .7]]
    for draw, expected in ((0, 0), (.7999, 0), (.8, 1), (.9999, 1)):
        assert planning['sample_next'](0, Draw(draw), two) == expected
        assert reference.sample_next(0, Draw(draw), two) == expected
    with pytest.raises(ValueError):
        planning['sample_next'](0, Draw(1), two)
    assert planning['advance'](planning['advance']([1, 0], two), two) == pytest.approx([.7, .3])
    assert planning['advance']([.6, .4], two) == pytest.approx([.6, .4])
    assert planning['expected_value']([(.25, 20), (.75, 16)]) == 17
    # Clipping destroys the zero-mean-noise equivalence even in one step.
    assert sum(max(0, x) for x in (-1, 1))/2 == .5 != max(0, 0)


def test_terminal_masks_and_four_hand_updates(tabular):
    update = tabular['update']
    reference = pack('p4-td')
    cases = [(2, 1, [4, 8, 99], [True, True, False], .25, .5, False, False),
             (2, 1, [], [], .25, .5, True, False),
             (2, 1, [4, 8, 99], [True, True, False], .25, .5, False, True),
             (2, 1, [], [], .25, .5, True, True)]
    for args in cases:
        assert update(*args) == reference.update(*args)
    assert update(*cases[0])['value'] == 2.75
    assert update(*cases[1])['value'] == 1.75
    with pytest.raises(ValueError):
        update(0, 1, [], [], .5, 0, False, False)
    q = {1: [0., 0.], 2: [0., 0.]}
    for state, action, reward, successor, done in [(1, 0, -1, 2, False),
                                                 (2, 0, -1, 0, True),
                                                 (1, 1, -3, 0, True),
                                                 (1, 0, -1, 2, False)]:
        q[state][action] = update(q[state][action], reward,
                                 [] if done else q[successor], [] if done else [True, True],
                                 .5, 1, done, False)['value']
    assert q == {1: [-.75, -1.5], 2: [-.5, 0.]}


def test_exploration_distribution_schedule_and_sarsa_commitment(tabular):
    assert tabular['probabilities']([3, 5, 99], [True, True, False], .2) == pytest.approx([.1, .9, 0])
    assert tabular['probabilities']([5, 5, 99], [True, True, False], .2) == pytest.approx([.5, .5, 0])
    assert tabular['epsilon_at'](250000) == pytest.approx(.525)
    assert tabular['epsilon_at'](500001) == .05
    memory, rng = {}, Draw(.95)
    assert tabular['target'](memory, 0, 'risk', [6, -10], [True, True], 1,
                             False, False, .2, rng) == -10
    assert memory['pending'] == ('risk', 1)
    assert tabular['act'](memory, 'risk', [100, -100], [True, True], 0, rng) == 1
    assert rng.calls == 1 and memory == {}
    tabular['target'](memory, 0, 'risk', [6, -10], [True, True], 1,
                      False, True, .2, rng)
    assert memory == {}
    assert tabular['target'](memory, -7, 'end', [], [], 1, True, True, .2, rng) == -7
    memory['pending'] = ('risk', 1)
    with pytest.raises(ValueError):
        tabular['act'](memory, 'start', [0, 0], [True, True], .2, rng)
    memory['pending'] = ('risk', 1)
    tabular['reset'](memory)
    assert memory == {}
    assert tabular['expected_sarsa_target'](0, [6, -10], [True, True], 1, .2, False) == pytest.approx(4.4)
    ql = sarsa = 0
    successor = [0., 0.]
    for action, q_expected, s_expected in [(1, -.5, -.5), (0, -.75, -.75), (1, -2.875, -8.375)]:
        ql += .5*(-1 + max(successor) - ql)
        sarsa += .5*(-1 + successor[action] - sarsa)
        successor[action] += .5*((-8 if action == 0 else -30) - successor[action])
        assert (ql, sarsa) == (q_expected, s_expected)


def test_evaluation_does_not_allocate_or_mutate_learner(tabular):
    for name in ('OffPolicyLearner', 'OnPolicyLearner'):
        learner = tabular[name]()
        learner.table[0] = [-20, 1]
        before = copy.deepcopy(dict(learner.table)), learner.steps
        result = tabular['one_episode'](learner, tabular['TinyStrategyWorld'](), random.Random(7), True)
        assert result in (-9, -31)
        assert (dict(learner.table), learner.steps) == before
        assert learner.memory == {}


def test_bins_full_key_alias_and_observation_contract(tabular):
    edges = [0, .25, .5, 1]
    for value, expected in ((0, 0), (.25, 1), (.5, 2), (1, 2)):
        assert tabular['bin_index'](value, edges) == expected
        assert pack('p4-bins').bin_index(value, edges) == expected
    assert tabular['bin_index'](float(np.nextafter(np.float32(.5), np.float32(0))), edges) == 1
    for bad in (-.1, 1.1, float('nan')):
        with pytest.raises(ValueError):
            tabular['bin_index'](bad, edges)
    assert tabular['table_size']([12, 5, 10, 3, 3, 2, 8, 2], 6) == dict(states=172800, entries=1036800, bytes=8294400)
    obs = np.zeros(16, dtype=np.float32)
    obs[0], obs[1], obs[8], obs[12] = .4, 1, 1, 1
    obs[6] = 27/50
    key27 = tabular['discretize_obs'](obs, age_bins=10)
    obs[6] = 29/50
    key29 = tabular['discretize_obs'](obs, age_bins=10)
    assert key27 == key29  # every other feature matches, not just the age bin
    assert 10 < 16 < 20  # STAY best at 27, PIT best at 29 in the specified cliff toy
    obs[6] = 27/50
    fine27 = tabular['discretize_obs'](obs, age_bins=40)
    obs[6] = 29/50
    assert fine27 != tabular['discretize_obs'](obs, age_bins=40)
    for index, value in ((2, 1), (11, .5), (0, 1.1)):
        invalid = obs.copy(); invalid[index] = value
        with pytest.raises(ValueError):
            tabular['discretize_obs'](invalid)
