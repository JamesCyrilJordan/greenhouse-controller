"""Support utilities for providing stub hardware modules in tests."""

import sys
import types


class RelayStub:
    """A controllable relay stub that records value changes."""

    def __init__(self):
        self.state = 1
        self.values = []

    def value(self, new_value=None):
        if new_value is None:
            return self.state
        self.state = new_value
        self.values.append(new_value)


class SensorStub:
    """A DHT-like sensor stub with configurable readings and failures."""

    def __init__(self, *, temp_c, humidity, failures=None):
        self._temp_c = temp_c
        self._humidity = humidity
        self._failures = list(failures or [])

    def measure(self):
        if self._failures:
            raise self._failures.pop(0)

    def temperature(self):
        return self._temp_c

    def humidity(self):
        return self._humidity


def install_stub_modules():
    """Ensure stub versions of the hardware-specific modules are installed."""

    if "machine" not in sys.modules:
        machine_module = types.ModuleType("machine")

        class Pin:
            OUT = 0

            def __init__(self, pin_number, mode=None):
                self.pin_number = pin_number
                self.mode = mode
                self._value = 1

            def value(self, new_value=None):
                if new_value is None:
                    return self._value
                self._value = new_value

        class I2C:
            last_init = None

            def __init__(self, channel, scl=None, sda=None):
                self.channel = channel
                self.scl = scl
                self.sda = sda
                self._addresses = [0x3C]
                type(self).last_init = {"channel": channel, "scl": scl, "sda": sda}

            def scan(self):
                return list(self._addresses)

        machine_module.Pin = Pin
        machine_module.I2C = I2C
        sys.modules["machine"] = machine_module

    if "dht" not in sys.modules:
        dht_module = types.ModuleType("dht")

        class DHT11:
            def __init__(self, pin):
                self.pin = pin

        dht_module.DHT11 = DHT11
        sys.modules["dht"] = dht_module

    if "ssd1306" not in sys.modules:
        ssd1306_module = types.ModuleType("ssd1306")

        class SSD1306_I2C:
            def __init__(self, width, height, i2c, addr=0x3C):
                self.width = width
                self.height = height
                self.i2c = i2c
                self.addr = addr

            def fill(self, *_):
                pass

            def text(self, *_):
                pass

            def show(self):
                pass

        ssd1306_module.SSD1306_I2C = SSD1306_I2C
        sys.modules["ssd1306"] = ssd1306_module


__all__ = ["RelayStub", "SensorStub", "install_stub_modules"]
