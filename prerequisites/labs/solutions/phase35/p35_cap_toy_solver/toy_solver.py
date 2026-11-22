"""Phase 3.5 capstone: solve the toy race exactly, one complication at a time.

The brief is page 05 of the Phase 3.5 set ("Build a Toy DP Solver, Step by Step"). This file
is the same journey on the race you built in the Phase 1 capstone, so the answer you compute
here is the exact optimum of a world you already know.

    python -m labs check p35-cap 1      check one stage
    python -m labs check p35-cap        check everything
    python -m labs hint  p35-cap        if you are stuck

THE MODEL
---------
You are not stepping through an environment here. You are handed a `model` (a
labs.labkit.toyrace.RaceModel) and you ask it questions. Everything you need:

    model.horizon                                   number of laps; laps are numbered 1..horizon
    model.cost(lap, compound, age, action, weather, sc)
                                                    time of that lap if `action` is taken on it
    model.next_tyre(compound, age, action)          (compound, age) the next lap is driven on
    model.sc_prob(sc)                               P(safety car out next lap | sc now)
    model.weather_probs(lap, weather)               (P(DRY next lap), P(WET next lap))
    model.legal_actions(lap, compound, weather, used_both)
                                                    list of legal actions

Compounds are A = 0 and B = 1. Weather is DRY = 0 or WET = 1. `sc` is 0 or 1.
Actions are STAY_OUT = 0, PIT_A = 1, PIT_B = 2. The race starts on a new compound A, age 1.

CONVENTIONS, the same in every stage
------------------------------------
* The solver MINIMISES total time. V[state] is the best achievable (expected) time from that
  state to the finish.
* V and policy are dicts keyed by a state tuple. The tuple grows by one entry per stage.
* The terminal row, lap = horizon + 1, is 0.0 for every combination of the other entries,
  with ages 1 .. horizon + 1.
* At lap t the tyre can be 1 .. t laps old, so loop ages over range(1, t + 1).
* When two actions are equally good, keep the one with the lower number.

Names here are deliberately not the real project's names.
"""

from labs.labkit.toyrace import A, ALL_ACTIONS, B, DRY, PIT_A, PIT_B, STAY_OUT, WET  # noqa: F401

COMPOUNDS = (A, B)

# ============================================================================ Stage 1


def solve_dry_green(model):
    """Deterministic backward induction: dry, no safety car, no rules.

    State: (lap, compound, age). All three actions are allowed in every state.
        V[(lap, compound, age)] = min over actions of
            model.cost(lap, compound, age, action) + V[(lap + 1, next compound, next age)]
    Returns (V, policy).
    """
    # >>> SOLUTION: terminal row of zeros, then laps backward, compounds, ages 1..lap, keeping the cheapest of the three cost + next-value totals
    H = model.horizon
    V = {(H + 1, c, age): 0.0 for c in COMPOUNDS for age in range(1, H + 2)}
    policy = {}
    for lap in range(H, 0, -1):
        for c in COMPOUNDS:
            for age in range(1, lap + 1):
                best_total, best_action = None, None
                for action in ALL_ACTIONS:
                    next_c, next_age = model.next_tyre(c, age, action)
                    total = model.cost(lap, c, age, action) + V[(lap + 1, next_c, next_age)]
                    if best_total is None or total < best_total:
                        best_total, best_action = total, action
                V[(lap, c, age)], policy[(lap, c, age)] = best_total, best_action
    return V, policy
    # <<< SOLUTION


# ============================================================================ Stage 2


def solve_with_safety_car(model):
    """Add the safety car. Still dry, still no rules.

    State: (lap, compound, age, sc). The cost now depends on sc:
        model.cost(lap, compound, age, action, DRY, sc)
    and the next lap may or may not be under the safety car, so the next value is an
    expectation, with p = model.sc_prob(sc):
        p * V[(lap + 1, next compound, next age, 1)] + (1 - p) * V[(lap + 1, next compound, next age, 0)]
    Returns (V, policy).
    """
    # >>> SOLUTION: stage 1's loops with one more loop over sc in (0, 1), and the two-term expectation in place of the single next value
    H = model.horizon
    V = {(H + 1, c, age, sc): 0.0 for c in COMPOUNDS for age in range(1, H + 2) for sc in (0, 1)}
    policy = {}
    for lap in range(H, 0, -1):
        for c in COMPOUNDS:
            for age in range(1, lap + 1):
                for sc in (0, 1):
                    p = model.sc_prob(sc)
                    best_total, best_action = None, None
                    for action in ALL_ACTIONS:
                        next_c, next_age = model.next_tyre(c, age, action)
                        expected = p * V[(lap + 1, next_c, next_age, 1)] + (1 - p) * V[(lap + 1, next_c, next_age, 0)]
                        total = model.cost(lap, c, age, action, DRY, sc) + expected
                        if best_total is None or total < best_total:
                            best_total, best_action = total, action
                    V[(lap, c, age, sc)], policy[(lap, c, age, sc)] = best_total, best_action
    return V, policy
    # <<< SOLUTION


# ============================================================================ Stage 3


