"""Hardware initialisation and actuator control for the greenhouse controller."""

from machine import I2C, Pin
import dht
import ssd1306

from . import utils
from .utils import log

SENSOR_PIN = 15  # DHT data pin
RELAY_PIN = 16  # Relay signal pin
I2C_SCL_PIN = 1  # OLED clock
I2C_SDA_PIN = 0  # OLED data

__all__ = [
    "SENSOR_PIN",
    "RELAY_PIN",
    "I2C_SCL_PIN",
    "I2C_SDA_PIN",
    "initialize_hardware",
    "initialize_sensor",
    "initialize_relay",
    "initialize_display",
    "control_heater",
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


def initialize_display(scl_pin=None, sda_pin=None):
    """Attempt to initialise the OLED display, returning ``None`` on failure."""
    if scl_pin is None:
        scl_pin = I2C_SCL_PIN
    if sda_pin is None:
        sda_pin = I2C_SDA_PIN

    try:
        i2c = I2C(0, scl=Pin(scl_pin), sda=Pin(sda_pin))
        addresses = set(i2c.scan())
        preferred_addresses = (0x3C, 0x3D)
        address = next((addr for addr in preferred_addresses if addr in addresses), None)

        if address is None:
            log(
                "error",
                "Display not detected on I2C0 (SCL=GP{0}, SDA=GP{1}); found {2}".format(
                    scl_pin, sda_pin, sorted(addresses)
                ),
            )
            return None

        oled = ssd1306.SSD1306_I2C(128, 64, i2c, addr=address)
        log("info", "Display initialised at address 0x{0:02X}".format(address))
        return oled
    except Exception as exc:  # pragma: no cover - exercised via behaviour
        log("error", "Display initialisation failed: {exc}".format(exc=exc))
        return None


def initialize_hardware():
    """Initialise all hardware components."""
    log("info", "Initialising hardware")
    sensor = initialize_sensor()
    relay = initialize_relay()
    display = initialize_display()
    return sensor, relay, display


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
