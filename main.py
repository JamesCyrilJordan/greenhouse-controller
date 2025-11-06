"""Entry point for the greenhouse controller application."""

import time

from greenhouse_controller.display import DisplayManager
from greenhouse_controller.hardware import control_heater, initialize_hardware
from greenhouse_controller.sensors import read_environment
from greenhouse_controller.utils import (
    POLL_INTERVAL,
    SENSOR_RETRY_DELAY,
    log,
    validate_config,
)


def main():
    """Run the greenhouse controller loop."""
    validate_config()
    sensor, relay, oled = initialize_hardware()
    display = DisplayManager(oled)
    heater_on = False

    try:
        while True:
            try:
                temp_f, humidity = read_environment(sensor)
            except RuntimeError as exc:
                display.show_message("Sensor error", str(exc))
                time.sleep(SENSOR_RETRY_DELAY)
                continue

            heater_on = control_heater(relay, heater_on, temp_f)
            display.show_status(temp_f, humidity, heater_on)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        log("info", "Shutdown requested")
    finally:
        relay.value(1)
        display.show_message("Controller", "Shutting down")
        log("info", "Heater turned OFF; exiting")


if __name__ == "__main__":
    main()
