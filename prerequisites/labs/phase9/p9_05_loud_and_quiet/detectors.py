"""Lab p9-05 · Loud and quiet.

TASK 1. Run the given script from the prerequisites/ folder:

    python labs/phase9/p9_05_loud_and_quiet/run_variants.py

It trains the same mini PPO five ways, one correct and four with a planted bug, and prints only
what a training log would show you: the mean race time as training goes on. From that alone,
decide which variants are broken LOUDLY (you would notice from the curve) and which QUIETLY (the
curve looks like learning). Put the code names in the two sets below. Then rerun with --gaps to see
the exact distance of each from the optimum.

TASK 2. Three detectors. Each receives the internals of one PPO update, as returned by
`labs.labkit.minipg.inspect_update(bug)`:

    trace["ratios"]            one array per epoch: pi_new(a) / pi_old(a) for every sample
    trace["used_advantages"]   the advantages actually fed to the clipped update
    trace["raw_advantages"]    the same before any standardising
    trace["rewards"], trace["values"]   one race of the batch, and the critic's V on its laps
    trace["advantage_fn"]      the estimator the trainer used: fn(rewards, values, lam) -> array

Each detector returns True if its piece is right. It is graded mutation-style: it must return True
for the correct trainer, and False for the trainer carrying its one bug.

Run `python -m labs check p9-05`.
"""

from __future__ import annotations

import numpy as np

LOUD = None  # TODO: your answer
QUIET = None  # TODO: your answer


def ratio_moves(trace) -> bool:
    """After the first epoch the policy has changed, so some ratio must differ from 1.

    (Page 04: the ratio compares the policy being updated with the FROZEN one that collected the
    batch. If "old" is re-read from the current policy, every ratio is 1 and the clip never binds.)
    """
    # TODO: any ratio in an epoch after the first that is not 1 (to 1e-9)
    raise NotImplementedError("TODO p9-05: any ratio in an epoch after the first that is not 1 (to 1e-9)")


def gae_matches_returns(trace) -> bool:
    """At lam = 1 and gamma = 1, GAE on a complete episode must equal G_t - V(s_t) (page 03)."""
    rewards, values = np.asarray(trace["rewards"]), np.asarray(trace["values"])
    # TODO: run trace["advantage_fn"] at lam=1.0 and compare with the returns-to-go minus values
    raise NotImplementedError("TODO p9-05: run trace[\"advantage_fn\"] at lam=1.0 and compare with the returns-to-go minus values")


def advantages_standardised(trace) -> bool:
    """The advantages fed to the update have mean 0 and standard deviation 1 (page 05)."""
    # TODO: mean within 1e-6 of 0 and std within 1e-3 of 1
    raise NotImplementedError("TODO p9-05: mean within 1e-6 of 0 and std within 1e-3 of 1")
