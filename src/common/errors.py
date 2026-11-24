"""Errors raised when the project refuses to continue."""


class StratexError(Exception):
    """Base class for every error this project raises on purpose."""


class ConfigError(StratexError):
    """A config file is missing, malformed, or lacks a key."""


class CalibrationError(StratexError):
    """Race data or a calibrated value is implausible."""


class ContractError(StratexError):
    """A shared interface was used in a way its contract forbids."""
