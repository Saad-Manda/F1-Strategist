"""Checks for the Phase 1 capstone, one group per stage. Given code: nothing to edit here."""

import os
import sys
import warnings

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import toy_race as tr  # noqa: E402
from toy_race import DRY, HORIZON, PIT_A, PIT_B, STAY_OUT, WET  # noqa: E402

GREEN = [False] * HORIZON


def dry_green_env(**options):
    env = tr.ToyRaceEnv()
    obs, _ = env.reset(seed=0, options={"weather": DRY, "sc_trace": GREEN, **options})
    return env, obs


# ---------------------------------------------------------------- stage 1: spaces and observation


def test_stage1_spaces():
    env = tr.ToyRaceEnv()
    assert env.observation_space.shape == (9,), "The observation has 9 numbers."
    assert env.observation_space.dtype == np.float32
    assert float(env.observation_space.low.min()) == 0.0 and float(env.observation_space.high.max()) == 1.0
    assert env.action_space.n == 3, "Three actions: STAY_OUT, PIT_A, PIT_B."


def test_stage1_first_observation():
    env, obs = dry_green_env()
    assert obs.dtype == np.float32 and obs.shape == (9,)
    want = [1 / HORIZON, 1, 0, 1, 0, (HORIZON - 1) / HORIZON, 0, 1, 0]
    assert obs == pytest.approx(want), (
        "At the start of a dry, green race on compound A the observation should be "
        f"{want} (age, A, B, dry, wet, laps left, safety car, used A, used B), got {obs.tolist()}."
    )


def test_stage1_observation_reflects_state():
    env = tr.ToyRaceEnv()
    trace = [True] + [False] * (HORIZON - 1)
    obs, _ = env.reset(seed=0, options={"weather": WET, "sc_trace": trace, "compound": "B"})
    assert obs[1:5] == pytest.approx([0, 1, 0, 1]), "Compound B in the wet should set the B and WET entries."
    assert obs[6] == 1.0, "The safety car is out on lap 1 in this trace, so entry 6 should be 1."
    assert obs[7:9] == pytest.approx([0, 1]), "Only compound B has been used so far."


# ---------------------------------------------------------------- stage 2: pace and tyre bookkeeping


def test_stage2_pace():
    assert tr.toy_pace("A") == 0.0 and tr.toy_pace("B") == pytest.approx(0.6)


def test_stage2_apply_action():
    assert tr.apply_action("A", 5, STAY_OUT) == ("A", 6), "Staying out keeps the compound and ages it one lap."
    assert tr.apply_action("A", 5, PIT_B) == ("B", 1), "A new tyre's next lap is its first: age 1, whatever the old age was."
    assert tr.apply_action("B", 9, PIT_A) == ("A", 1)


# ---------------------------------------------------------------- stage 3: wear with a capped cliff


def test_stage3_wear_is_linear_before_the_cliff():
    assert tr.toy_wear("A", 3) == pytest.approx(0.15)
    assert tr.toy_wear("A", 6) == pytest.approx(0.30), "At exactly cliff_age the cliff has not started yet."
    assert tr.toy_wear("B", 11) == pytest.approx(0.22)


def test_stage3_cliff_bites_after_cliff_age():
    assert tr.toy_wear("A", 8) == pytest.approx(0.05 * 8 + 0.15 * 2**2), "Two laps past A's cliff: linear part plus severity x 2 squared."
    assert tr.toy_wear("B", 13) == pytest.approx(0.02 * 13 + 0.08 * 2**2)


def test_stage3_cliff_is_capped():
    for compound, c in tr.COMPOUNDS.items():
        for age in range(1, 60):
            cliff_part = tr.toy_wear(compound, age) - c["wear_rate"] * age
            assert cliff_part <= c["cliff_cap"] + 1e-9, f"The cliff penalty for {compound} at age {age} is {cliff_part:.2f}, above its cap."
    assert tr.toy_wear("A", 30) == pytest.approx(0.05 * 30 + 4.0)


def test_stage3_compound_tradeoff():
    fresh = lambda c: tr.toy_pace(c) + tr.toy_wear(c, 1)
    old = lambda c: tr.toy_pace(c) + tr.toy_wear(c, 10)
    assert fresh("A") < fresh("B"), "Fresh, A should be the quicker compound."
    assert old("A") > old("B"), "Ten laps old, A should have fallen behind B. That trade-off is what makes the choice a decision."


# ---------------------------------------------------------------- stage 4: fuel


def test_stage4_fuel():
    assert tr.toy_fuel_penalty(19) == pytest.approx(0.57)
    assert tr.toy_fuel_penalty(0) == 0.0, "On the last lap there is no fuel left to carry."
    assert all(tr.toy_fuel_penalty(n + 1) > tr.toy_fuel_penalty(n) for n in range(19))


# ---------------------------------------------------------------- stage 5: weather


def test_stage5_weather():
    assert tr.toy_weather_penalty(DRY, "A") == 0.0 and tr.toy_weather_penalty(DRY, "B") == 0.0
    assert tr.toy_weather_penalty(WET, "A") == pytest.approx(6.0)
    assert tr.toy_weather_penalty(WET, "B") == pytest.approx(5.5)


