# %% [markdown]
# # Phase 6 capstone · Duel race report
#
# Run this **after** `python -m labs check p6-cap` is green. It uses the race you wrote in
# `duel_race.py` to draw the three pictures pages 02, 03 and 05 argue for: the undercut window
# that only exists once cars can be held up, what each reward design actually prefers, and
# which shapings leave the answer alone. There is nothing to implement: two predictions, then
# read the results. It runs in under a minute.

# %%
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path.cwd().resolve().parents if (p / "labs" / "labkit").exists())))

import matplotlib.pyplot as plt
import numpy as np

import duel_race as dr
from labs.labkit import predict
from labs.labkit.toyrace import PIT_B

LAB = "p6-cap"
SEEDS = range(200)
LAPS = list(range(4, 12))

# %% [markdown]
# ## 1 · The undercut window
#
# The rival stops on lap 9. The agent is the faster car but starts 0.3 s behind. For every
# single stop from lap 4 to lap 11, how often does the agent finish ahead? (Stopping earlier or
# later is a bad race on its own, rival or not.) First with
# interaction off (the plan as written: position is only a readout of time), then on (wake,
# holding up, passing).
#
# **Predict first.** With interaction **off**, how does the chance of finishing ahead depend on
# the lap the agent stops?

# %%
CHOICES = {
    "flat": "it does not: the faster car finishes ahead whenever it stops",
    "early": "stopping a few laps before the rival is clearly best",
    "late": "stopping after the rival is clearly best",
}
my_prediction = "flat"  # >>> ANSWER

predict.commit(LAB, "window-off", my_prediction, CHOICES)

# %%
rate = {
    inter: [np.mean([dr.play({lap: PIT_B}, s, interaction=inter)["finished_ahead"] for s in SEEDS]) for lap in LAPS]
    for inter in (False, True)
}
fig, ax = plt.subplots(figsize=(7, 3.2))
ax.plot(LAPS, rate[False], "o--", label="interaction off (position = sorted time)")
ax.plot(LAPS, rate[True], "o-", label="interaction on (wake, held up, passing)")
ax.axvline(9, color="grey", lw=0.8, ls=":")
ax.text(9.1, 0.5, "rival stops", color="grey", fontsize=9)
ax.set_xlabel("lap the agent stops for B")
ax.set_ylabel("share of races finished ahead")
ax.legend(fontsize=8, loc="lower left")
plt.show()
for lap, off, on in zip(LAPS, rate[False], rate[True]):
    print(f"lap {lap:2d}: off {off:.2f}   on {on:.2f}")
predict.reveal(LAB, "window-off", "with interaction off the curve is flat at 1.00: timing relative to the rival is worth nothing", correct="flat")

# %% [markdown]
# With interaction on, a window opens: stopping about three laps before the rival gets the
# agent out in front on fresh tyres while the rival is still on old ones, and the rival cannot
# simply drive back past. Stopping on the rival's own lap never works: the agent rejoins
# behind and is held up. That is page 05's argument as a picture. The undercut exists because
# of one line, the one in your stage 4.

# %% [markdown]
# ## 2 · What each reward design prefers
#
# Every one-stop and two-stop plan (190 of them), each driven on the same 60 seeds, scored under
# every design. Each design's top three, with how often that plan finishes ahead and its mean
# race time.

# %%
plans = dr.one_stop_plans() + dr.two_stop_plans()
races = [[dr.play(p, s) for s in range(60)] for p in plans]
KINDS = ["time", "time_plus_place", "gap_change", "potential", "flat_bonus", "unzeroed"]
score = {k: np.array([[sum(dr.rewards(r, k)) for r in row] for row in races]) for k in KINDS}
ahead = np.array([[r["finished_ahead"] for r in row] for row in races]).mean(1)
total = np.array([[r["total"] for r in row] for row in races]).mean(1)
for k in KINDS:
    top = np.argsort(-score[k].mean(1))[:3]
    print(f"{k:16s}" + " | ".join(f"{dr.plan_name(plans[i])} (ahead {ahead[i]:.2f}, {total[i]:.2f} s)" for i in top))

