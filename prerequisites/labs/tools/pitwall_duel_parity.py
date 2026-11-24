"""Check the Pit Wall's Rival mode engine (site/assets/pitwall/duel.js) against labs/labkit/duel.py.

    python -m labs.tools.pitwall_duel_parity

Every one- and two-stop plan (190), with blocking off, on, and on without passing, against a
rival stopping on lap 6, 9 or 12, on five sets of dice: three random, one where every pass
attempt succeeds and one where none does. Both engines get the same per-lap numbers (Python's
rng is replaced by the list), and both cars' accumulated times are compared after every lap,
to 1e-9.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from labs.labkit import duel as d
from labs.labkit.toyrace import PIT_B

NODE = Path(__file__).with_name("pitwall_duel_parity_node.js")
H = d.QUIET.horizon


class Fixed:
    """Stands in for numpy's generator: hands out the given numbers in order."""

    def __init__(self, values):
        self.values, self.k = list(values), 0

    def random(self):
        self.k += 1
        return self.values[self.k - 1]


def python_side(c):
    race = d.DuelRace(rival_script={c["rivalLap"]: PIT_B}, interaction=c["interaction"], passing=c["passing"])
    race.reset(0)
    race.rng = Fixed(c["dice"])
    agent, rival, passes = [], [], 0
    while not race.done:
        _, info = race.step(c["plan"].get(race.lap, d.STAY_OUT))
        agent.append(race.time[0])
        rival.append(race.time[1])
        passes += bool(info["passed"])
    return agent, rival, passes


def main():
    rng = np.random.default_rng(6)
    dice_sets = [rng.random(H).tolist() for _ in range(3)] + [[0.0] * H, [0.999999] * H]
    modes = [(False, True), (True, True), (True, False)]
    plans = d.one_stop_plans() + d.two_stop_plans()
    cases = [{"plan": p, "dice": dz, "interaction": i, "passing": ps, "rivalLap": rl}
             for p in plans for dz in dice_sets for i, ps in modes for rl in (6, 9, 12)]
    payload = json.dumps([dict(c, plan={str(k): v for k, v in c["plan"].items()}) for c in cases])
    out = subprocess.run(["node", str(NODE)], input=payload, capture_output=True, text=True, check=True)
    js = json.loads(out.stdout)
    worst, passes, bad = 0.0, 0, 0
    for c, j in zip(cases, js):
        agent, rival, n = python_side(c)
        w = max(max(abs(a - b) for a, b in zip(agent, j["agent"])), max(abs(a - b) for a, b in zip(rival, j["rival"])))
        worst = max(worst, w)
        passes += n
        bad += n != j["passes"]
    if worst > 1e-9 or bad:
        sys.exit(f"DUEL PARITY FAILED: worst difference {worst:.3g}, {bad} races with a different pass count")
    print(f"DUEL PARITY OK ({len(cases)} races, {passes} passes, worst difference {worst:.1e})")


if __name__ == "__main__":
    main()
