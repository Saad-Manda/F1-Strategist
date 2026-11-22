"""Checks for the Phase 6 capstone, one group per stage. Given code: nothing to edit here.

Most checks drive your race and labs/labkit/duel.py's reference race side by side, with the same
plan and the same seed, and require the same race to the last decimal.
"""

import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(next(p for p in HERE.parents if (p / "labs" / "labkit").exists())))

import duel_race as dr  # noqa: E402
from labs.labkit import duel as ref  # noqa: E402
from labs.labkit.toyrace import PIT_A, PIT_B, STAY_OUT, A, B  # noqa: E402

PLANS = [{}, {8: PIT_B}, {6: PIT_B}, {9: PIT_B}, {3: PIT_B, 12: PIT_A}, {16: PIT_B}]


def same_race(plan, seed, **kw):
    mine, theirs = dr.play(plan, seed, **kw), ref.play(plan, seed, **kw)
    for key in ("lap_times", "agent_time", "rival_time"):
        worst = float(np.max(np.abs(np.array(mine[key]) - np.array(theirs[key]))))
        if worst > 1e-9:
            lap = int(np.argmax(np.abs(np.array(mine[key]) - np.array(theirs[key])))) + 1
            return f"{key} differs from the reference by {worst:.4f} s, first at lap {lap} (plan {dr.plan_name(plan)}, seed {seed}, {kw})"
    if mine["ahead"] != theirs["ahead"]:
        return f"who is ahead differs from the reference (plan {dr.plan_name(plan)}, seed {seed}, {kw})"
    return None


# ---------------------------------------------------------------- stage 1: two cars, counted once


def test_stage1_matches_the_reference_without_interaction():
    for plan in PLANS:
        problem = same_race(plan, 0, interaction=False)
        assert problem is None, problem


def test_stage1_each_lap_is_counted_once():
    race = dr.DuelRace(interaction=False)
    race.reset(0)
    while not race.done:
        before = list(race.time)
        lap_time, info = race.step(STAY_OUT if race.lap != 8 else PIT_B)
        assert race.time[dr.RIVAL] - before[dr.RIVAL] == pytest.approx(info["rival_lap_time"]), "(given) the rival's lap time is read off its total"
        assert 9.0 < info["rival_lap_time"] < 20.0, (
            f"Lap {info['lap']}: the rival's total grew by {info['rival_lap_time']:.2f} s. A toy lap is 10 to 16 s; "
            "twice that means the lap was added twice (the plan's bug E1)."
        )
        assert 9.0 < lap_time < 20.0, f"Lap {info['lap']}: the agent's total grew by {lap_time:.2f} s."


def test_stage1_both_cars_on_the_same_lap_and_the_scripted_stop():
    race = dr.DuelRace(interaction=False)
    race.reset(0)
    for lap in range(1, 10):
        race.step(STAY_OUT)
        assert race.lap == lap + 1
    assert race.compound[dr.RIVAL] == B and race.age[dr.RIVAL] == 1, "The rival stops on lap 9: from lap 10 it is on a new compound B."
    assert race.compound[dr.AGENT] == A and race.age[dr.AGENT] == 10, "The agent never stopped: still on A, ten laps old at the start of lap 10."
    assert not race.used_both[dr.AGENT] and race.used_both[dr.RIVAL]


# ---------------------------------------------------------------- stage 2: order and the observation


def test_stage2_order_is_read_off_time():
    race = dr.DuelRace()
    race.reset(0)
    assert not race.agent_ahead(), "The agent starts 0.3 s behind."
    race.time = [100.0, 100.5]
    assert race.agent_ahead()
    race.time = [100.5, 100.0]
    assert not race.agent_ahead()


def test_stage2_observation():
    race = dr.DuelRace()
    obs = race.reset(0)
    assert obs.dtype == np.float32 and obs.shape == (8,), "observe returns 8 float32 numbers."
    assert np.allclose(obs, [1.0, 0.05, 0, 0, 0.03, 0.0, 1.0, 0.0]), f"At the start: 20 of 20 laps left, age 1/20, on A, one compound, 0.3 s behind (0.03), position 2. Got {obs.round(3).tolist()}."
    race.time = [200.0, 204.0]
    race.lap, race.age[0], race.compound[0], race.used_both[0] = 15, 6, B, True
    obs = race.observe()
    assert np.allclose(obs, [0.3, 0.3, 1, 1, 0.0, 0.4, 0.5, 1.0]), f"Lap 15 on B (age 6), leading by 4 s. Got {obs.round(3).tolist()}."
    assert np.all((obs >= 0) & (obs <= 1))