def solve_with_rules(model):
    """Add the rules of the race. Still dry.

    State: (lap, compound, age, sc, used_both), where used_both is True once both compounds
    have been fitted at some point in the race.
      * Only compare the actions in model.legal_actions(lap, compound, DRY, used_both).
      * used_both carries forward: it becomes True as soon as an action changes the compound,
        and never goes back to False.
    Returns (V, policy).
    """
    # >>> SOLUTION: stage 2's loops with one more loop over used_both in (False, True), actions taken from model.legal_actions, and next_used = used_both or (next compound differs)
    H = model.horizon
    V = {
        (H + 1, c, age, sc, used): 0.0
        for c in COMPOUNDS
        for age in range(1, H + 2)
        for sc in (0, 1)
        for used in (False, True)
    }
    policy = {}
    for lap in range(H, 0, -1):
        for c in COMPOUNDS:
            for age in range(1, lap + 1):
                for sc in (0, 1):
                    for used in (False, True):
                        p = model.sc_prob(sc)
                        best_total, best_action = None, None
                        for action in model.legal_actions(lap, c, DRY, used):
                            next_c, next_age = model.next_tyre(c, age, action)
                            next_used = used or next_c != c
                            expected = (
                                p * V[(lap + 1, next_c, next_age, 1, next_used)]
                                + (1 - p) * V[(lap + 1, next_c, next_age, 0, next_used)]
                            )
                            total = model.cost(lap, c, age, action, DRY, sc) + expected
                            if best_total is None or total < best_total:
                                best_total, best_action = total, action
                        V[(lap, c, age, sc, used)], policy[(lap, c, age, sc, used)] = best_total, best_action
    return V, policy
    # <<< SOLUTION


# ============================================================================ Stage 4


def expect_next(model, V, lap, next_compound, next_age, next_used, sc, weather):
    """Expected value of the next lap's state, over BOTH things that are random.

    The safety car and the weather change independently, so each of the four combinations
    (sc', weather') has probability  P(sc') * P(weather'):
        sum over sc' in (0, 1) and weather' in (DRY, WET) of
            P(sc') * P(weather') * V[(lap + 1, next_compound, next_age, sc', next_used, weather')]
    with P(sc' = 1) = model.sc_prob(sc) and (P(DRY), P(WET)) = model.weather_probs(lap, weather).
    """
    # >>> SOLUTION: a double loop over the two next-lap safety-car states and the two next-lap weathers, weighting each V by the product of its two probabilities
    p_sc = model.sc_prob(sc)
    p_weather = model.weather_probs(lap, weather)
    total = 0.0
    for next_sc, p1 in ((0, 1 - p_sc), (1, p_sc)):
        for next_weather, p2 in ((DRY, p_weather[DRY]), (WET, p_weather[WET])):
            total += p1 * p2 * V[(lap + 1, next_compound, next_age, next_sc, next_used, next_weather)]
    return total
    # <<< SOLUTION


def solve_full(model):
    """Add the weather. This is the whole race.

    State: (lap, compound, age, sc, used_both, weather).
      * cost:   model.cost(lap, compound, age, action, weather, sc)
      * legal:  model.legal_actions(lap, compound, weather, used_both)
      * next:   expect_next(...)
    Returns (V, policy).
    """
    # >>> SOLUTION: stage 3's loops with one more loop over weather in (DRY, WET), passing weather to cost and legal_actions, and expect_next() for the next value
    H = model.horizon
    V = {
        (H + 1, c, age, sc, used, w): 0.0
        for c in COMPOUNDS
        for age in range(1, H + 2)
        for sc in (0, 1)
        for used in (False, True)
        for w in (DRY, WET)
    }
    policy = {}
    for lap in range(H, 0, -1):
        for c in COMPOUNDS:
            for age in range(1, lap + 1):
                for sc in (0, 1):
                    for used in (False, True):
                        for w in (DRY, WET):
                            best_total, best_action = None, None
                            for action in model.legal_actions(lap, c, w, used):
                                next_c, next_age = model.next_tyre(c, age, action)
                                next_used = used or next_c != c
                                total = model.cost(lap, c, age, action, w, sc) + expect_next(
                                    model, V, lap, next_c, next_age, next_used, sc, w
                                )
                                if best_total is None or total < best_total:
                                    best_total, best_action = total, action
                            V[(lap, c, age, sc, used, w)] = best_total
                            policy[(lap, c, age, sc, used, w)] = best_action
    return V, policy
    # <<< SOLUTION


# ============================================================================ Stage 5


def best_one_stop_time(model):
    """A baseline you can reason about without any solver: the best simple one-stop race.

    Dry, no safety car. Start on A, STAY_OUT every lap except one, on which you PIT_B.
    Try every lap from 1 to horizon as the pit lap and return the lowest total time.
    Add up model.cost(...) lap by lap, moving the tyre on with model.next_tyre(...).
    """
    # >>> SOLUTION: for each candidate pit lap, simulate the race by hand (cost, then next_tyre) and keep the smallest total
    best = None
    for pit_lap in range(1, model.horizon + 1):
        compound, age, total = A, 1, 0.0
        for lap in range(1, model.horizon + 1):
            action = PIT_B if lap == pit_lap else STAY_OUT
            total += model.cost(lap, compound, age, action)
            compound, age = model.next_tyre(compound, age, action)
        best = total if best is None else min(best, total)
    return best
    # <<< SOLUTION


def looks_absurd(solver_time, baseline_time, margin=0.15):
    """True when the solver claims to beat a sensible baseline by more than `margin` of it.

    An exact solver can beat a simple plan. It cannot beat one by a large fraction of the whole
    race unless the model it was given is wrong.
    """
    # >>> SOLUTION: compare the saving (baseline_time - solver_time) with margin * baseline_time
    return (baseline_time - solver_time) > margin * baseline_time
    # <<< SOLUTION
