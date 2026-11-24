"""Record a trained DQN for the Pit Wall's Replay mode (Phase 5), and check the record.

    python -m labs.tools.pitwall_replay_export train --seed 1 --races 2000   # train, then export
    python -m labs.tools.pitwall_replay_export export --weights dqn.pt --seed 1 --races 2000
    python -m labs.tools.pitwall_replay_export check                         # JS against Python

The learner is the Phase 5 capstone's NetLearner (the solution in labs/solutions), trained on the
Pit Wall's dry race with a safety car. The browser cannot run PyTorch, so the export evaluates the
online network once on every reachable dry state (1,680 of them) and writes the greedy call and
the three Q-values to site/assets/pitwall/replay_policy.js. A greedy table is the whole policy: the
network is only ever asked about these states.

`check` loads replay_policy.js in Node, has replay.js compute the exact expected time of the policy
with exploration off and on, and the expected random, changed and pointless calls per race, and
compares them all with this file's Python, to 1e-9.
"""
import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

from labs.labkit import toyrace as tr
from labs.labkit.toyrace import A, DRY

ROOT = Path(__file__).resolve().parents[2]
SOLUTION = ROOT / "labs" / "solutions" / "phase5" / "p5_cap_toy_dqn" / "toy_dqn.py"
OUT = ROOT / "site" / "assets" / "pitwall" / "replay_policy.js"
NODE = Path(__file__).with_name("pitwall_replay_parity_node.js")
H = tr.HORIZON
EPSILONS = (0.0, 0.01, 0.05, 0.1, 0.2)


def load_td():
    spec = importlib.util.spec_from_file_location("toy_dqn_solution", SOLUTION)
    td = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(td)
    return td


def index(lap, compound, age, sc, used):
    """Must match replay.js: one slot per (lap 1..20, compound, age 1..20, sc, used_both)."""
    return ((((lap - 1) * 2 + compound) * H + (age - 1)) * 2 + sc) * 2 + int(used)


def states():
    for lap in range(1, H + 1):
        for c in (0, 1):
            for age in range(1, lap + 1):
                for sc in (0, 1):
                    for used in (False, True):
                        yield lap, c, age, sc, used


def record(td, learner, model):
    """The greedy call ('.' where no state exists) and the Q-values as expected seconds to the flag."""
    size = H * 2 * H * 2 * 2
    acts, q = ["."] * size, [None] * (3 * size)
    for lap, c, age, sc, used in states():
        i = index(lap, c, age, sc, used)
        mask = td.legal_mask(model, lap, c, used)
        vals = learner.values(td.encode(lap, c, age, sc, used, model.horizon)).astype(float)
        masked = np.where(mask, vals, -np.inf)
        acts[i] = str(int(np.argmax(masked)))
        laps_left = model.horizon - lap + 1
        for a in range(3):
            # Q is the centred return: -(time - 10 s per lap). Back to seconds to the flag.
            q[3 * i + a] = round(float(laps_left * td.BASE_LAP - vals[a]), 3) if mask[a] else None
    return "".join(acts), q


def table_policy(acts):
    def policy(lap, c, age, sc, used, weather):
        return int(acts[index(lap, c, age, sc, used)])
    return policy


def expected_time_eps(model, policy, eps):
    """Exact expected race time of ε-greedy around `policy`: with probability eps the call is a
    uniform pick among the legal actions (the greedy one included), as td.choose does."""
    V = {}
    for c in (0, 1):
        for age in range(1, H + 2):
            for sc in (0, 1):
                for used in (False, True):
                    V[(H + 1, c, age, sc, used)] = 0.0
    for lap in range(H, 0, -1):
        for c in (0, 1):
            for age in range(1, lap + 1):
                for sc in (0, 1):
                    for used in (False, True):
                        legal = model.legal_actions(lap, c, DRY, used)
                        g = policy(lap, c, age, sc, used, DRY)
                        g = g if g in legal else min(legal)
                        p_sc, total = model.sc_prob(sc), 0.0
                        for a in legal:
                            p = eps / len(legal) + (1.0 - eps if a == g else 0.0)
                            nc, na = model.next_tyre(c, age, a)
                            nu = used or nc != c
                            nxt = (1 - p_sc) * V[(lap + 1, nc, na, 0, nu)] + p_sc * V[(lap + 1, nc, na, 1, nu)]
                            total += p * (model.cost(lap, c, age, a, DRY, sc) + nxt)
                        V[(lap, c, age, sc, used)] = total
    return V[(1, A, 1, 0, False)]


