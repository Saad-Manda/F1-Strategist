"""The races calibration may use, with their conditions. The holdout is never loaded (D25)."""

from dataclasses import dataclass
from pathlib import Path

from src.calibration.conditions.table import RaceConditions, race_conditions
from src.common.config import ConfigSection
from src.data.spec.frames import RaceFrames
from src.data.spec.races import Race
from src.data.storage.frozen import load_race

FITTING_ROLES = ("fit", "conditions_only")


@dataclass(frozen=True)
class FittingRace:
    """One race of 2021-2024 with complete laps."""

    frames: RaceFrames
    conditions: RaceConditions

    @property
    def race(self) -> Race:
        return self.conditions.race

    @property
    def fully_dry(self) -> bool:
        """Whether every lap is known to be DRY."""
        regimes = self.conditions.table["regime"]
        return not self.conditions.weather_rejection and bool((regimes == "DRY").all())


def load_fitting_races(
    races: list[Race], interim_dir: str | Path, config: ConfigSection
) -> list[FittingRace]:
    """Every race with a fitting role, in list order."""
    loaded = []
    for race in races:
        if race.role in FITTING_ROLES:
            frames = load_race(race.id, interim_dir)
            loaded.append(FittingRace(frames, race_conditions(race, frames, config["conditions"])))
    return loaded
