"""Turn OpenF1's stints into one tyre label per lap, and flag every label that was changed."""

from dataclasses import dataclass, replace
from functools import lru_cache

import pandas as pd

from src.data.spec.frames import COMPOUNDS, UNKNOWN


@dataclass(frozen=True)
class Stint:
    """One set of tyres as OpenF1 reports it, laps inclusive."""

    start: int
    end: int
    compound: str
    age_at_start: int


def label_laps(
    stints: list[Stint],
    pit_out_laps: list[int],
    laps: list[int],
    opening_compound: bool = False,
) -> pd.DataFrame:
    """Compound, tyre age, stint number and label quality for each of one driver's laps.

    OpenF1 starts a stint one lap early where the pit boxes come before the timing line
    (Monaco, Montreal, Melbourne; see E10). The pit-out lap is the one to trust.

    With `opening_compound`, stints that begin before the first pit-out without a stop are
    removed, because the car cannot have changed tyres (2025 Spa).
    """
    if not laps:
        return pd.DataFrame(columns=["lap", "stint", "compound", "tyre_age", "label"])
    stints = [s for s in stints if s.start <= max(laps)]
    pit_outs = sorted(p for p in set(pit_out_laps) if p > 1)

    removed_until = 0
    if opening_compound and pit_outs:
        stints, removed_until = _drop_stints_before_first_stop(stints, pit_outs)

    stints = _drop_empty_stints(stints, pit_outs)
    stints = _merge_continuations(stints, pit_outs)
    boundaries = [s.start for s in stints[1:]]
    matches = match_boundaries(tuple(boundaries), tuple(pit_outs))

    moved = list(stints)
    shifted: set[int] = set()
    suspect: set[int] = set()
    for i, boundary in enumerate(boundaries):
        pit_out = matches[i]
        if pit_out is None:
            suspect.update((i, i + 1))
        elif pit_out != boundary:
            shifted.update(range(boundary, pit_out))
            moved[i] = replace(moved[i], end=pit_out - 1)
            moved[i + 1] = replace(moved[i + 1], start=pit_out)

    unused = sorted(set(pit_outs) - {m for m in matches if m is not None})
    rows = []
    for lap in laps:
        index = next((i for i, s in enumerate(moved) if s.start <= lap <= s.end), None)
        if index is None or moved[index].compound not in COMPOUNDS:
            rows.append((lap, pd.NA if index is None else index + 1, UNKNOWN, pd.NA, "missing"))
            continue
        stint = moved[index]
        # An unexplained stop leaves the tyre age unknown for the rest of that stint.
        after_unused_stop = any(stint.start < p <= lap for p in unused)
        if index in suspect or after_unused_stop:
            label = "suspect"
        elif index == 0 and 1 < lap <= removed_until:
            label = "repaired"
        elif lap in shifted:
            label = "shifted"
        else:
            label = "raw"
        age = stint.age_at_start + lap - stint.start + 1
        rows.append((lap, index + 1, stint.compound, age, label))
    return pd.DataFrame(rows, columns=["lap", "stint", "compound", "tyre_age", "label"])


def match_boundaries(
    boundaries: tuple[int, ...], pit_outs: tuple[int, ...]
) -> list[int | None]:
    """Pair each stint start with a pit-out on the same lap or the next one.

    Pairs keep their order. The most pairs win, then the fewest shifts.
    """

    @lru_cache(maxsize=None)
    def best(i: int, j: int) -> tuple[int, int, tuple[int | None, ...]]:
        if i == len(boundaries):
            return 0, 0, ()
        if j == len(pit_outs):
            return 0, 0, (None,) * (len(boundaries) - i)
        pairs, shifts, rest = best(i + 1, j)
        options = [(pairs, shifts, (None, *rest)), best(i, j + 1)]
        offset = pit_outs[j] - boundaries[i]
        if offset in (0, 1):
            pairs, shifts, rest = best(i + 1, j + 1)
            options.append((pairs + 1, shifts - offset, (pit_outs[j], *rest)))
        return max(options, key=lambda option: option[:2])

    return list(best(0, 0)[2])


def _drop_empty_stints(stints: list[Stint], pit_outs: list[int]) -> list[Stint]:
    """Remove zero-length stints, except those that a pit-out shows to be real."""
    stints = list(stints)
    i = 0
    while i < len(stints):
        if stints[i].end < stints[i].start:
            matches = match_boundaries(tuple(s.start for s in stints[1:]), tuple(pit_outs))
            begins_with_stop = i == 0 or matches[i - 1] is not None
            ends_with_stop = i < len(stints) - 1 and matches[i] is not None
            if not (begins_with_stop and ends_with_stop):
                del stints[i]
                continue
        i += 1
    return stints


def _drop_stints_before_first_stop(
    stints: list[Stint], pit_outs: list[int]
) -> tuple[list[Stint], int]:
    first_stop = pit_outs[0]
    opening = stints[0]
    # The first real stint may start one lap before its pit-out.
    later = [s for s in stints[1:] if s.start >= first_stop - 1]
    dropped = [s for s in stints[1:] if s not in later]
    if not dropped:
        return stints, 0
    end = later[0].start - 1 if later else dropped[-1].end
    return [replace(opening, end=end), *later], end


def _merge_continuations(stints: list[Stint], pit_outs: list[int]) -> list[Stint]:
    """Join stints that split without a stop and carry the same tyres on."""
    merged: list[Stint] = []
    for stint in stints:
        if merged:
            last = merged[-1]
            same_tyres = (
                stint.compound == last.compound
                and stint.start == last.end + 1
                and stint.age_at_start == last.age_at_start + stint.start - last.start
            )
            stopped = stint.start in pit_outs or stint.start + 1 in pit_outs
            if same_tyres and not stopped:
                merged[-1] = replace(last, end=stint.end)
                continue
        merged.append(stint)
    return merged
