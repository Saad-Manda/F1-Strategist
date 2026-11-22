"""Lab p35-03: backward induction when the next state is not certain.

THE PROBLEM — the machine from lab p35-02, which can now develop a fault
-------------------------------------------------------------------------
Same workshop: HORIZON = 6 years, KEEP or REPLACE each year, starting with a healthy machine
of age START_AGE = 2. One thing is new. A machine is either HEALTHY or FAULTY.

    * Running a FAULTY machine for a year costs FAULT_COST on top of its running cost.
    * A fault never repairs itself. A machine that is faulty and is kept is faulty next year.
    * Any other machine (a healthy one that is kept, or a newly bought one) is faulty at the
      start of next year with probability fault_prob(its age next year): older machines
      fail more often.

So the state is (year, age, faulty), and after choosing an action you do not know which of
two states you will land in. Page 03's one new move handles it:

    expected next value = p * V[(year + 1, next age, FAULTY)]
                        + (1 - p) * V[(year + 1, next age, HEALTHY)]

Everything else about the backward pass is unchanged from lab p35-02.

Run the checks with:  python -m labs check p35-03
"""

import numpy as np

KEEP, REPLACE = 0, 1
ACTIONS = (KEEP, REPLACE)
HEALTHY, FAULTY = 0, 1

HORIZON = 6
START_AGE = 2
NEW_MACHINE_PRICE = 10.0
FAULT_RATE = 0.08  # chance of a fault per year of age
FAULT_COST = 6.0  # extra cost of running a faulty machine for one year

# ---------------------------------------------------------------------------- your prediction
# Before you write any code: compared with lab p35-02's answer for the same workshop (38.5,
# with no faults possible), will the expected total cost here be "higher", "lower" or "same"?
# Any of the three is accepted. The point is to commit before the tests tell you.
MY_PREDICTION = "higher"  # >>> ANSWER


def running_cost(age: int) -> float:
    """Cost of running a healthy machine of this age for one year. Given."""
    return 2.0 + 1.5 * age


def reachable_ages(year: int, start_age: int) -> list[int]:
    """Every age the machine can have at the start of `year`. Given (same as lab p35-02)."""
    return sorted(set(range(1, year)) | {start_age + year - 1})


# ============================================================================ Task 1


def fault_prob(age: int) -> float:
    """Chance that a machine which will be `age` years old next year is faulty then.

    FAULT_RATE for every year of age, never more than 1.0.
    """
    # >>> SOLUTION: FAULT_RATE * age, capped at 1.0
    return min(FAULT_RATE * age, 1.0)
    # <<< SOLUTION


def step(age: int, faulty: int, action: int) -> tuple[float, int, float]:
    """The model: (cost paid this year, age next year, probability of being FAULTY next year).

    KEEP:    cost = running_cost(age), plus FAULT_COST if the machine is faulty now.
             Next age = age + 1. A faulty machine stays faulty (probability 1.0);
             a healthy one is faulty next year with probability fault_prob(next age).
    REPLACE: cost = NEW_MACHINE_PRICE + running_cost(0), whatever state the old machine was in.
             Next age = 1, faulty next year with probability fault_prob(1).
    """
    # >>> SOLUTION: the two cases described above, each returning (cost, next_age, probability of FAULTY next year)
    if action == REPLACE:
        return NEW_MACHINE_PRICE + running_cost(0), 1, fault_prob(1)
    cost = running_cost(age) + (FAULT_COST if faulty else 0.0)
    return cost, age + 1, (1.0 if faulty else fault_prob(age + 1))
    # <<< SOLUTION


# ============================================================================ Task 2


def expected_value(V: dict, year: int, age: int, p_faulty: float) -> float:
    """The probability-weighted average of the two states (year, age) could be in."""
    # >>> SOLUTION: p_faulty * V[(year, age, FAULTY)] + (1 - p_faulty) * V[(year, age, HEALTHY)]
    return p_faulty * V[(year, age, FAULTY)] + (1.0 - p_faulty) * V[(year, age, HEALTHY)]
    # <<< SOLUTION


# ============================================================================ Task 3


def solve(horizon: int = HORIZON, start_age: int = START_AGE) -> tuple[dict, dict]:
    """Backward induction over (year, age, faulty). Returns (V, policy), dicts with those keys.

    * V[(horizon + 1, age, f)] = 0.0 for every age from 0 to start_age + horizon and both f.
    * For year = horizon down to 1, every age in reachable_ages(year, start_age), both f:
        each action's total = cost + expected_value(V, year + 1, next_age, p_faulty)
        V = the smaller total, policy = the action giving it (KEEP when they are equal).
    """
    # >>> SOLUTION: the loop from lab p35-02 with one more loop over faulty, and expected_value() where the single next value used to be
    V = {(horizon + 1, age, f): 0.0 for age in range(0, start_age + horizon + 1) for f in (HEALTHY, FAULTY)}
    policy = {}
    for year in range(horizon, 0, -1):
        for age in reachable_ages(year, start_age):
            for faulty in (HEALTHY, FAULTY):
                best_total, best_action = None, None
                for action in ACTIONS:
                    cost, next_age, p_faulty = step(age, faulty, action)
                    total = cost + expected_value(V, year + 1, next_age, p_faulty)
                    if best_total is None or total < best_total:
                        best_total, best_action = total, action
                V[(year, age, faulty)], policy[(year, age, faulty)] = best_total, best_action
    return V, policy
    # <<< SOLUTION


# ============================================================================ Given: one sampled history, used by the checks


def simulate(policy: dict, rng: np.random.Generator, horizon: int = HORIZON, start_age: int = START_AGE) -> float:
    """Live through the six years once, with real dice, following `policy`. Returns the total paid. Given."""
    age, faulty, total = start_age, HEALTHY, 0.0
    for year in range(1, horizon + 1):
        cost, age, p_faulty = step(age, faulty, policy[(year, age, faulty)])
        total += cost
        faulty = FAULTY if rng.random() < p_faulty else HEALTHY
    return total
