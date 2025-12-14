"""Entry point for the greenhouse controller application."""

import time

from greenhouse_controller.display import DisplayManager
from greenhouse_controller.hardware import (
    control_fan,
    control_heater,
    initialize_hardware,
)
from greenhouse_controller.sensors import read_environment
from greenhouse_controller.utils import (
    COOLDOWN_DURATION,
    COOLDOWN_INTERVAL,
    POLL_INTERVAL,
    SENSOR_RETRY_DELAY,
    log,
    validate_config,
)


def main():
    """Run the greenhouse controller loop."""
    validate_config()
    sensor, relay, fan_relay, oled = initialize_hardware()
    
    # Sensor is required for operation
    if sensor is None:
        raise RuntimeError("Sensor is disabled but required for operation. Set ENABLE_SENSOR=True in secrets.py")
    
    display = DisplayManager(oled)
    heater_on = False
    fan_on = False
    cooldown_active = False
    cooldown_start = None
    last_cooldown_end = time.time()

    try:
        while True:
            try:
                temp_f, humidity = read_environment(sensor)
            except RuntimeError as exc:
                display.show_message("Sensor error", str(exc))
                time.sleep(SENSOR_RETRY_DELAY)
                continue

            now = time.time()

            # Control fan if enabled
            if fan_relay is not None:
                fan_on = control_fan(fan_relay, fan_on, temp_f)

            # Handle heater cooldown only if heater is enabled
            if relay is not None:
                if cooldown_active:
                    if now - cooldown_start >= COOLDOWN_DURATION:
                        cooldown_active = False
                        last_cooldown_end = now
                        log("info", "Scheduled heater cooldown complete")
                    else:
                        if heater_on:
                            relay.value(1)
                            heater_on = False
                        display.show_status(temp_f, humidity, heater_on, fan_on)
                        time.sleep(POLL_INTERVAL)
                        continue

                if now - last_cooldown_end >= COOLDOWN_INTERVAL:
                    cooldown_active = True
                    cooldown_start = now
                    if heater_on:
                        relay.value(1)
                    heater_on = False
                    log("info", "Scheduled heater cooldown started")
                    display.show_status(temp_f, humidity, heater_on, fan_on)
                    time.sleep(POLL_INTERVAL)
                    continue

                heater_on = control_heater(relay, heater_on, temp_f)
            
            display.show_status(temp_f, humidity, heater_on, fan_on)
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        log("info", "Shutdown requested")
    finally:
        # Safely turn off relays if they were enabled
        if relay is not None:
            relay.value(1)
            log("info", "Heater turned OFF; exiting")
        if fan_relay is not None:
            fan_relay.value(1)
            log("info", "Fan turned OFF; exiting")
        display.show_message("Controller", "Shutting down")


if __name__ == "__main__":
    main()