# ---------------------------------------------------------------- stage 6: warm-up and the pit-lap ordering rule


def test_stage6_warmup():
    assert tr.toy_warmup(1) == pytest.approx(1.2)
    assert tr.toy_warmup(2) == pytest.approx(0.5)
    assert tr.toy_warmup(3) == 0.0 and tr.toy_warmup(15) == 0.0


def test_stage6_green_lap_time():
    env, _ = dry_green_env()
    _, reward, terminated, truncated, info = env.step(STAY_OUT)
    want = 10.0 + 0.0 + 0.05 + 0.57 + 0.0 + 1.2
    assert info["lap_time"] == pytest.approx(want), f"Lap 1 on a new compound A, dry, green, staying out should take {want:.2f} s, got {info['lap_time']}."
    assert reward == pytest.approx(-want), "reward is minus the lap time."
    assert not terminated and not truncated


def test_stage6_pit_lap_is_timed_on_the_old_tyre():
    env, _ = dry_green_env()
    env.step(STAY_OUT)
    _, reward, _, _, info = env.step(PIT_B)
    old_tyre = 10.0 + 0.0 + 0.05 * 2 + 0.03 * 18 + 0.0 + 0.5
    assert info["lap_time"] == pytest.approx(old_tyre + 4.0), (
        "The lap you pit on is driven on the OLD tyre (compound A, age 2) and then pays PIT_LOSS. "
        f"Expected {old_tyre + 4.0:.2f} s, got {info['lap_time']:.2f} s. If your number is lower, the new tyre's pace was applied one lap early."
    )
    assert info["pit"] is True
    assert info["lap_time_compound"] == "A" and info["lap_time_age"] == 2, "info must report the tyre the lap was actually driven on."
    assert info["compound"] == "B" and info["age"] == 1, "After the stop, compound B is fitted and its first lap is next."


def test_stage6_warmup_lands_on_the_lap_after_the_stop():
    env, _ = dry_green_env()
    env.step(STAY_OUT)
    env.step(PIT_B)
    obs, _, _, _, info = env.step(STAY_OUT)
    want = 10.0 + 0.6 + 0.02 * 1 + 0.03 * 17 + 0.0 + 1.2
    assert info["lap_time"] == pytest.approx(want), f"The out-lap on new compound B should take {want:.2f} s (it carries the warm-up), got {info['lap_time']:.2f} s."
    assert obs[7:9] == pytest.approx([1, 1]), "Both compounds have now been used."


def test_stage6_episode_length_and_return():
    env, _ = dry_green_env()
    total_reward, total_time, steps, terminated = 0.0, 0.0, 0, False
    while not terminated:
        _, reward, terminated, truncated, info = env.step(PIT_B if steps == 8 else STAY_OUT)
        assert not truncated, "truncated is always False in this environment."
        total_reward += reward
        total_time += info["lap_time"]
        steps += 1
        assert steps <= HORIZON, "The race should end after exactly HORIZON laps."
    assert steps == HORIZON
    assert total_reward == pytest.approx(-total_time), "The episode return must equal minus the total race time."


# ---------------------------------------------------------------- stage 7: a safety car that is not scripted


def test_stage7_trace_shape_and_reproducibility():
    a = tr.sample_sc_trace(HORIZON, np.random.default_rng(5))
    b = tr.sample_sc_trace(HORIZON, np.random.default_rng(5))
    assert isinstance(a, np.ndarray) and a.dtype == bool and a.shape == (HORIZON,)
    assert (a == b).all(), "The same seed must give the same trace."
    distinct = {tuple(tr.sample_sc_trace(HORIZON, np.random.default_rng(s))) for s in range(40)}
    assert len(distinct) >= 8, "Different seeds should give different traces. If they do not, an agent could memorise where the safety car comes."


def test_stage7_one_draw_per_lap():
    rng, reference = np.random.default_rng(11), np.random.default_rng(11)
    tr.sample_sc_trace(HORIZON, rng)
    reference.random(HORIZON)
    assert rng.random() == reference.random(), "The spec asks for exactly one rng.random() draw per lap."


def test_stage7_hazard_and_duration():
    trace = tr.sample_sc_trace(60000, np.random.default_rng(0))
    starts = int(np.sum(trace[1:] & ~trace[:-1]))
    green = int(np.sum(~trace[:-1]))
    assert 0.05 < starts / green < 0.07, f"A safety car should start on about 6% of green laps, measured {starts / green:.1%}."
    mean_duration = trace.sum() / max(starts, 1)
    assert 2.6 < mean_duration < 3.4, f"Safety-car periods should last about 3 laps on average, measured {mean_duration:.2f}."


def test_stage7_safety_car_lap_and_discounted_pit():
    trace = [True, True] + [False] * (HORIZON - 2)
    env = tr.ToyRaceEnv()
    env.reset(seed=0, options={"weather": DRY, "sc_trace": trace})
    _, _, _, _, info = env.step(STAY_OUT)
    assert info["lap_time"] == pytest.approx(14.0), "A lap behind the safety car takes exactly SC_LAP_TIME: wear, fuel and warm-up do not apply."
    _, _, _, _, info = env.step(PIT_B)
    assert info["lap_time"] == pytest.approx(14.0 + 4.0 * 0.4), "Pitting under the safety car is discounted, not free and not full price."
    assert info["compound"] == "B" and info["age"] == 1