def test_stage2_leading_does_not_look_like_far_behind():
    race = dr.DuelRace()
    race.reset(0)
    race.time = [100.0, 130.0]  # leading by 30 s
    leading = race.observe()
    race.time = [130.0, 100.0]  # 30 s behind
    behind = race.observe()
    assert not np.allclose(leading[4:], behind[4:]), "Leading by 30 s and trailing by 30 s give the same duel features (the plan's 99.0 sentinel problem, E6c)."
    assert leading[7] == 1.0 and behind[7] == 0.0, "Feature 7 is is_leader."


# ---------------------------------------------------------------- stage 3: the wake reaches the lap time


def test_stage3_wake_loss_formula():
    assert dr.wake_loss(0.0) == pytest.approx(0.5)
    assert dr.wake_loss(0.75) == pytest.approx(0.25)
    assert dr.wake_loss(1.5) == pytest.approx(0.0) and dr.wake_loss(3.0) == 0.0, "No wake loss from 1.5 s on."
    assert dr.wake_loss(1.2) == pytest.approx(0.1), "0.5 × (1.5 − 1.2) / 1.5 = 0.1"


def test_stage3_wake_slows_the_car():
    kw = dict(rival_slower=-0.5, start_gap=1.1)  # the rival is faster: the cars only ever separate
    race = dr.DuelRace(**kw)
    race.reset(0)
    own = race.own_lap_time(dr.AGENT, STAY_OUT)
    lap_time, _ = race.step(STAY_OUT)
    assert lap_time == pytest.approx(own + dr.wake_loss(1.1)), (
        f"1.1 s behind, the agent's lap should be its own {own:.3f} s plus a wake loss of {dr.wake_loss(1.1):.3f} s. Got {lap_time:.3f} s."
    )
    problem = same_race({8: PIT_B}, 0, **kw)
    assert problem is None, problem


def test_stage3_return_is_minus_the_race_time():
    kw = dict(rival_slower=-0.5, start_gap=1.1)
    race = dr.play({8: PIT_B}, 3, **kw)
    assert sum(dr.rewards(race, "time")) == pytest.approx(-(race["total"] - 1.1)), (
        "With the wake in the lap time, the rewards add up to minus the race time exactly. The plan's E3 charges it to the reward and breaks this."
    )


# ---------------------------------------------------------------- stage 4: held up


def test_stage4_a_faster_car_gains_nothing_while_it_cannot_pass():
    race = dr.DuelRace(rival_slower=1.0, start_gap=0.5, passing=False, rival_script={})  # the rival never stops
    race.reset(0)
    for _ in range(10):
        race.step(STAY_OUT)
        gap = race.time[dr.AGENT] - race.time[dr.RIVAL]
        assert gap == pytest.approx(0.5, abs=1e-9), (
            f"The agent is a full second a lap faster but cannot pass: it must stay exactly 0.5 s behind. After lap {race.lap - 1} the gap is {gap:.3f} s. "
            "This is the test the plan's Definition of Done asks for (page 05)."
        )


def test_stage4_matches_the_reference_without_passing():
    for plan in PLANS:
        for seed in (0, 1):
            problem = same_race(plan, seed, passing=False)
            assert problem is None, problem


# ---------------------------------------------------------------- stage 5: passing


def test_stage5_pass_chance():
    assert dr.pass_chance(0.0) == 0.0 and dr.pass_chance(0.4) == 0.0, "No attempt unless faster this lap."
    assert dr.pass_chance(-0.5) == pytest.approx(0.5)
    assert dr.pass_chance(-1.0) == pytest.approx(0.924, abs=1e-3), "Page 04: 92.4% at 1.0 s faster, not the docstring's 80%."
    assert dr.pass_chance(-3.0) == pytest.approx(0.95), "Capped at 0.95."


def test_stage5_matches_the_reference_with_passing():
    for plan in PLANS:
        for seed in range(6):
            problem = same_race(plan, seed)
            assert problem is None, problem


