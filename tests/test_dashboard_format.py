"""Tests der reinen Anzeige-Formatierung (keine Berechnung)."""

from __future__ import annotations

import math

from dashboard import format as fmt


def test_placeholder_constant():
    assert fmt.PLACEHOLDER == "—"


def test_na_none():
    assert fmt.na(None) is True


def test_na_nan():
    assert fmt.na(float("nan")) is True


def test_na_number():
    assert fmt.na(0.0) is False
    assert fmt.na(5) is False


def test_text_placeholder_for_none():
    assert fmt.text(None) == "—"


def test_text_value():
    assert fmt.text("abc") == "abc"
    assert fmt.text(7) == "7"


def test_number_default_decimals():
    assert fmt.number(1234.5) == "1,234.50"


def test_number_custom_decimals():
    assert fmt.number(1.23456, 3) == "1.235"


def test_number_none():
    assert fmt.number(None) == "—"


def test_number_infinity():
    assert fmt.number(float("inf")) == "∞"


def test_integer():
    assert fmt.integer(1500) == "1,500"
    assert fmt.integer(3.0) == "3"


def test_integer_none():
    assert fmt.integer(None) == "—"


def test_currency():
    assert fmt.currency(1200.5) == "1,200.50 €"


def test_currency_custom_symbol():
    assert fmt.currency(1000, symbol="$") == "1,000.00 $"


def test_currency_none():
    assert fmt.currency(None) == "—"


def test_signed_currency_positive():
    assert fmt.signed_currency(50.0) == "+50.00 €"


def test_signed_currency_negative():
    assert fmt.signed_currency(-50.0) == "-50.00 €"


def test_signed_currency_none():
    assert fmt.signed_currency(None) == "—"


def test_percent_already_in_percent():
    assert fmt.percent(12.5) == "12.5 %"


def test_percent_none():
    assert fmt.percent(None) == "—"


def test_percent_infinity():
    assert fmt.percent(float("inf")) == "∞"


def test_ratio_as_percent_multiplies_by_100():
    assert fmt.ratio_as_percent(0.6) == "60.0 %"


def test_ratio_as_percent_none():
    assert fmt.ratio_as_percent(None) == "—"


def test_signed_percent():
    assert fmt.signed_percent(2.4) == "+2.40 %"
    assert fmt.signed_percent(-1.0) == "-1.00 %"


def test_signed_percent_none():
    assert fmt.signed_percent(None) == "—"


def test_profit_factor_regular():
    assert fmt.profit_factor(1.85) == "1.85"


def test_profit_factor_infinity():
    assert fmt.profit_factor(math.inf) == "∞"


def test_profit_factor_none():
    assert fmt.profit_factor(None) == "—"


def test_number_zero_is_not_placeholder():
    assert fmt.number(0.0) == "0.00"
