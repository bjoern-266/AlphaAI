"""Tests für die Logging-Einrichtung."""

from __future__ import annotations

import logging

from core.logging_config import get_logger, setup_logging


def test_setup_logging_returns_root_logger() -> None:
    logger = setup_logging()
    assert logger is logging.getLogger()
    assert logger.handlers, "Es muss mindestens ein Handler registriert sein."


def test_setup_logging_is_idempotent() -> None:
    first = setup_logging()
    handler_count = len(first.handlers)
    second = setup_logging()
    assert len(second.handlers) == handler_count, "Handler dürfen sich nicht verdoppeln."


def test_get_logger_uses_given_name() -> None:
    logger = get_logger("alpha_ai.test")
    assert logger.name == "alpha_ai.test"
