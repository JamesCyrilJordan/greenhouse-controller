"""Tests for the Wi-Fi manager and logger helper modules."""

from __future__ import annotations

import importlib
import sys
import types

import pytest


@pytest.fixture(autouse=True)
def stub_secrets_module():
    module = types.ModuleType("secrets")
    module.SSID = "demo-ssid"
    module.PASSWORD = "demo-password"
    sys.modules["secrets"] = module
    try:
        yield module
    finally:
        sys.modules.pop("secrets", None)


@pytest.fixture
def fake_network_module():
    module = types.ModuleType("network")

    class FakeWLAN:
        def __init__(self, interface):
            self.interface = interface
            self._active = False
            self._connected = False
            self.connect_calls = 0

        def active(self, state=None):
            if state is None:
                return self._active
            self._active = state

        def isconnected(self):
            return self._connected

        def connect(self, *_):
            self.connect_calls += 1
            self._connected = True

    module.WLAN = FakeWLAN
    module.FakeWLAN = FakeWLAN
    module.STA_IF = 0
    sys.modules["network"] = module
    try:
        yield module
    finally:
        sys.modules.pop("network", None)


@pytest.fixture
def wifi_manager_module(fake_network_module):
    sys.modules.pop("wifi_manager", None)
    module = importlib.import_module("wifi_manager")
    return importlib.reload(module)


def test_wifi_manager_reconnects_and_calls_callback(monkeypatch, wifi_manager_module):
    wifi_manager = wifi_manager_module
    wifi_manager.configure(reconnect_interval_seconds=0.05, on_reconnect=lambda: None)
    wifi_manager.connect(max_attempts=1)

    wlan = wifi_manager._wlan  # type: ignore[attr-defined]
    reconnects = []

    def _callback():
        reconnects.append(True)

    wifi_manager.configure(reconnect_interval_seconds=0.05, on_reconnect=_callback)
    wlan._connected = False  # type: ignore[attr-defined]
    wifi_manager._last_reconnect_attempt = (
        wifi_manager.utime.ticks_ms() - wifi_manager._reconnect_interval_ms - 1  # type: ignore[attr-defined]
    )

    monkeypatch.setattr(wifi_manager.utime, "sleep_ms", lambda _ms: None, raising=False)

    wifi_manager.maintain_connection()

    assert reconnects == [True]
    assert wlan._connected  # type: ignore[attr-defined]
    assert wlan.connect_calls >= 1  # type: ignore[attr-defined]


@pytest.fixture
def logger_module():
    sys.modules.pop("logger", None)
    module = importlib.import_module("logger")
    return importlib.reload(module)


class DummyResponse:
    def __init__(self, status_code=204, text="ok"):
        self.status_code = status_code
        self.text = text

    def close(self):
        pass


def test_logger_process_sends_payload(monkeypatch, logger_module):
    logger = logger_module
    logger.configure(endpoint="https://example.test/log", retry_interval_seconds=0)
    logger._buffer.clear()  # type: ignore[attr-defined]
    logger._last_attempt_ms = 0  # type: ignore[attr-defined]

    payload = {
        "timestamp": 1700000000,
        "temperature_f": 70.0,
        "humidity": 45.0,
        "heater_on": True,
    }
    logger.log(payload)

    posts = []

    def fake_post(url, data, headers):
        posts.append((url, data, headers))
        return DummyResponse()

    monkeypatch.setattr(logger, "wifi_manager", types.SimpleNamespace(is_connected=lambda: True))
    monkeypatch.setattr(logger, "urequests", types.SimpleNamespace(post=fake_post))

    logger.process()

    assert posts
    assert not logger._buffer  # type: ignore[attr-defined]


def test_logger_process_defers_when_wifi_down(monkeypatch, logger_module):
    logger = logger_module
    logger.configure(retry_interval_seconds=0)
    logger._buffer.clear()  # type: ignore[attr-defined]
    logger._last_attempt_ms = 0  # type: ignore[attr-defined]

    logger.log({
        "temperature_f": 71.0,
        "humidity": 40.0,
        "heater_on": False,
    })

    monkeypatch.setattr(logger, "wifi_manager", types.SimpleNamespace(is_connected=lambda: False))

    def _fail_post(*_args, **_kwargs):
        raise AssertionError("post() should not be called when Wi-Fi is down")

    monkeypatch.setattr(logger, "urequests", types.SimpleNamespace(post=_fail_post))

    logger.process()

    assert len(logger._buffer) == 1  # type: ignore[attr-defined]
