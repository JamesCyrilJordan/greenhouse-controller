from machine import Pin, I2C
import dht
import time
import ssd1306


# --- CONFIG ---
SENSOR_PIN = 15       # DHT data pin
RELAY_PIN = 16        # Relay signal pin
I2C_SCL_PIN = 1       # OLED clock
I2C_SDA_PIN = 0       # OLED data
LOW_THRESHOLD = 50.0  # °F
HIGH_THRESHOLD = 55.0  # °F
POLL_INTERVAL = 2      # seconds between measurements
SENSOR_RETRY_DELAY = 3  # seconds before retrying after error
MAX_SENSOR_ATTEMPTS = 3


def current_millis():
    if hasattr(time, "ticks_ms"):
        return time.ticks_ms()
    return int(time.time() * 1000)


def log(level, message):
    timestamp = current_millis()
    print(f"[{timestamp:>10} ms] {level.upper():<5} {message}")


def validate_config():
    if LOW_THRESHOLD >= HIGH_THRESHOLD:
        raise ValueError("LOW_THRESHOLD must be less than HIGH_THRESHOLD")


def initialize_hardware():
    log("info", "Initialising hardware")
    sensor = dht.DHT11(Pin(SENSOR_PIN))
    relay = Pin(RELAY_PIN, Pin.OUT)
    relay.value(1)  # assume relay is active LOW (1 = off)

    oled = None
    try:
        i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
        oled = ssd1306.SSD1306_I2C(128, 64, i2c)
        log("info", "Display initialised")
    except Exception as exc:
        log("error", f"Display initialisation failed: {exc}")

    return sensor, relay, oled


def c_to_f(temp_c):
    return temp_c * 9 / 5 + 32


class DisplayManager:
    def __init__(self, oled):
        self._oled = oled
        self._failed = oled is None

    def _safe_call(self, action, fallback_message):
        if self._failed:
            log("warn", fallback_message)
            return False

        try:
            action()
            return True
        except Exception as exc:
            self._failed = True
            log("error", f"Display failure: {exc}")
            log("warn", fallback_message)
            return False

    def show_status(self, temp_f, humidity, heater_on):
        message = (
            f"Temp: {temp_f:.1f}°F | Humidity: {humidity:.1f}% | "
            f"Heater: {'ON' if heater_on else 'OFF'}"
        )

        if self._failed:
            log("info", message)
            return

        def draw():
            self._oled.fill(0)
            self._oled.text("Greenhouse Monitor", 0, 0)
            self._oled.text(f"Temp: {temp_f:.1f} F", 0, 20)
            self._oled.text(f"Hum:  {humidity:.1f} %", 0, 35)
            self._oled.text(f"Heater: {'ON' if heater_on else 'OFF'}", 0, 50)
            self._oled.show()

        if self._safe_call(draw, "Display unavailable; status logged to console"):
            log("info", message)

    def show_message(self, line1, line2="", line3=""):
        if self._failed:
            log("info", f"{line1} {line2} {line3}".strip())
            return

        def draw():
            self._oled.fill(0)
            self._oled.text(line1, 0, 0)
            if line2:
                self._oled.text(line2, 0, 20)
            if line3:
                self._oled.text(line3, 0, 40)
            self._oled.show()

        self._safe_call(draw, "Display unavailable; message logged to console")


def read_environment(sensor):
    last_error = None
    for attempt in range(1, MAX_SENSOR_ATTEMPTS + 1):
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
            log("warn", f"Sensor read failed (attempt {attempt}/{MAX_SENSOR_ATTEMPTS}): {exc}")
            time.sleep(SENSOR_RETRY_DELAY)

    raise RuntimeError(f"Sensor failed after {MAX_SENSOR_ATTEMPTS} attempts: {last_error}")


def control_heater(relay, heater_on, temp_f):
    if not heater_on and temp_f < LOW_THRESHOLD:
        relay.value(0)
        log("info", "Heater turned ON")
        return True

    if heater_on and temp_f > HIGH_THRESHOLD:
        relay.value(1)
        log("info", "Heater turned OFF")
        return False

    return heater_on


def main():
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

