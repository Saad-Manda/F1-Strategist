"""Lab p9-05, given script: train the mini PPO five ways and show only what a training log shows.

    python labs/phase9/p9_05_loud_and_quiet/run_variants.py           # curves only (under a minute)
    python labs/phase9/p9_05_loud_and_quiet/run_variants.py --gaps    # also the exact gap to the optimum

Run it from the prerequisites/ folder. One variant is correct; four have one planted bug each.
The names are the bugs' code names in labs/labkit/minipg.py; read their descriptions there only
after you have made your call in detectors.py.
"""

import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path(__file__).resolve().parents if (p / "labs" / "labkit").exists())))

import numpy as np  # noqa: E402

from labs.labkit import minipg  # noqa: E402

RACES, SEEDS = 1000, (0,)


def blocks(times, size=200):
    return [float(np.mean(times[i : i + size])) for i in range(0, len(times), size)]


if __name__ == "__main__":
    show_gaps = "--gaps" in sys.argv
    print(f"Mean race time per block of 200 training races, {RACES} races, seeds {SEEDS}. Lower is better; a random policy averages about 268 s.\n")
    for bug in minipg.BUGS:
        name = "correct" if bug is None else bug
        for seed in SEEDS:
            res = minipg.train("ppo", RACES, seed, bug=bug)
            curve = "  ".join(f"{t:6.1f}" for t in blocks(res.times))
            extra = f"   gap to the optimum {minipg.gap(res.theta):6.2f} s" if show_gaps else ""
            print(f"{name:10s} seed {seed}:  {curve}{extra}", flush=True)
    if not show_gaps:
        print("\nMake your call in detectors.py (LOUD and QUIET), then rerun with --gaps.")