# %% [markdown]
# Read the table as page 02 asks: what did each design actually optimise?
#
# * `time` cares only about the agent's own race time, and still picks the lap-6 undercut. Alone
#   on track this car's best stop is lap 8; with the rival there, the race time itself moved,
#   because laps spent held up behind the rival are slow laps. Track position has become worth
#   time, which is page 05's point from the other side.
# * `time_plus_place` makes finishing ahead worth 20 s as well, and widens the margin by which
#   plans that finish ahead lead the table.
# * `gap_change` (the plan's formula) adds up to minus the final gap (your stage 6 test), so it
#   optimises the final margin: a design of its own, neither "time" nor "position".
# * `potential` ranks every plan exactly as `time_plus_place` does, as page 03 promises.
# * `unzeroed` keeps the same top three here; `flat_bonus` does not. It ranks a two-stop plan
#   that is more than 2 s slower in second place, because that plan spends more laps ahead.
#   Both keep the same winner, and the next section shows why that is luck, not a guarantee.

# %% [markdown]
# ## 3 · gap_change is the final margin, spread over the laps

# %%
margin = np.array([-(r["agent_time"][-1] - r["rival_time"][-1]) for row in races for r in row])
gc = score["gap_change"].ravel()
fig, ax = plt.subplots(figsize=(4.5, 3.6))
ax.plot(margin, gc, ".", ms=2)
ax.set_xlabel("final margin over the rival, s")
ax.set_ylabel("sum of gap_change rewards")
plt.show()
print(f"largest difference between the two: {np.abs(margin - gc).max():.2e} s")

# %% [markdown]
# A straight line through the origin. With γ = 1 every lap's change cancels the next one's
# start, and only the last gap is left. The plan's version even keeps this under a safety car:
# it returns 0 without updating the stored gap, so the change is credited on the next green
# lap. Page 02's worry about pushing tyres for a short-term gain needs a discount below 1.

# %% [markdown]
# ## 4 · Which shapings are safe
#
# For every plan and every race, how much does each shaping add compared with
# `time_plus_place`? A safe shaping adds the same amount to all of them.
#
# **Predict first.** Which of the three shapings shift every race by the same amount?

# %%
CHOICES2 = {
    "potential": "only the zeroed potential",
    "potential+unzeroed": "both potentials, zeroed or not: a Φ difference is a Φ difference",
    "all": "all three: they all reward being ahead",
}
my_prediction2 = "potential"  # >>> ANSWER

predict.commit(LAB, "safe-shapings", my_prediction2, CHOICES2)

# %%
fig, axes = plt.subplots(1, 3, figsize=(10, 2.8), sharey=True)
for ax, k in zip(axes, ("potential", "unzeroed", "flat_bonus")):
    shift = (score[k] - score["time_plus_place"]).ravel()
    ax.hist(shift, bins=np.arange(-0.25, 10.5, 0.5))
    ax.set_title(f"{k}: {shift.min():.2f} to {shift.max():.2f}", fontsize=10)
    ax.set_xlabel("shift added to the return")
plt.tight_layout()
plt.show()
predict.reveal(LAB, "safe-shapings", "only the zeroed potential is a single spike (exactly 1.0); the unzeroed one adds 0 or 0.5 depending on the finish; the flat bonus adds 0.5 per lap spent ahead", correct="potential")

# %% [markdown]
# * The zeroed potential is one spike at 1.0: it shifts everything equally, so no ranking can
#   change, on any race.
# * Without the zero, a race that finishes ahead gets 0.5 more than one that does not. That is
#   a hidden finishing bonus, the same one that makes the real plan's Definition-of-Done test
#   ("shaped and unshaped optima agree") fail with Φ = −position/n_cars.
# * The flat bonus pays for every lap spent ahead, so it prefers plans that run ahead longer,
#   whether or not they finish ahead. It is the plan's `potential_shaping` branch as written (E5).
#
# The last two kept the same winner in section 2 only because the winner, lap 6, is ahead
# for most of the race and finishes ahead every time. Give a design a smaller bonus, or a closer pair of plans, and they are free to pick
# differently. Your stage 7 check tells the safe case from the lucky ones without needing to
# find such a pair.
