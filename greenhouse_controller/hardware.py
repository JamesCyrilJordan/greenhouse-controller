"""Hardware initialisation and actuator control for the greenhouse controller."""

from machine import I2C, Pin
import dht
import ssd1306

from . import utils
from .utils import log

SENSOR_PIN = 15  # DHT data pin
RELAY_PIN = 16  # Relay signal pin
FAN_PIN = 17  # Fan relay signal pin
I2C_SCL_PIN = 1  # OLED clock
I2C_SDA_PIN = 0  # OLED data

__all__ = [
    "SENSOR_PIN",
    "RELAY_PIN",
    "FAN_PIN",
    "I2C_SCL_PIN",
    "I2C_SDA_PIN",
    "initialize_hardware",
    "initialize_sensor",
    "initialize_relay",
    "initialize_fan",
    "initialize_display",
    "control_heater",
    "control_fan",
]


def initialize_sensor(pin=None):
    """Initialise and return the DHT sensor instance."""
    if pin is None:
        pin = SENSOR_PIN
    return dht.DHT11(Pin(pin))


def initialize_relay(pin=None):
    """Initialise the relay output pin."""
    if pin is None:
        pin = RELAY_PIN
    relay = Pin(pin, Pin.OUT)
    relay.value(1)  # assume relay is active LOW (1 = off)
    return relay


def initialize_fan(pin=None):
    """Initialise the fan relay output pin."""
    if pin is None:
        pin = FAN_PIN
    fan_relay = Pin(pin, Pin.OUT)
    fan_relay.value(1)  # assume relay is active LOW (1 = off)
    return fan_relay


def initialize_display(scl_pin=None, sda_pin=None):
    """Attempt to initialise the OLED display, returning ``None`` on failure."""
    if scl_pin is None:
        scl_pin = I2C_SCL_PIN
    if sda_pin is None:
        sda_pin = I2C_SDA_PIN

    try:
        i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))
        oled = ssd1306.SSD1306_I2C(128, 64, i2c)
        log("info", "Display initialised")
        return oled
    except Exception as exc:  # pragma: no cover - exercised via behaviour
        log("error", "Display initialisation failed: {exc}".format(exc=exc))
        return None


def initialize_hardware():
    """Initialise all hardware components."""
    log("info", "Initialising hardware")
    sensor = initialize_sensor()
    relay = initialize_relay()
    fan_relay = initialize_fan()
    display = initialize_display()
    return sensor, relay, fan_relay, display


def control_heater(relay, heater_on, temp_f):
    """Toggle the heater relay based on the measured temperature."""
    low_threshold = utils.LOW_THRESHOLD
    high_threshold = utils.HIGH_THRESHOLD

    if not heater_on and temp_f < low_threshold:
        relay.value(0)
        log("info", "Heater turned ON")
        return True

    if heater_on and temp_f > high_threshold:
        relay.value(1)
        log("info", "Heater turned OFF")
        return False

    return heater_on


def control_fan(fan_relay, fan_on, temp_f):
    """Toggle the fan relay based on the measured temperature."""
    high_threshold = utils.FAN_THRESHOLD
    off_threshold = high_threshold - 2  # add light hysteresis to avoid chatter

    if not fan_on and temp_f > high_threshold:
        fan_relay.value(0)
        log("info", "Fan turned ON")
        return True

    if fan_on and temp_f <= off_threshold:
        fan_relay.value(1)
        log("info", "Fan turned OFF")
        return False

    return fan_on
