"""Sensor reading helpers for the greenhouse controller."""

import time

from . import utils
from .utils import log

__all__ = ["c_to_f", "read_environment"]


def c_to_f(temp_c):
    """Convert a temperature from Celsius to Fahrenheit."""
    return temp_c * 9 / 5 + 32


def read_environment(sensor):
    """Read temperature and humidity from the configured sensor."""
    last_error = None
    max_attempts = utils.MAX_SENSOR_ATTEMPTS
    retry_delay = utils.SENSOR_RETRY_DELAY

    for attempt in range(1, max_attempts + 1):
        try:
            sensor.measure()
            temp_c = sensor.temperature()
            humidity = sensor.humidity()

            if temp_c is None or humidity is None:
                raise ValueError("Sensor returned None readings")

            temp_f = c_to_f(temp_c)
            return temp_f, humidity
        except (OSError, ValueError) as exc:
            last_error = exc
            log(
                "warn",
                "Sensor read failed (attempt {attempt}/{max_attempts}): {exc}".format(
                    attempt=attempt,
                    max_attempts=max_attempts,
                    exc=exc,
                ),
            )
            time.sleep(retry_delay)

    raise RuntimeError(
        "Sensor failed after {max_attempts} attempts: {error}".format(
            max_attempts=max_attempts,
            error=last_error,
        )
    )
