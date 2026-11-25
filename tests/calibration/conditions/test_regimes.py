import pandas as pd
import pytest

from src.calibration.conditions.regimes import lap_regimes, tyre_shares, weather_rejection

RULES = {
    "damp_start_share": 0.3,
    "damp_end_share": 0.7,
    "wet_share": 0.5,
    "median_filter_laps": 3,
}
LETTERS = {"DRY": "-", "DAMP": "d", "WET": "W"}


def regimes(inter, wet=None):
    shares = pd.DataFrame({"inter_share": inter, "wet_share": wet or [0.0] * len(inter)})
    return "".join(LETTERS[r] for r in lap_regimes(shares, RULES))


@pytest.mark.parametrize(
    "inter, expected",
    [
        ([0.0, 0.0, 0.3, 0.6, 0.9, 1.0], "--dddd"),  # fails if damp starts after 30%
        ([1.0, 0.9, 0.7, 0.6, 0.4, 0.0], "ddd---"),  # fails if damp ends at 30%
        ([0.0, 0.29, 0.29, 0.29, 0.0], "-----"),  # fails if a few gamblers make it damp
        ([0.0, 0.4, 0.5, 0.4, 0.0], "-ddd-"),  # fails if a phase under 70% is lost
        ([1.0, 1.0, 0.6, 0.6, 1.0, 1.0, 0.5], "dddddd-"),  # fails if a dip ends the phase
        ([0.0, 0.0, 0.9, 0.0, 0.0], "-----"),  # fails without the median filter
    ],
)
def test_damp(inter, expected):
    assert regimes(inter) == expected


def test_wet_needs_half_of_the_cars_on_wet_tyres():
    # Fails if the WET share is compared with the wrong limit.
    assert regimes([0.0, 0.5, 0.5, 0.51, 0.6], [1.0, 0.5, 0.5, 0.49, 0.4]) == "WWWdd"


def test_wet_tyres_count_as_rain_tyres():
    # Fails if DAMP looks at INTERMEDIATE only.
    assert regimes([0.2] * 4, [0.2] * 4) == "dddd"


def laps(*rows):
    return pd.DataFrame(rows, columns=["lap", "compound", "label"])


def test_untrusted_labels_are_left_out():
    # Fails if suspect labels count as known, or shares use all cars.
    shares = tyre_shares(
        laps(
            (1, "INTERMEDIATE", "raw"),
            (1, "SOFT", "repaired"),
            (1, "WET", "suspect"),
            (1, "UNKNOWN", "missing"),
        )
    ).loc[1]
    assert (shares["known_share"], shares["inter_share"], shares["wet_share"]) == (0.5, 0.5, 0.0)


def test_rejection_names_the_laps():
    # Fails if the limit is ignored, or exactly the limit is rejected.
    shares = pd.DataFrame({"known_share": [1.0, 0.4, 0.5]}, index=[1, 2, 3])
    assert weather_rejection(shares, 0.5) == "known tyres fall to 40% (laps 2-2)"
    assert weather_rejection(shares, 0.4) == ""
