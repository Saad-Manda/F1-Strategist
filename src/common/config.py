"""Strict YAML config loading: a missing key is an error, never a default."""

from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from src.common.errors import ConfigError


class ConfigSection:
    """Read-only view of one mapping in a config file.

    It has no `get` method on purpose, so a fallback value cannot be hidden in the code.
    """

    def __init__(self, values: dict[str, Any], file: Path, path: str = "") -> None:
        self._values = values
        self._file = file
        self._path = path

    def __getitem__(self, key: str) -> Any:
        full_key = f"{self._path}.{key}" if self._path else str(key)
        if key not in self._values:
            known = ", ".join(str(k) for k in self._values)
            raise ConfigError(f"{self._file}: missing key '{full_key}' (found: {known})")
        if self._values[key] is None:
            raise ConfigError(f"{self._file}: key '{full_key}' is empty")
        return self._wrap(self._values[key], full_key)

    def _wrap(self, value: Any, path: str) -> Any:
        if isinstance(value, dict):
            return ConfigSection(value, self._file, path)
        if isinstance(value, list):
            return tuple(self._wrap(item, f"{path}[{i}]") for i, item in enumerate(value))
        return value

    def __iter__(self) -> Iterator[str]:
        return iter(self._values)

    def __len__(self) -> int:
        return len(self._values)

    def __contains__(self, key: object) -> bool:
        return key in self._values

    def __repr__(self) -> str:
        return f"ConfigSection({self._file}, '{self._path}')"


class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that rejects repeated keys, which YAML would silently overwrite."""


def _construct_unique_mapping(loader: _UniqueKeyLoader, node: yaml.MappingNode) -> dict:
    seen = set()
    for key_node, _ in node.value:
        key = loader.construct_object(key_node)
        if key in seen:
            raise ConfigError(f"duplicate key '{key}' on line {key_node.start_mark.line + 1}")
        seen.add(key)
    return loader.construct_mapping(node, deep=True)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_unique_mapping
)


def load_config(file: str | Path) -> ConfigSection:
    """Load a YAML config file. Each file is read once per process."""
    return _load(Path(file).resolve())


@lru_cache(maxsize=None)
def _load(file: Path) -> ConfigSection:
    try:
        text = file.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise ConfigError(f"{file}: config file not found") from error
    try:
        values = yaml.load(text, Loader=_UniqueKeyLoader)
    except ConfigError as error:
        raise ConfigError(f"{file}: {error}") from error
    except yaml.YAMLError as error:
        raise ConfigError(f"{file}: invalid YAML: {error}") from error
    if not isinstance(values, dict) or not values:
        raise ConfigError(f"{file}: expected a non-empty mapping at the top level")
    return ConfigSection(values, file)
