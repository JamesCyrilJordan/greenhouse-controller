"""Wi-Fi manager module for MicroPython on the Raspberry Pi Pico W.

This module encapsulates Wi-Fi station (STA) connectivity logic with
automatic reconnection that can be polled from the main application
loop without blocking heater or sensor operations.
"""

from __future__ import annotations

import sys

try:  # pragma: no cover - MicroPython provides utime
    import utime  # type: ignore
except ImportError:  # pragma: no cover - host testing fallback
    import time as _time

    class _UTimeShim:
        @staticmethod
        def ticks_ms():
            return int(_time.time() * 1000)

        @staticmethod
        def ticks_diff(current, previous):
            return current - previous

        @staticmethod
        def sleep_ms(duration):
            _time.sleep(duration / 1000.0)

        @staticmethod
        def time():
            return int(_time.time())

    utime = _UTimeShim()  # type: ignore

try:
    import network
except ImportError:  # pragma: no cover - not available in host env
    network = None

try:
    from secrets import SSID, PASSWORD
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("secrets.py must define SSID and PASSWORD") from exc

_wlan = network.WLAN(network.STA_IF) if network else None
if _wlan:
    _wlan.active(True)

_reconnect_interval_ms = 10000
_reconnect_callback = None
_last_reconnect_attempt = 0


def configure(reconnect_interval_seconds=10, on_reconnect=None):
    """Configure reconnect interval and success callback."""

    global _reconnect_interval_ms, _reconnect_callback
    _reconnect_interval_ms = int(reconnect_interval_seconds * 1000)
    if on_reconnect is not None and not callable(on_reconnect):
        raise ValueError("on_reconnect must be callable or None")
    _reconnect_callback = on_reconnect


def is_connected():
    """Return True when the STA interface is connected to Wi-Fi."""

    return bool(_wlan and _wlan.isconnected())


def _attempt_connection():
    if not _wlan:
        return False
    if not SSID or not PASSWORD:
        raise RuntimeError("SSID and PASSWORD must be set in secrets.py")

    if not _wlan.active():
        _wlan.active(True)

    _wlan.connect(SSID, PASSWORD)
    return True


def connect(max_attempts=5, attempt_delay=2):
    """Connect to Wi-Fi with retries; returns True on success."""

    global _last_reconnect_attempt

    if not _wlan:
        raise RuntimeError("network module unavailable on this platform")

    attempt = 0
    while attempt < max_attempts:
        attempt += 1
        if _wlan.isconnected():
            _last_reconnect_attempt = utime.ticks_ms()
            return True

        _attempt_connection()
        start = utime.ticks_ms()
        while not _wlan.isconnected():
            if utime.ticks_diff(utime.ticks_ms(), start) >= int(attempt_delay * 1000):
                break
            utime.sleep_ms(200)

        if _wlan.isconnected():
            _last_reconnect_attempt = utime.ticks_ms()
            return True

    return False


def maintain_connection():
    """Poll this from the main loop to keep Wi-Fi alive without blocking."""

    global _last_reconnect_attempt

    if not _wlan or _reconnect_interval_ms <= 0:
        return

    if _wlan.isconnected():
        return

    now = utime.ticks_ms()
    if utime.ticks_diff(now, _last_reconnect_attempt) < _reconnect_interval_ms:
        return

    _last_reconnect_attempt = now
    if connect(max_attempts=1, attempt_delay=1):
        if _reconnect_callback:
            try:
                _reconnect_callback()
            except Exception as exc:  # pragma: no cover - callback safety
                sys.print_exception(exc)


# Backwards compatible alias
poll = maintain_connection

