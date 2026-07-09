"""Gap Risk – Risiko aus Overnight-Kurslücken.

Misst die durchschnittliche relative Kurslücke zwischen der Eröffnung und dem
vorherigen Schlusskurs über ein Fenster und skaliert sie auf ein Risiko 0..100.
Unabhängig von allen anderen Risk-Modellen.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from risk.base import (
    BaseRiskModel,
    RiskContext,
    RiskModelOutput,
    require_float,
    require_int,
    scaled_risk,
)


class GapRiskModel(BaseRiskModel):
    """Risiko aus Overnight-Kurslücken (|Open − Prev Close| / Prev Close)."""

    name = "gap_risk"
    component = "gap"
    value_range = "0..100"

    def compute(self, context: RiskContext, params: Mapping[str, Any]) -> RiskModelOutput:
        """Berechnet das Gap-Risiko."""
        window = require_int(params, "window", self.name)
        low = require_float(params, "gap_low_pct", self.name)
        high = require_float(params, "gap_high_pct", self.name)

        data = context.data
        columns = getattr(data, "columns", [])
        if data is None or "open" not in columns or "close" not in columns or len(data) < 2:
            return RiskModelOutput(self.name, 50.0, ["Gap: unvollständige Daten (neutral)."])

        prev_close = data["close"].shift(1)
        gaps = ((data["open"] - prev_close).abs() / prev_close * 100.0).dropna().tail(window)
        if gaps.empty:
            return RiskModelOutput(self.name, 50.0, ["Gap: zu wenig Historie (neutral)."])
        mean_gap = float(gaps.mean())
        value = scaled_risk(mean_gap, low, high)
        return RiskModelOutput(
            name=self.name,
            value=value,
            reasons=[f"Gap: Ø Overnight-Lücke {mean_gap:.2f} %."],
            details={"mean_gap_pct": mean_gap},
        )