def test_stage5_passing_changes_the_race():
    seeds = range(30)
    kw = dict(rival_slower=1.0, start_gap=0.5, rival_script={})  # neither car stops
    on = [dr.play({}, s, **kw)["finished_ahead"] for s in seeds]
    off = [dr.play({}, s, passing=False, **kw)["finished_ahead"] for s in seeds]
    assert not any(off), "With passing off, a car held up from lap 1 never gets ahead."
    assert sum(on) >= 25, f"With passing on, a car a second a lap faster should get by in nearly every race; it did in {sum(on)} of 30. The plan's E2 makes this 0."


def test_stage5_the_undercut_exists():
    seeds = range(150)
    rates = {lap: np.mean([dr.play({lap: PIT_B}, s)["finished_ahead"] for s in seeds]) for lap in (6, 9)}
    assert rates[6] > 0.95 and rates[9] == 0.0, (
        f"Against the rival's lap-9 stop, stopping on lap 6 should get the agent ahead (measured ~100%), stopping on lap 9 never. Got {rates[6]:.2f} and {rates[9]:.2f}."
    )
    flat = [np.mean([dr.play({lap: PIT_B}, s, interaction=False)["finished_ahead"] for s in range(20)]) for lap in (4, 6, 9, 11)]
    assert flat == [1.0, 1.0, 1.0, 1.0], "(given) with interaction off, the faster car is ahead whatever lap it stops on"


# ---------------------------------------------------------------- stage 6: four reward designs


def test_stage6_matches_the_reference_rewards():
    for plan in PLANS[:4]:
        race = ref.play(plan, 2)
        for kind in ("time", "time_plus_place", "gap_change", "potential"):
            mine, theirs = dr.rewards(race, kind), ref.rewards(race, kind)
            assert len(mine) == 20, f"{kind}: one reward per lap."
            assert np.allclose(mine, theirs, atol=1e-9), f"{kind} rewards differ from the reference on plan {dr.plan_name(plan)}: first at lap {int(np.argmax(np.abs(np.array(mine) - theirs))) + 1}."


def test_stage6_gap_change_adds_up_to_the_final_gap():
    for plan in PLANS:
        race = dr.play(plan, 4)
        final_gap = race["agent_time"][-1] - race["rival_time"][-1]
        assert sum(dr.rewards(race, "gap_change")) == pytest.approx(-final_gap, abs=1e-9), (
            "The plan's gap_change telescopes: its rewards add up to minus the final gap, whatever happened in between."
        )


def test_stage6_potential_shifts_every_race_by_the_same_amount():
    for plan in PLANS:
        for seed in range(3):
            race = dr.play(plan, seed)
            shift = sum(dr.rewards(race, "potential")) - sum(dr.rewards(race, "time_plus_place"))
            assert shift == pytest.approx(1.0, abs=1e-9), (
                f"With Φ = 0 at the finish, the shaping adds 0 − Φ(start) = 0 − (−2/2) = 1 to every race. Got {shift:.4f} (plan {dr.plan_name(plan)}, seed {seed})."
            )


# ---------------------------------------------------------------- stage 7: which shapings are safe


SEEDS = range(40)


def test_stage7_the_safe_shaping():
    assert dr.shift_is_constant("time_plus_place", dr.one_stop_plans(), SEEDS), "A design compared with itself shifts by 0 everywhere."
    assert dr.shift_is_constant("potential", dr.one_stop_plans(), SEEDS), "The zeroed potential shifts every plan, every race, by exactly 1."


def test_stage7_the_plans_flat_bonus_is_caught():
    assert not dr.shift_is_constant("flat_bonus", dr.one_stop_plans(), SEEDS), (
        "The flat bonus pays 0.5 for every lap spent ahead, so plans that run ahead longer gain more: the shift is not constant (the plan's E5)."
    )


def test_stage7_the_unzeroed_potential_is_caught():
    assert not dr.shift_is_constant("unzeroed", dr.one_stop_plans(), SEEDS), (
        "Without the zero at the finish the leftover term is −position/2 at the end: 0.5 more for finishing ahead. Races that finish differently shift differently."
    )


def test_stage7_compare_race_by_race_not_on_average():
    plans = [{6: PIT_B}, {7: PIT_B}]
    assert not dr.shift_is_constant("unzeroed", plans, range(60)), (
        "Lap 6 always finishes ahead; lap 7 does in most races but not all. The unzeroed shift differs between those races, even if the averages look close."
    )
