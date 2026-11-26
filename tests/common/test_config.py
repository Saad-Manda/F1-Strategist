"""Each test names the code change that would make it fail."""

from pathlib import Path

import pytest

from src.common.config import load_config
from src.common.errors import ConfigError
from tests.conftest import COMPOUNDS


@pytest.fixture
def write_config(tmp_path: Path):
    def write(text: str) -> Path:
        file = tmp_path / "example.yaml"
        file.write_text(text, encoding="utf-8")
        return file

    return write


def test_reads_nested_values(write_config):
    # Fails if nested mappings are not wrapped.
    config = load_config(write_config("fuel:\n  kg: 1.9\nbounds: [1, 2]\n"))
    assert config["fuel"]["kg"] == 1.9
    assert config["bounds"] == (1, 2)


def test_missing_key_names_file_and_full_key(write_config):
    # Fails if the error drops the file or the parent path, or a default is returned.
    file = write_config("fuel:\n  kg: 1.9\n")
    with pytest.raises(ConfigError) as error:
        load_config(file)["fuel"]["sensitivity"]
    assert "example.yaml" in str(error.value)
    assert "fuel.sensitivity" in str(error.value)


def test_missing_key_inside_a_list_names_its_position(write_config):
    # Fails if mappings inside lists are returned as plain dicts.
    config = load_config(write_config("circuits:\n  - name: spa\n"))
    with pytest.raises(ConfigError, match=r"circuits\[0\]\.laps"):
        config["circuits"][0]["laps"]


def test_fallback_values_are_impossible(write_config):
    # Fails if ConfigSection gains a dict-style get, for example by subclassing Mapping.
    assert not hasattr(load_config(write_config("a: 1\n")), "get")


def test_empty_value_is_an_error(write_config):
    # Fails if an empty YAML value is passed on as None.
    with pytest.raises(ConfigError, match="'pit_loss' is empty"):
        load_config(write_config("pit_loss:\n"))["pit_loss"]


def test_zero_and_false_are_values(write_config):
    # Fails if the empty check uses truthiness instead of None.
    config = load_config(write_config("a: 0\nb: false\n"))
    assert config["a"] == 0
    assert config["b"] is False


def test_missing_file_is_an_error(tmp_path):
    # Fails if a missing file loads as an empty config (N15).
    with pytest.raises(ConfigError, match="not found"):
        load_config(tmp_path / "absent.yaml")


@pytest.mark.parametrize("text", ["", "- 1\n- 2\n", "just text\n"])
def test_file_without_a_mapping_is_an_error(write_config, text):
    # Fails if the top-level type check is removed.
    with pytest.raises(ConfigError, match="non-empty mapping"):
        load_config(write_config(text))


def test_duplicate_key_is_an_error(write_config):
    # Fails with the plain YAML loader, which keeps the last value.
    with pytest.raises(ConfigError, match="example.yaml.*duplicate key 'a' on line 2"):
        load_config(write_config("a: 1\na: 2\n"))


def test_invalid_yaml_is_an_error(write_config):
    # Fails if YAML errors escape without the file name.
    with pytest.raises(ConfigError, match="example.yaml.*invalid YAML"):
        load_config(write_config("a: [1, 2\n"))


def test_weather_penalties_use_full_compound_names():
    # Fails if INTERMEDIATE is shortened to INTER again in defaults.yaml.
    penalties = load_config("configs/defaults.yaml")["calibration"]["weather_penalty_defaults"]
    assert set(penalties) == {"DRY", "DAMP", "WET"}
    for weather in penalties:
        assert set(penalties[weather]) == set(COMPOUNDS)
