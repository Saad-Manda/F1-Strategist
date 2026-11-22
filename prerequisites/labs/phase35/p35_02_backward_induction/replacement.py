"""Lab p35-02: backward induction on a problem that is not a race.

THE PROBLEM — keep or replace an ageing machine
-----------------------------------------------
A workshop runs one machine for HORIZON = 6 years and then closes. At the start of each
year it makes one decision:

    KEEP     run the machine it has. Pay running_cost(age). The machine is one year older
             next year.
    REPLACE  buy a new one. Pay NEW_MACHINE_PRICE plus running_cost(0) for running the new
             machine this year. Next year that machine is 1 year old.

`age` is the number of full years the machine has already worked. The workshop starts with a
machine of age START_AGE = 2. An old machine has no resale value, and nothing is owed or
earned after the last year.

The goal is the plan with the lowest total cost over the six years.

This is page 02's recursion with different nouns:

    V[(HORIZON + 1, age)] = 0                                  nothing follows the last year
    V[(year, age)] = min over the two actions of
                     cost(age, action) + V[(year + 1, next age)]

Run the checks with:  python -m labs check p35-02
"""

from itertools import product

KEEP, REPLACE = 0, 1
ACTIONS = (KEEP, REPLACE)

HORIZON = 6
START_AGE = 2
NEW_MACHINE_PRICE = 10.0


def running_cost(age: int) -> float:
    """Cost of running a machine of this age for one year. Given."""
    return 2.0 + 1.5 * age


# ============================================================================ Task 1


def step(age: int, action: int) -> tuple[float, int]:
    """The model: (cost paid this year, age of the machine at the start of next year)."""
    # TODO: KEEP costs running_cost(age) and gives age + 1; REPLACE costs NEW_MACHINE_PRICE + running_cost(0) and gives age 1
    raise NotImplementedError("TODO p35-02: KEEP costs running_cost(age) and gives age + 1; REPLACE costs NEW_MACHINE_PRICE + running_cost(0) and gives age 1")


# ============================================================================ Task 2


def reachable_ages(year: int, start_age: int) -> list[int]:
    """Every age the machine can have at the start of `year` (years count from 1). Given.

    Either it was never replaced (start_age + year - 1), or it was last replaced k years ago
    and is now k years old, for k = 1 .. year - 1.
    """
    return sorted(set(range(1, year)) | {start_age + year - 1})


def backward_induction(horizon: int = HORIZON, start_age: int = START_AGE) -> tuple[dict, dict]:
    """Solve the problem exactly. Returns (V, policy), both dicts keyed by (year, age).

    * V[(horizon + 1, age)] = 0.0 for every age from 0 to start_age + horizon.
    * For year = horizon down to 1, and for every age in reachable_ages(year, start_age):
        V[(year, age)]      = the smaller of the two totals  cost + V[(year + 1, next_age)]
        policy[(year, age)] = the action that gives it (KEEP when the two are equal)
    * Use step() for the cost and the next age. Do not repeat its arithmetic here.
    """
    # TODO: fill the terminal row with zeros, then loop years backward and ages over reachable_ages, keeping the cheaper of the two step() + V totals
    raise NotImplementedError("TODO p35-02: fill the terminal row with zeros, then loop years backward and ages over reachable_ages, keeping the cheaper of the two step() + V totals")


# ============================================================================ Task 3


def replay_policy(policy: dict, horizon: int = HORIZON, start_age: int = START_AGE) -> tuple[list[int], float]:
    """Walk forward through the policy from year 1. Returns (actions taken, total cost paid).

    In each year, look up the action for the state you are actually in, pay for it with
    step(), and move to the age it leads to.
    """
    # TODO: start at start_age; for each year look up policy[(year, age)], add step()'s cost, move to step()'s next age
    raise NotImplementedError("TODO p35-02: start at start_age; for each year look up policy[(year, age)], add step()'s cost, move to step()'s next age")


# ============================================================================ Given: the slow way, used by the checks


def brute_force_best(horizon: int = HORIZON, start_age: int = START_AGE) -> float:
    """Try every one of the 2 ** horizon possible plans and return the cheapest total. Given."""
    best = None
    for plan in product(ACTIONS, repeat=horizon):
        age, total = start_age, 0.0
        for action in plan:
            cost, age = step(age, action)
            total += cost
        best = total if best is None else min(best, total)
    return best


def myopic_total(horizon: int = HORIZON, start_age: int = START_AGE) -> float:
    """Total cost of always taking whichever action is cheaper THIS year. Given."""
    age, total = start_age, 0.0
    for _ in range(horizon):
        cost, age = min(step(age, KEEP), step(age, REPLACE))
        total += cost
    return total
