"""Utility helpers and configuration constants for the greenhouse controller."""

import time

LOW_THRESHOLD = 50.0  # °F
HIGH_THRESHOLD = 55.0  # °F
POLL_INTERVAL = 2  # seconds between measurements
SENSOR_RETRY_DELAY = 3  # seconds before retrying after error
MAX_SENSOR_ATTEMPTS = 3


__all__ = [
    "LOW_THRESHOLD",
    "HIGH_THRESHOLD",
    "POLL_INTERVAL",
    "SENSOR_RETRY_DELAY",
    "MAX_SENSOR_ATTEMPTS",
    "current_millis",
    "log",
    "validate_config",
]


def current_millis():
    """Return the current time in milliseconds."""
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int(time.time() * 1000)


def log(level, message):
    """Simple logging helper that includes a millisecond timestamp."""
    timestamp = current_millis()
    print(
        "[{timestamp:>10} ms] {level:<5} {message}".format(
            timestamp=timestamp,
            level=level.upper(),
            message=message,
        )
    )


def validate_config():
    """Ensure the configured temperature thresholds are valid."""
    if LOW_THRESHOLD >= HIGH_THRESHOLD:
        raise ValueError("LOW_THRESHOLD must be less than HIGH_THRESHOLD")
