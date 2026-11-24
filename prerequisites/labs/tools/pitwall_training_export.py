"""Record learning runs for the Pit Wall's Training room (Phase 9), and check the record.

    python -m labs.tools.pitwall_training_export export     # train every run (about 15 minutes on 10 cores)
    python -m labs.tools.pitwall_training_export export --keep   # train only the runs the file lacks
    python -m labs.tools.pitwall_training_export check      # JS against Python, and one run re-trained

The browser cannot run PyTorch or train for minutes, so the Training room replays recorded runs.
Each run is one learner on the quiet toy race (no safety car, dry; optimum 224.49 s), scored at a
checkpoint every 100 races (2,000 environment steps) from race 0 to race 2,000:

    learners  reinforce, ac            labkit.minipg, pages 01 and 02
              ppo4, noclip4            labkit.minipg "ppo" / "noclip", 4 epochs per batch (page 04)
              ppo10, noclip10          the same with 10 epochs, the plan's n_epochs (stage 7)
              sb3                      sb3_contrib.MaskablePPO with the capstone report's settings
    rewards   centred                  each lap -(lap time - 10 s), as the capstone uses
              raw                      each lap -lap time, the plan's reward without Finding C's offset
              vecnorm                  (sb3 only) the raw reward through SB3's VecNormalize(norm_reward=True,
                                       norm_obs=False), the fallback the plan's Risks table names
    seeds     0, 1, 2

At each checkpoint the record holds the greedy plan (the race is deterministic, so the plan is the
whole policy as far as the ruler sees), its exact gap to the optimum, the mean policy entropy over
the 20 states that plan visits, and the critic's value of the start state (minipg's V table, or
SB3's value head; REINFORCE has no critic).

`check` loads site/assets/pitwall/training_data.js in Node and replays every recorded plan with
engine.js on the quiet race: each plan's time minus oracle.js's optimum must equal the recorded gap
to 1e-9. Then it re-trains one minipg run and one MaskablePPO checkpoint in Python and compares.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "site" / "assets" / "pitwall" / "training_data.js"
NODE = Path(__file__).with_name("pitwall_training_parity_node.js")
RACES, EVERY, SEEDS = 2000, 100, (0, 1, 2)
LEARNERS = ("reinforce", "ac", "ppo4", "noclip4", "ppo10", "noclip10", "sb3")
OFFSETS = {"centred": 10.0, "raw": 0.0, "vecnorm": 0.0}
SB3_KW = dict(n_steps=400, batch_size=100, n_epochs=10, gamma=1.0, ent_coef=0.01, verbose=0, policy_kwargs=dict(net_arch=[32, 32]))


def _path(probs_at):
    """Follow the greedy plan of probs_at(lap, compound, age, used) -> (probs, mask) from the start."""
    from labs.labkit import toyrace as tr
    from labs.labkit.racegym import QUIET

    lap, c, age, used, plan, ent = 1, tr.A, 1, False, [], []
    while lap <= QUIET.horizon:
        p, mask = probs_at(lap, c, age, used)
        p = np.where(mask, p, 0.0)
        a = int(np.argmax(p))
        q = p[p > 0]
        plan.append(a)
        ent.append(float(-(q * np.log(q)).sum()))
        nc, age = QUIET.next_tyre(c, age, a)
        used = used or nc != c
        c = nc
        lap += 1
    return "".join(map(str, plan)), float(np.mean(ent))


def run_minipg(learner: str, reward: str, seed: int) -> dict:
    from labs.labkit import minipg, toyrace as tr
    from labs.labkit.racegym import QUIET, legal_mask

    kind = {"ppo4": "ppo", "ppo10": "ppo", "noclip4": "noclip", "noclip10": "noclip"}.get(learner, learner)
    epochs = 10 if learner.endswith("10") else 4
    rec = {"gap": [], "plan": [], "ent": [], "v": []}
    holder = {}
    real_gap, real_result = minipg.gap, minipg.Result

    class Result(real_result):
        def __init__(self, *a, **k):
            super().__init__(*a, **k)
            holder["res"] = self

    def snap(theta):
        plan, ent = _path(lambda lap, c, age, used: (minipg.probs(theta.get((lap, c, age, used), np.zeros(3)), legal_mask(QUIET, lap, c, used)), legal_mask(QUIET, lap, c, used)))
        rec["gap"].append(round(real_gap(theta), 9))
        rec["plan"].append(plan)
        rec["ent"].append(round(ent, 4))
        V = holder["res"].V if "res" in holder else {}
        rec["v"].append(None if kind == "reinforce" else round(float(V.get((1, tr.A, 1, False), 0.0)), 3))

    def gap_hook(theta, model=QUIET):
        snap(theta)
        return rec["gap"][-1]

    minipg.gap, minipg.Result = gap_hook, Result
    try:
        snap({})
        minipg.train(kind, RACES, seed, epochs=epochs, offset=OFFSETS[reward], checkpoint_every=EVERY)
    finally:
        minipg.gap, minipg.Result = real_gap, real_result
    assert len(rec["gap"]) == RACES // EVERY + 1, len(rec["gap"])
    return rec


def run_sb3(reward: str, seed: int, steps: int | None = None) -> dict:
    import torch as th
    from sb3_contrib import MaskablePPO
    from stable_baselines3.common.callbacks import BaseCallback
    from stable_baselines3.common.vec_env import DummyVecEnv, VecNormalize

    from labs.labkit import toyrace as tr
    from labs.labkit.racegym import QUIET, TinyRaceEnv, encode, gap_of_sb3, legal_mask

    th.set_num_threads(1)
    rec = {"gap": [], "plan": [], "ent": [], "v": []}
    every = EVERY * QUIET.horizon

    def snap(model):
        def probs_at(lap, c, age, used):
            mask = legal_mask(QUIET, lap, c, used)
            with th.no_grad():
                d = model.policy.get_distribution(th.as_tensor(encode(lap, c, age, used)[None]), action_masks=mask[None])
            return d.distribution.probs[0].numpy().astype(float), mask

        plan, ent = _path(probs_at)
        with th.no_grad():
            v = float(model.policy.predict_values(th.as_tensor(encode(1, tr.A, 1, False)[None]))[0, 0])
        rec["gap"].append(round(gap_of_sb3(model), 9))
        rec["plan"].append(plan)
        rec["ent"].append(round(ent, 4))
        rec["v"].append(round(v, 3))

    class CB(BaseCallback):
        def _on_step(self):
            if self.num_timesteps % every == 0:
                snap(self.model)
            return True

    env = TinyRaceEnv(offset=OFFSETS[reward])
    if reward == "vecnorm":
        env = VecNormalize(DummyVecEnv([lambda: TinyRaceEnv(offset=0.0)]), norm_obs=False, norm_reward=True)
    model = MaskablePPO("MlpPolicy", env, seed=seed, **SB3_KW)
    snap(model)
    model.learn(steps or RACES * QUIET.horizon, callback=CB())
    return rec


def one(job):
    learner, reward, seed = job
    rec = run_sb3(reward, seed) if learner == "sb3" else run_minipg(learner, reward, seed)
    return f"{learner}|{reward}|{seed}", rec


def export(workers: int, keep: bool = False) -> None:
    from labs.labkit import minipg
    from labs.labkit.racegym import optimum

    jobs = [(l, r, s) for l in LEARNERS for r in OFFSETS for s in SEEDS if r != "vecnorm" or l == "sb3"]
    jobs.sort(key=lambda j: j[0] != "sb3")  # the long ones first
    runs = load_data()["runs"] if keep and OUT.exists() else {}
    jobs = [j for j in jobs if f"{j[0]}|{j[1]}|{j[2]}" not in runs]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        for key, rec in ex.map(one, jobs):
            runs[key] = rec
            print(f"{key:22s} final gap {rec['gap'][-1]:6.2f} s", flush=True)
    data = {
        "source": "labs/tools/pitwall_training_export.py: labkit.minipg and sb3_contrib.MaskablePPO on the quiet toy race",
        "optimum": round(optimum(), 9), "uniform": round(minipg.uniform_gap(), 9), "races": RACES, "every": EVERY,
        "offsets": OFFSETS, "sb3": {k: v for k, v in SB3_KW.items() if k != "verbose"},
        "runs": {k: runs[k] for k in sorted(runs)},
    }
    OUT.write_text("/* Recorded learning runs for the Pit Wall's Training room (Phase 9). Written by\n"
                   "   labs/tools/pitwall_training_export.py; checked by its `check` action. */\n"
                   "(function (root) { var D = " + json.dumps(data, separators=(",", ":")) + ";\n"
                   "  if (typeof module !== \"undefined\" && module.exports) module.exports = D;\n"
                   "  else { root.PitWall = root.PitWall || {}; root.PitWall.trainingData = D; }\n"
                   "})(this);\n", encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size // 1024} KB, {len(runs)} runs)")


def load_data() -> dict:
    text = OUT.read_text(encoding="utf-8")
    return json.loads(text[text.index("var D = ") + 8: text.index(";\n  if (typeof module")])


def check() -> int:
    out = subprocess.run(["node", str(NODE)], capture_output=True, text=True, cwd=ROOT)
    print(out.stdout.strip() or out.stderr.strip())
    if out.returncode:
        return 1
    data = load_data()
    bad = 0
    for key, rec in (("reinforce|raw|1", run_minipg("reinforce", "raw", 1)), ("ppo4|centred|2", run_minipg("ppo4", "centred", 2))):
        same = rec == data["runs"][key]
        bad += not same
        print(f"re-trained {key}: {'same record' if same else 'DIFFERENT'}")
    sb = run_sb3("centred", 0, steps=2 * EVERY * 20)
    want = {k: v[:3] for k, v in data["runs"]["sb3|centred|0"].items()}
    worst = max(abs(a - b) for a, b in zip(sb["gap"], want["gap"]))
    same = sb["plan"] == want["plan"] and worst < 1e-6
    bad += not same
    print(f"re-trained sb3|centred|0 to race 200: {'same plans and gaps' if same else 'DIFFERENT'} (worst gap difference {worst:.1e})")
    print("TRAINING CHECK OK" if not bad else "TRAINING CHECK FAILED")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=("export", "check"))
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--keep", action="store_true", help="keep the runs already in the file")
    a = ap.parse_args()
    if a.action == "export":
        export(a.workers, a.keep)
        return 0
    return check()


if __name__ == "__main__":
    sys.exit(main())
