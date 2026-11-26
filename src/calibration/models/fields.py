"""What every model returns."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Fields:
    """Calibration fields, where each comes from (D10), and the numbers behind them."""

    values: dict[str, Any]
    provenance: dict[str, str]
    diagnostics: dict[str, Any]
