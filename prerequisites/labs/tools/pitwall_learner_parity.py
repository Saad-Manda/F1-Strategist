"""Check the Pit Wall's Learner mode (site/assets/pitwall/learner.js) against the Phase 4 capstone.

    python -m labs.tools.pitwall_learner_parity      (from inside prerequisites/, Node on PATH)

The reference is the capstone's own solution: OffPolicyLearner and run_race() from
labs/solutions/phase4/p4_cap_toy_learners/toy_learners.py, run unchanged on the dry toy race with
a safety car. Two things are swapped in, so both sides draw the same random numbers:

  - the random numbers: a port of the Pit Wall's Mulberry32 generator, shared by the learner's
    exploration and the safety car, as in learner.js (choice(legal) = legal[floor(u * len)]);
  - for the coarse binning, a subclass that hands the capstone's learner a binned state
    (laps remaining // 5, compound, age // 5, sc, used both) instead of the full one.

For each binning and two seeds it trains 3,000 races and compares every race time, the whole
table, epsilon, and the exact expected time of the greedy policy (toyrace.expected_time against
oracle.expectedTime). Fine bins are a one-to-one renaming of the capstone's unbinned state, so
there the JavaScript is the capstone learner itself. Exit status 0 only if all agree to 1e-9.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

from labs.labkit import toyrace as tr

HERE = Path(__file__).resolve().parent
SOLUTION = HERE.parent / "solutions" / "phase4" / "p4_cap_toy_learners" / "toy_learners.py"
TOL = 1e-9
RACES = 3000
SEEDS = (1, 7)
DECAY_STEPS = 120_000
WIDTH = {"fine": 1, "coarse": 5}
M32 = 0xFFFFFFFF


def load_capstone():
    spec = importlib.util.spec_from_file_location("toy_learners_solution", SOLUTION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Mulberry32:
    """engine.js rngFrom(seed), with the two calls the capstone makes on a numpy Generator."""

    def __init__(self, seed: int):
        self.a = seed & M32

    def random(self) -> float:
        self.a = (self.a + 0x6D2B79F5) & M32
        t = self.a
        t = ((t ^ (t >> 15)) * (t | 1)) & M32
        t ^= (t + (((t ^ (t >> 7)) * (t | 61)) & M32)) & M32
        return ((t ^ (t >> 14)) & M32) / 4294967296

    def choice(self, legal):
        return legal[int(self.random() * len(legal))]


def binned_learner(cap, width: int, horizon: int, seed: int):
    class Binned(cap.OffPolicyLearner):
        def cell(self, state):
            lap, c, age, sc, used = state
            return ((horizon - lap) // width, c, age // width, sc, bool(used))

        def act(self, state, legal, greedy=False):
            return super().act(self.cell(state), legal, greedy)

        def learn(self, state, action, reward, next_state, done, legal_next):
            super().learn(self.cell(state), action, reward, self.cell(next_state), done, legal_next)

    learner = Binned(alpha=0.1, eps_start=1.0, eps_end=0.05, decay_steps=DECAY_STEPS, seed=0)
    learner.rng = Mulberry32(seed)
    return learner


def main() -> int:
    cap = load_capstone()
    model = tr.RaceModel()
    py = {}
    for bins, width in WIDTH.items():
        for seed in SEEDS:
            learner = binned_learner(cap, width, model.horizon, seed)
            times = [cap.run_race(learner, model, learner.rng, train=True, offset=cap.BASE_LAP)["time"]
                     for _ in range(RACES)]
            table = {}
            for (lb, c, ab, sc, used), q in learner.table.items():
                k = (((lb * 2 + c) * 64 + ab) * 2 + sc) * 2 + int(used)
                table[k] = [float(x) for x in q]
            expected = tr.expected_time(model, cap.greedy_policy(learner, model))
            py[f"{bins}/{seed}"] = {"times": times, "table": table, "epsilon": learner.epsilon,
                                    "steps": learner.steps, "expected": expected}

    cases = {"races": RACES, "seeds": list(SEEDS), "decay": DECAY_STEPS, "bins": list(WIDTH)}
    node = subprocess.run(["node", str(HERE / "pitwall_learner_parity_node.js")], input=json.dumps(cases),
                          capture_output=True, text=True, check=True)
    js = json.loads(node.stdout)

    bad = 0
    optimum = tr.solve(model)[0][(1, tr.A, 1, 0, False, tr.DRY)]
    for name, P in py.items():
        J = js[name]
        dt = max(abs(a - b) for a, b in zip(P["times"], J["times"]))
        if len(P["times"]) != len(J["times"]) or dt > TOL:
            bad += 1
            print(f"{name}: race times differ by up to {dt}")
        jt = {int(k): v for k, v in J["table"].items()}
        dq = 0.0
        for k in set(P["table"]) | set(jt):
            a, b = P["table"].get(k, [0.0] * 3), jt.get(k, [0.0] * 3)
            dq = max(dq, max(abs(x - y) for x, y in zip(a, b)))
        if dq > TOL:
            bad += 1
            print(f"{name}: tables differ by up to {dq}")
        if abs(P["epsilon"] - J["epsilon"]) > TOL or P["steps"] != J["steps"]:
            bad += 1
            print(f"{name}: epsilon py {P['epsilon']} js {J['epsilon']}, steps {P['steps']} vs {J['steps']}")
        if abs(P["expected"] - J["expected"]) > TOL:
            bad += 1
            print(f"{name}: expected time py {P['expected']} js {J['expected']}")
        print(f"{name:9s}: {RACES} races, {len(P['table'])} cells visited, "
              f"gap to the optimum {P['expected'] - optimum:.2f} s")
    print("LEARNER PARITY OK" if bad == 0 else f"LEARNER PARITY FAILED: {bad} mismatches")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
