"""Lab p6-06: write the three tests the plan is missing.

`mini_race.py` (given, read it) is a three-car race in the plan's shape, with page 06's bugs
available as switches. Each function below is a TEST: it receives `make_race`, a function that
builds a fresh race,

    race = make_race(passing=True, seed=0)      # a mini_race.Race, bugs already chosen for you

drives it (mini_race.run(race) drives one to the end), and must raise AssertionError (use
`assert`) when the bug it is named after is present. It must NOT raise on the reference race.

You are graded the way mutation testing grades a test suite: each of your checks is run against
the reference race (it must pass) and against a race that carries only its own bug (it must
fail). A check that passes on both catches nothing; one that fails on both is wrong about the
reference.

    Task 1   check_time_counted_once      E1: a rival's total grows by twice its lap time
    Task 2   check_pass_changes_the_race  E2: a successful pass is written, then overwritten
    Task 3   check_reward_matches_time    E3: the reward is charged for time the car never lost

Run the checks with:  python -m labs check p6-06
"""

import mini_race

# ============================================================================ Task 1


def check_time_counted_once(make_race):
    """Each car's total_time must grow by exactly the lap time it just drove, every lap."""
    # TODO: step a race lap by lap; for every car, the increase in total_time must equal its last_lap_time
    raise NotImplementedError("TODO p6-06: step a race lap by lap; for every car, the increase in total_time must equal its last_lap_time")


# ============================================================================ Task 2


def check_pass_changes_the_race(make_race):
    """Switching passing off must change how at least one seeded race finishes.

    If a pass can never change the result, the overtaking model is dead code.
    """
    # TODO: for seeds 0..19, run with passing on and off; at least one seed must finish in a different order
    raise NotImplementedError("TODO p6-06: for seeds 0..19, run with passing on and off; at least one seed must finish in a different order")


# ============================================================================ Task 3


def check_reward_matches_time(make_race):
    """Every lap, the agent's reward must be minus the time its total actually grew by."""
    # TODO: step a race; each reward must equal -(the increase in race.agent.total_time) on that lap
    raise NotImplementedError("TODO p6-06: step a race; each reward must equal -(the increase in race.agent.total_time) on that lap")