def stats(model, policy, eps):
    """Expected calls per race under ε-greedy, exact: random (the dice said explore), changed (the
    call differs from the greedy one), pointless (a random pit stop where greedy stays out), and
    anyPointless, the chance a race has at least one."""
    dist, out = {(A, 1, 0, False, False): 1.0}, {"randoms": 0.0, "changed": 0.0, "pointless": 0.0, "anyPointless": 0.0}
    for lap in range(1, H + 1):
        nxt = {}
        for (c, age, sc, used, f), p in dist.items():
            legal = model.legal_actions(lap, c, DRY, used)
            g = policy(lap, c, age, sc, used, DRY)
            g = g if g in legal else min(legal)
            p_sc = model.sc_prob(sc)
            out["randoms"] += p * eps
            for a in legal:
                pa = eps / len(legal) + (1.0 - eps if a == g else 0.0)
                bad = a != g and a != tr.STAY_OUT and g == tr.STAY_OUT
                if a != g:
                    out["changed"] += p * pa
                if bad:
                    out["pointless"] += p * pa
                nc, na = model.next_tyre(c, age, a)
                key = (nc, na, None, used or nc != c, f or bad)
                for nsc, q in ((0, 1 - p_sc), (1, p_sc)):
                    if p * pa * q:
                        k2 = key[:2] + (nsc,) + key[3:]
                        nxt[k2] = nxt.get(k2, 0.0) + p * pa * q
        dist = nxt
    out["anyPointless"] = sum(p for k, p in dist.items() if k[4])
    return out


def summary(model, acts):
    policy = table_policy(acts)
    optimum = tr.solve(model)[0][(1, A, 1, 0, False, DRY)]
    greedy = tr.expected_time(model, policy)
    assert abs(greedy - expected_time_eps(model, policy, 0.0)) < 1e-9
    return optimum, {str(e): expected_time_eps(model, policy, e) for e in EPSILONS}


def write(acts, q, meta):
    body = json.dumps({"meta": meta, "acts": acts, "q": q}, separators=(",", ":"))
    OUT.write_text(
        "/* Generated by labs/tools/pitwall_replay_export.py; do not edit. The Phase 5 capstone's DQN,\n"
        "   recorded on every dry state of the toy race: the greedy call per state, and the network's\n"
        "   Q-values as expected seconds to the flag (null where the action is illegal). */\n"
        "(function (root) { root.PitWall = root.PitWall || {}; root.PitWall.replayData = " + body + "; })(this);\n"
        "if (typeof module !== \"undefined\" && module.exports) module.exports = this.PitWall.replayData;\n",
        encoding="utf-8", newline="\n")


def export(learner, td, seed, races):
    model = tr.RaceModel()
    acts, q = record(td, learner, model)
    optimum, times = summary(model, acts)
    meta = {"seed": seed, "races": races, "optimum": round(optimum, 6),
            "expected": {k: round(v, 6) for k, v in times.items()}}
    write(acts, q, meta)
    st = stats(model, table_policy(acts), 0.05)
    print(f"wrote {OUT.relative_to(ROOT)}: seed {seed}, {races} races, gap {times['0.0'] - optimum:.3f} s, "
          f"ε 0.05 costs {times['0.05'] - times['0.0']:.3f} s; per race at ε 0.05: {st['randoms']:.3f} random, "
          f"{st['changed']:.3f} changed, {st['pointless']:.3f} unplanned stops, {st['anyPointless']:.1%} of races with one")


def check():
    model = tr.RaceModel()
    text = OUT.read_text(encoding="utf-8")
    data = json.loads(text[text.index("replayData = ") + len("replayData = "):text.index("; })(this);")])
    optimum, times = summary(model, data["acts"])
    out = subprocess.run(["node", str(NODE)], capture_output=True, text=True, check=True)
    js = json.loads(out.stdout)
    worst = max(abs(js["expected"][k] - v) for k, v in times.items())
    worst = max(worst, abs(js["optimum"] - optimum))
    for k in times:
        py = stats(model, table_policy(data["acts"]), float(k))
        worst = max([worst] + [abs(js["stats"][k][f] - py[f]) for f in py])
    if worst > 1e-9:
        sys.exit(f"REPLAY PARITY FAILED: worst difference {worst:.3g}")
    print(f"REPLAY PARITY OK ({len(times)} exploration rates, worst difference {worst:.1e})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=("train", "export", "check"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--races", type=int, default=2000)
    ap.add_argument("--weights")
    args = ap.parse_args()
    if args.what == "check":
        return check()
    td = load_td()
    learner = td.NetLearner(seed=args.seed)
    if args.what == "train":
        td.train(learner, tr.RaceModel(), args.races, seed=args.seed)
    else:
        import torch
        learner.online.load_state_dict(torch.load(args.weights))
    export(learner, td, args.seed, args.races)


if __name__ == "__main__":
    main()
