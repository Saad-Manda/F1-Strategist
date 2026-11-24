"""The list of races in configs/races.yaml."""

from dataclasses import dataclass
from pathlib import Path

from src.common.config import ConfigSection, load_config
from src.common.errors import ConfigError

RACES_FILE = Path("configs/races.yaml")
ROLES = ("fit", "holdout", "conditions_only", "frequency_only")
REPAIRS = ("opening_compound",)


@dataclass(frozen=True)
class Race:
    """One race and where its raw data comes from."""

    id: str
    circuit: str
    year: int
    source: str
    role: str
    event: str = ""
    session_key: int = 0
    repairs: tuple[str, ...] = ()


def load_races(file: str | Path = RACES_FILE) -> list[Race]:
    """Every race of the project, in file order."""
    config = load_config(file)
    races = [_parse(section, config) for section in config["races"]]
    ids = [race.id for race in races]
    repeated = sorted({race_id for race_id in ids if ids.count(race_id) > 1})
    if repeated:
        raise ConfigError(f"{file}: repeated race ids {repeated}")
    return races


def load_cross_checks(file: str | Path = RACES_FILE) -> list[Race]:
    """The races that also exist in the second source."""
    config = load_config(file)
    return [_parse(section, config) for section in config["cross_checks"]]


def _parse(section: ConfigSection, config: ConfigSection) -> Race:
    source = section["source"]
    race = Race(
        id=section["id"],
        circuit=section["circuit"],
        year=section["year"],
        source=source,
        role=section["role"],
        event=section["event"] if source == "fastf1" else "",
        session_key=section["session_key"] if source == "openf1" else 0,
        repairs=section["repairs"] if "repairs" in section else (),
    )
    if source not in ("fastf1", "openf1"):
        raise ConfigError(f"{race.id}: unknown source '{source}'")
    if race.role not in ROLES:
        raise ConfigError(f"{race.id}: unknown role '{race.role}'")
    unknown = set(race.repairs) - set(REPAIRS)
    if unknown:
        raise ConfigError(f"{race.id}: unknown repairs {sorted(unknown)}")
    if race.year > config["last_allowed_year"]:
        raise ConfigError(f"{race.id}: {race.year} is held out for the transfer check (D23)")
    if (race.year in config["holdout_years"]) != (race.role == "holdout"):
        raise ConfigError(f"{race.id}: role '{race.role}' does not match the holdout rule (D25)")
    return race