def test_stage7_reset_samples_fresh_traces():
    env = tr.ToyRaceEnv()
    seen = set()
    for seed in range(30):
        obs, _ = env.reset(seed=seed, options={"weather": DRY})
        flags, done = [obs[6]], False
        while not done:
            obs, _, done, _, _ = env.step(STAY_OUT)
            flags.append(obs[6])
        seen.add(tuple(flags))
    assert len(seen) >= 6, "Across 30 seeds the safety car should land on different laps."


# ---------------------------------------------------------------- stage 8: action masking


@pytest.mark.parametrize(
    "compound, weather, laps_left, used, want, why",
    [
        ("A", DRY, 10, {"A"}, [True, False, True], "you cannot pit for the compound you are on"),
        ("B", DRY, 10, {"A", "B"}, [True, True, False], "you cannot pit for the compound you are on"),
        ("A", WET, 10, {"A"}, [True, False, False], "B is unsafe in the wet"),
        ("A", DRY, 1, {"A"}, [False, False, True], "the two-compound rule forces the stop when time is nearly up"),
        ("A", DRY, 0, {"A"}, [False, False, True], "the two-compound rule still applies on the last lap"),
        ("A", DRY, 1, {"A", "B"}, [True, False, True], "the rule is already satisfied, so staying out is fine"),
        ("A", WET, 0, {"A"}, [True, False, False], "the two-compound rule does not apply in the wet"),
        ("B", WET, 5, {"B"}, [True, True, False], "on B in the wet, switching to A is allowed"),
    ],
)
def test_stage8_mask_rules(compound, weather, laps_left, used, want, why):
    mask = np.asarray(tr.toy_action_mask(compound, weather, laps_left, used))
    assert mask.dtype == bool and mask.shape == (3,)
    assert mask.tolist() == want, f"[STAY_OUT, PIT_A, PIT_B] should be {want}: {why}. Got {mask.tolist()}."


def test_stage8_mask_is_never_empty():
    for compound in "AB":
        for weather in (DRY, WET):
            for laps_left in range(HORIZON):
                for used in ({compound}, {"A", "B"}):
                    assert np.asarray(tr.toy_action_mask(compound, weather, laps_left, used)).any()


def test_stage8_masked_random_policy_always_uses_both_compounds():
    env = tr.ToyRaceEnv()
    rng = np.random.default_rng(0)
    for seed in range(40):
        obs, _ = env.reset(seed=seed, options={"weather": DRY})
        done = False
        while not done:
            legal = np.flatnonzero(env.action_masks())
            obs, _, done, _, _ = env.step(int(rng.choice(legal)))
        assert obs[7] == 1.0 and obs[8] == 1.0, "A dry race played with only legal actions must end having used both compounds."


# ---------------------------------------------------------------- stage 9: reward centring as a wrapper


def run(env, pit_lap):
    env.reset(seed=0, options={"weather": DRY, "sc_trace": GREEN})
    total, done, lap = 0.0, False, 1
    while not done:
        _, reward, done, _, info = env.step(PIT_B if lap == pit_lap else STAY_OUT)
        total += reward
        lap += 1
    return total, info


def test_stage9_wrapper_shifts_every_return_by_the_same_amount():
    offset = 10.0
    plain_good, _ = run(tr.ToyRaceEnv(), pit_lap=9)
    plain_bad, _ = run(tr.ToyRaceEnv(), pit_lap=2)
    centred_good, info = run(tr.RewardCentringWrapper(tr.ToyRaceEnv(), offset), pit_lap=9)
    centred_bad, _ = run(tr.RewardCentringWrapper(tr.ToyRaceEnv(), offset), pit_lap=2)
    assert centred_good == pytest.approx(plain_good + offset * HORIZON), "Each of the 20 steps should be shifted by exactly the offset."
    assert centred_good - centred_bad == pytest.approx(plain_good - plain_bad), "Centring must not change the gap between two policies."
    assert "true_reward" in info and info["true_reward"] == pytest.approx(-info["lap_time"]), "info['true_reward'] must keep the uncentred reward."


# ---------------------------------------------------------------- stage 10: the whole thing


def test_stage10_check_env():
    from stable_baselines3.common.env_checker import check_env

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        check_env(tr.ToyRaceEnv())


def test_stage10_return_is_minus_race_time_in_any_conditions():
    env = tr.ToyRaceEnv()
    rng = np.random.default_rng(1)
    for seed in range(25):
        obs, _ = env.reset(seed=seed)
        total_reward, total_time, done = 0.0, 0.0, False
        while not done:
            assert env.observation_space.contains(obs), f"Observation left its declared space: {obs.tolist()}"
            obs, reward, done, _, info = env.step(int(rng.choice(np.flatnonzero(env.action_masks()))))
            total_reward += reward
            total_time += info["lap_time"]
        assert total_reward == pytest.approx(-total_time)
