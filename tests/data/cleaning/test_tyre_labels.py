"""Each test names the code change that would make it fail."""

from src.data.cleaning.tyre_labels import Stint, label_laps, match_boundaries


def labelled(stints, pit_outs, last_lap, **options):
    """Lap -> (compound, tyre age, label)."""
    table = label_laps([Stint(*s) for s in stints], pit_outs, list(range(1, last_lap + 1)), **options)
    return {row.lap: (row.compound, row.tyre_age, row.label) for row in table.itertuples()}


def test_clean_stints_are_unchanged():
    # Fails if an ordinary stop is moved or flagged, or the age is off by one.
    laps = labelled([(1, 3, "SOFT", 2), (4, 6, "HARD", 0)], [4], 6)
    assert laps[1] == ("SOFT", 3, "raw")
    assert laps[3] == ("SOFT", 5, "raw")
    assert laps[4] == ("HARD", 1, "raw")
    assert laps[6] == ("HARD", 3, "raw")


def test_early_stint_start_moves_to_the_pit_out_lap():
    # Fails if the Monaco shift is not applied: lap 4 ran on the old SOFT.
    laps = labelled([(1, 3, "SOFT", 0), (4, 6, "HARD", 0)], [5], 6)
    assert laps[4] == ("SOFT", 4, "shifted")
    assert laps[5] == ("HARD", 1, "raw")


def test_shifted_stops_on_consecutive_laps_all_move():
    # Fails if pairs are chosen greedily: 2->3, 3->4, 4->5 (2025 Australia).
    assert match_boundaries((2, 3, 4), (3, 4, 5)) == [3, 4, 5]


def test_exact_match_beats_a_shift():
    # Fails if the tie-break on shifts is removed.
    assert match_boundaries((4,), (4, 5)) == [4]


def test_pairs_never_reach_back_or_skip_two_laps():
    # Fails if the allowed offset is widened.
    assert match_boundaries((5,), (4,)) == [None]
    assert match_boundaries((5,), (7,)) == [None]


def test_unexplained_tyre_change_is_suspect_on_both_sides():
    # Fails if a compound change without a stop is trusted.
    laps = labelled([(1, 3, "SOFT", 0), (4, 6, "HARD", 0)], [], 6)
    assert {lap[2] for lap in laps.values()} == {"suspect"}


def test_stop_without_a_new_stint_makes_later_laps_suspect():
    # Fails if a possible tyre change hides inside a stint.
    laps = labelled([(1, 6, "HARD", 0)], [4], 6)
    assert laps[3][2] == "raw"
    assert laps[4][2] == "suspect"
    assert laps[6][2] == "suspect"


def test_doubt_ends_at_the_next_explained_stop():
    # Fails if one unexplained stop taints the rest of the race.
    laps = labelled([(1, 6, "HARD", 0), (7, 9, "SOFT", 0)], [4, 7], 9)
    assert laps[6][2] == "suspect"
    assert laps[7] == ("SOFT", 1, "raw")


def test_split_stint_on_the_same_tyres_is_joined():
    # Fails if a bookkeeping split is mistaken for a stop.
    laps = labelled([(1, 3, "HARD", 0), (4, 6, "HARD", 3)], [], 6)
    assert laps[4] == ("HARD", 4, "raw")


def test_same_compound_with_reset_age_is_not_joined():
    # Fails if the join ignores the tyre age.
    assert labelled([(1, 3, "HARD", 0), (4, 6, "HARD", 0)], [], 6)[4][2] == "suspect"


def test_empty_stint_without_a_stop_is_ignored():
    # Fails if a zero-length artefact flags its neighbours (2023 Montreal).
    laps = labelled([(1, 0, "MEDIUM", 0), (1, 6, "HARD", 0)], [], 6)
    assert laps[1] == ("HARD", 1, "raw")


def test_empty_opening_stint_is_kept_when_a_stop_follows():
    # Fails if a lap 1 tyre change is dropped (2024 Monaco red flag).
    laps = labelled([(1, 0, "MEDIUM", 0), (1, 6, "HARD", 0)], [2], 6)
    assert laps[1] == ("MEDIUM", 1, "shifted")
    assert laps[2] == ("HARD", 1, "raw")


def test_stint_after_the_last_lap_is_ignored():
    # Fails if tyres fitted for the cool-down lap flag the last stint (2024 Spa).
    laps = labelled([(1, 6, "HARD", 0), (7, 7, "SOFT", 0)], [], 6)
    assert laps[6] == ("HARD", 6, "raw")


def test_opening_compound_holds_until_the_first_stop():
    # Fails if the 2025 Spa repair is lost: the cars started on INTERMEDIATE.
    stints = [(1, 1, "INTERMEDIATE", 0), (2, 4, "MEDIUM", 0), (5, 8, "MEDIUM", 0)]
    laps = labelled(stints, [5], 8, opening_compound=True)
    assert laps[1] == ("INTERMEDIATE", 1, "raw")
    assert laps[2] == ("INTERMEDIATE", 2, "repaired")
    assert laps[4] == ("INTERMEDIATE", 4, "repaired")
    assert laps[5] == ("MEDIUM", 1, "raw")


def test_opening_compound_is_only_applied_on_request():
    # Fails if the repair runs on every race.
    laps = labelled([(1, 1, "INTERMEDIATE", 0), (2, 4, "MEDIUM", 0), (5, 8, "HARD", 0)], [5], 8)
    assert laps[2][0] == "MEDIUM"


def test_opening_compound_keeps_a_shifted_first_stop():
    # Fails if a stint starting one lap before its pit-out is removed as false.
    laps = labelled([(1, 3, "SOFT", 0), (4, 6, "HARD", 0)], [5], 6, opening_compound=True)
    assert laps[4] == ("SOFT", 4, "shifted")
    assert laps[5] == ("HARD", 1, "raw")


def test_laps_outside_every_stint_are_missing():
    # Fails if the last compound is extrapolated.
    assert labelled([(1, 3, "SOFT", 0)], [], 4)[4][0] == "UNKNOWN"
    assert labelled([(1, 3, "SOFT", 0)], [], 4)[4][2] == "missing"


def test_unknown_compound_is_missing():
    # Fails if an invalid compound is passed through.
    assert labelled([(1, 3, "UNKNOWN", 0)], [], 3)[2][2] == "missing"
    assert labelled([(1, 3, "None", 0)], [], 3)[2][0] == "UNKNOWN"
