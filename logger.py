"""Asynchronous-friendly logging helper for MicroPython."""

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
    import ujson as json
except ImportError:  # pragma: no cover
    import json  # type: ignore

try:
    import urequests
except ImportError:  # pragma: no cover - desktop testing
    urequests = None  # type: ignore

try:  # Optional dependency so the module works without Wi-Fi helper
    import wifi_manager
except ImportError:  # pragma: no cover
    wifi_manager = None  # type: ignore

_endpoint = "https://example.com/logs"
_retry_interval_ms = 10000
_last_attempt_ms = 0
_buffer = []
_max_buffer = 100


def configure(endpoint=None, retry_interval_seconds=10, max_buffer=100):
    """Configure the logger endpoint, retry interval, and buffer size."""

    global _endpoint, _retry_interval_ms, _max_buffer
    if endpoint:
        _endpoint = endpoint
    _retry_interval_ms = max(1000, int(retry_interval_seconds * 1000))
    _max_buffer = max(1, int(max_buffer))


def _normalize_entry(data):
    timestamp = data.get("timestamp", utime.time())
    entry = {
        "timestamp": int(timestamp),
        "temperature_f": float(data["temperature_f"]),
        "humidity": float(data["humidity"]),
        "heater_on": bool(data["heater_on"]),
    }
    return entry


def log(data):
    """Queue a reading for background delivery."""

    if len(_buffer) >= _max_buffer:
        _buffer.pop(0)

    try:
        entry = _normalize_entry(data)
    except Exception as exc:  # pragma: no cover - invalid payload safety
        sys.print_exception(exc)
        return

    _buffer.append(entry)


def _can_attempt_send(now):
    if not _buffer:
        return False
    if wifi_manager and not wifi_manager.is_connected():
        return False
    return utime.ticks_diff(now, _last_attempt_ms) >= _retry_interval_ms


def process():
    """Send queued logs if the retry interval has elapsed."""

    global _last_attempt_ms

    if not urequests or not _buffer:
        return

    now = utime.ticks_ms()
    if not _can_attempt_send(now):
        return

    payload = json.dumps(_buffer[0])
    headers = {"Content-Type": "application/json"}

    try:
        response = urequests.post(_endpoint, data=payload, headers=headers)
        status = getattr(response, "status_code", None)
        text = response.text if hasattr(response, "text") else None
        response.close()
    except Exception as exc:
        _last_attempt_ms = now
        sys.print_exception(exc)
        return

    _last_attempt_ms = now
    if status and 200 <= status < 300:
        _buffer.pop(0)
    else:
        if text:
            print("logger: server error", status, text)


# Compatibility alias for cooperative schedulers
tick = process

