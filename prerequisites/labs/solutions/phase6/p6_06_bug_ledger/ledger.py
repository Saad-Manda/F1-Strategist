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
    # >>> SOLUTION: step a race lap by lap; for every car, the increase in total_time must equal its last_lap_time
    race = make_race(passing=True, seed=0)
    while not race.done:
        before = {car.name: car.total_time for car in race.cars}
        race.step(mini_race.STAY)
        for car in race.cars:
            grew = car.total_time - before[car.name]
            assert abs(grew - car.last_lap_time) < 1e-9, f"{car.name}'s total grew by {grew:.2f} on a {car.last_lap_time:.2f} s lap"
    # <<< SOLUTION


# ============================================================================ Task 2


def check_pass_changes_the_race(make_race):
    """Switching passing off must change how at least one seeded race finishes.

    If a pass can never change the result, the overtaking model is dead code.
    """
    # >>> SOLUTION: for seeds 0..19, run with passing on and off; at least one seed must finish in a different order
    for seed in range(20):
        on, off = make_race(passing=True, seed=seed), make_race(passing=False, seed=seed)
        mini_race.run(on)
        mini_race.run(off)
        if on.order() != off.order():
            return
    raise AssertionError("passing on or off, every race finished in the same order: passes never change the race")
    # <<< SOLUTION


# ============================================================================ Task 3


def check_reward_matches_time(make_race):
    """Every lap, the agent's reward must be minus the time its total actually grew by."""
    # >>> SOLUTION: step a race; each reward must equal -(the increase in race.agent.total_time) on that lap
    race = make_race(passing=True, seed=0)
    while not race.done:
        before = race.agent.total_time
        reward, _ = race.step(mini_race.STAY)
        lost = race.agent.total_time - before
        assert abs(reward + lost) < 1e-9, f"lap {race.lap - 1}: reward {reward:.3f}, but the car lost {lost:.3f} s"
    # <<< SOLUTION
