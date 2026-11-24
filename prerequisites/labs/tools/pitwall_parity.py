"""Check the Pit Wall's JavaScript engine against the Python toy race.

    python -m labs.tools.pitwall_parity            (from inside prerequisites/, Node on PATH)

For four models (the dry race with a safety car, the same with Markov rain, a quiet race with no
safety car, and a race whose weather is known in advance, as Oracle A knows it) it draws 1,000
races of dice and plays three policies (the exact optimum and two scripts) through both engines
on the same dice. An illegal call becomes the first legal one, as on the Pit Wall. It compares
every lap time and total, the oracle's value and chosen action in every state, the best race in
hindsight on every set of dice, the exact expected time of a scripted policy, and the known
optimum of the quiet race (224.49 s). Exit status 0 only if all agree to 1e-9.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from labs.labkit import toyrace as tr

HERE = Path(__file__).resolve().parent
TOL = 1e-9
N_RACES = 1000
TRACE = [0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0]
MODELS = {
    "dry": (dict(), dict()),
    "rain": (dict(weather="markov"), dict(weather="markov")),
    "quiet": (dict(sc_hazard=0.0), dict(scHazard=0.0)),
    # Oracle A: this race's weather known in advance (a fixed trace with two showers)
    "trace": (dict(weather_trace=TRACE), dict(weatherTrace=TRACE)),
}


class ListRng:
    """Stands in for np.random.Generator in toyrace.simulate: returns the pre-drawn dice in order."""

    def __init__(self, dice):
        self.dice, self.k = list(dice), 0

    def random(self):
        self.k += 1
        return self.dice[self.k - 1]


def hindsight(model: tr.RaceModel, dice) -> float:
    """Best race with the safety car and weather known in advance (reference for oracle.js)."""
    H = model.horizon
    sc, w = [0], [tr.DRY]
    for lap in range(1, H):
        sc.append(int(dice[2 * (lap - 1)] < model.sc_prob(sc[-1])))
        w.append(int(dice[2 * (lap - 1) + 1] < model.weather_probs(lap, w[-1])[tr.WET]))
    V = {(H + 1, c, age, u): 0.0 for c in (0, 1) for age in range(1, H + 2) for u in (0, 1)}
    for lap in range(H, 0, -1):
        for c in (0, 1):
            for age in range(1, lap + 1):
                for u in (0, 1):
                    best = np.inf
                    for a in model.legal_actions(lap, c, w[lap - 1], bool(u)):
                        nc, na = model.next_tyre(c, age, a)
                        best = min(best, model.cost(lap, c, age, a, w[lap - 1], sc[lap - 1]) + V[(lap + 1, nc, na, int(u or nc != c))])
                    V[(lap, c, age, u)] = best
    return V[(1, tr.A, 1, 0)]


def main() -> int:
    rng = np.random.default_rng(2026)
    cases, py = {}, {}
    for name, (pykw, jskw) in MODELS.items():
        model = tr.RaceModel(**pykw)
        dice = rng.random((N_RACES, 2 * model.horizon)).tolist()
        cases[name] = {"model": jskw, "dice": dice}
        V, policy = tr.solve(model)
        scripts = {
            "oracle": lambda lap, c, age, sc, u, w, P=policy: P[(lap, c, age, sc, u, w)],
            "b_on_8": lambda lap, *s: tr.PIT_B if lap == 8 else tr.STAY_OUT,
            "b_then_a": lambda lap, *s: tr.PIT_B if lap == 6 else (tr.PIT_A if lap == 13 else tr.STAY_OUT),
        }
        races = []
        for d in dice:
            r = {}
            for pname, pol in scripts.items():
                laps = []

                def logged(lap, c, age, sc, u, w, pol=pol, laps=laps):
                    a = pol(lap, c, age, sc, u, w)
                    legal = model.legal_actions(lap, c, w, u)
                    if a not in legal:  # the Pit Wall's rule: an illegal call becomes the first legal one
                        a = min(legal)
                    laps.append(model.cost(lap, c, age, a, w, sc))
                    return a

                res = tr.simulate(model, logged, ListRng(d))
                r[pname] = {"time": res["time"], "laps": laps, "actions": res["actions"]}
            r["hindsight"] = hindsight(model, d)
            races.append(r)
        b_on_8 = scripts["b_on_8"]
        py[name] = {"V": V, "policy": policy, "races": races,
                    "expected_b_on_8": tr.expected_time(model, lambda *s: b_on_8(*s))}

    node = subprocess.run(["node", str(HERE / "pitwall_parity_node.js")], input=json.dumps(cases),
                          capture_output=True, text=True, check=True)
    js = json.loads(node.stdout)

    bad = 0
    for name in MODELS:
        P, J = py[name], js[name]
        for st, v in P["V"].items():
            k = ",".join(str(int(x)) for x in st)
            if st[0] > tr.RaceModel(**MODELS[name][0]).horizon:
                continue
            if abs(J["V"][k] - v) > TOL or J["policy"][k] != P["policy"][st]:
                bad += 1
                if bad < 5:
                    print(f"{name} state {st}: py V {v} a {P['policy'][st]}, js V {J['V'][k]} a {J['policy'][k]}")
        for i, (pr, jr) in enumerate(zip(P["races"], J["races"])):
            if abs(pr["hindsight"] - jr["hindsight"]) > TOL:
                bad += 1
                print(f"{name} race {i}: hindsight py {pr['hindsight']} js {jr['hindsight']}")
            for pname in ("oracle", "b_on_8", "b_then_a"):
                a, b = pr[pname], jr[pname]
                if a["actions"] != b["actions"] or abs(a["time"] - b["time"]) > TOL or \
                        max(abs(x - y) for x, y in zip(a["laps"], b["laps"])) > TOL:
                    bad += 1
                    if bad < 5:
                        print(f"{name} race {i} {pname}: py {a['time']} js {b['time']}")
        if abs(P["expected_b_on_8"] - J["expected_b_on_8"]) > TOL:
            bad += 1
            print(f"{name}: expected time of b_on_8 py {P['expected_b_on_8']} js {J['expected_b_on_8']}")
        n_states = sum(1 for st in P["V"] if st[0] <= 20)
        print(f"{name:5s}: {n_states} states, {len(P['races'])} races x 3 policies + hindsight")

    quiet_opt = js["quiet"]["V"]["1,0,1,0,0,0"]
    print(f"quiet optimum: {quiet_opt:.4f} s (expected 224.49)")
    if abs(quiet_opt - 224.49) > 0.005:
        bad += 1
    sample = py["dry"]["races"][0]
    print(f"dry race 0: oracle {sample['oracle']['time']:.2f}, hindsight {sample['hindsight']:.2f}, "
          f"pit B on 8 {sample['b_on_8']['time']:.2f}")
    print("PARITY OK" if bad == 0 else f"PARITY FAILED: {bad} mismatches")
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
