"""Position Sizing – empfohlene Positionsgröße aus dem Risiko je Trade.

Berechnet Stückzahl, Orderwert, Stop-/Take-Profit-Abstand und geschätzte
Kosten – ausschließlich aus Konto-/Risikowerten (``settings.toml``) und
Ausführungsparametern (``risk_rules.toml``). Es wird **keine** Order erzeugt.
Trägt selbst **keine** Komponente zum Gesamtrisiko bei (``component = ""``);
die Kennzahlen liefert es über ``details['sizing']``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from risk.base import BaseRiskModel, RiskContext, RiskModelOutput, compute_position_sizing


class PositionSizingModel(BaseRiskModel):
    """Empfohlene Positionsgröße (keine Risikokomponente, nur Kennzahlen)."""

    name = "position_sizing"
    component = ""
    value_range = "0..100 (Risikoauslastung in %)"

    def compute(self, context: RiskContext, params: Mapping[str, Any]) -> RiskModelOutput:
        """Berechnet die Positionsgröße und liefert sie in ``details['sizing']``."""
        sizing = compute_position_sizing(context, params)
        reasons = [
            f"Positionswert: {sizing.suggested_position_size:.2f}",
            f"Stückzahl: {sizing.estimated_shares:g}",
            f"Stop-Abstand: {sizing.suggested_stop_distance:.4f}",
            f"Take-Profit-Abstand: {sizing.suggested_take_profit:.4f}",
            f"CRV: {sizing.suggested_risk_reward:.2f}",
        ]
        warnings: list[str] = []
        if sizing.estimated_shares <= 0:
            warnings.append("Keine handelbare Stückzahl (fehlender/ungültiger Preis oder ATR).")
        return RiskModelOutput(
            name=self.name,
            value=sizing.maximum_risk_pct,
            reasons=reasons,
            warnings=warnings,
            details={"sizing": sizing},
        )
