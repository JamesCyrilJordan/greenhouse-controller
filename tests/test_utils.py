"""Unit tests for utility helpers."""

import types

import pytest

from greenhouse_controller import utils


def test_current_millis_prefers_ticks_ms(monkeypatch):
    fake_time = types.SimpleNamespace(ticks_ms=lambda: 1234)
    monkeypatch.setattr(utils, "time", fake_time)

    assert utils.current_millis() == 1234


def test_current_millis_falls_back_to_time(monkeypatch):
    fake_time = types.SimpleNamespace(time=lambda: 1.2345)
    monkeypatch.setattr(utils, "time", fake_time)

    assert utils.current_millis() == 1234


def test_log_formats_output(capsys, monkeypatch):
    monkeypatch.setattr(utils, "current_millis", lambda: 42)

    utils.log("info", "hello world")

    captured = capsys.readouterr().out
    assert captured == "[        42 ms] INFO  hello world\n"


def test_validate_config_allows_valid_thresholds(monkeypatch):
    monkeypatch.setattr(utils, "LOW_THRESHOLD", 40.0)
    monkeypatch.setattr(utils, "HIGH_THRESHOLD", 50.0)

    # Should not raise when configuration is valid
    utils.validate_config()

