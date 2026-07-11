"""Tests der Lade-/Fehler-Anzeige (Zustand anzeigen, nie Exception werfen)."""

from __future__ import annotations

import pytest

from dashboard.feedback import ERROR_MESSAGES, error_spec, loading_spec
from dashboard.state import ErrorState, LoadingState
from models.dashboard import TONE_DANGER, TONE_INFO, TONE_WARNING


@pytest.mark.parametrize(
    "state",
    [
        ErrorState.LOADING,
        ErrorState.OFFLINE,
        ErrorState.NO_DATA,
        ErrorState.DISCONNECTED,
        ErrorState.TIMEOUT,
        ErrorState.ERROR,
    ],
)
def test_error_spec_has_message_and_is_placeholder(state):
    spec = error_spec(state)
    assert spec.placeholder is True
    assert spec.text == ERROR_MESSAGES[state]
    assert spec.text != ""


def test_error_spec_widget_id():
    assert error_spec(ErrorState.ERROR).widget_id == "error_state"


def test_error_tone_offline_is_danger():
    assert error_spec(ErrorState.OFFLINE).metadata["tone"] == TONE_DANGER


def test_error_tone_loading_is_info():
    assert error_spec(ErrorState.LOADING).metadata["tone"] == TONE_INFO


def test_error_tone_no_data_is_warning():
    assert error_spec(ErrorState.NO_DATA).metadata["tone"] == TONE_WARNING


@pytest.mark.parametrize(
    "state,text",
    [
        (LoadingState.SKELETON, "Skeleton"),
        (LoadingState.PROGRESS, "Progress"),
        (LoadingState.FADE, "Fade"),
    ],
)
def test_loading_spec_text(state, text):
    spec = loading_spec(state)
    assert spec.placeholder is True
    assert spec.text == text


def test_loading_spec_widget_id():
    assert loading_spec(LoadingState.SKELETON).widget_id == "loading_state"


def test_loading_spec_metadata_carries_state():
    spec = loading_spec(LoadingState.PROGRESS)
    assert spec.metadata["loading_state"] == "progress"


def test_error_spec_metadata_carries_state():
    spec = error_spec(ErrorState.TIMEOUT)
    assert spec.metadata["error_state"] == "timeout"


def test_error_messages_cover_all_states():
    for state in ErrorState:
        assert state in ERROR_MESSAGES
