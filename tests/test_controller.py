"""Unit tests for the greenhouse controller logic."""

import importlib
import sys
import types
from pathlib import Path

import pytest


def _install_stub_modules():
    """Provide stub versions of the hardware-specific modules."""
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
            def __init__(self, channel, scl=None, sda=None):
                self.channel = channel
                self.scl = scl
                self.sda = sda

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
            def __init__(self, width, height, i2c):
                self.width = width
                self.height = height
                self.i2c = i2c

            def fill(self, *_):
                pass

            def text(self, *_):
                pass

            def show(self):
                pass

        ssd1306_module.SSD1306_I2C = SSD1306_I2C
        sys.modules["ssd1306"] = ssd1306_module


_install_stub_modules()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
hardware = importlib.import_module("greenhouse_controller.hardware")
sensors = importlib.import_module("greenhouse_controller.sensors")
utils = importlib.import_module("greenhouse_controller.utils")
main_module = importlib.import_module("main")


class RelayStub:
    def __init__(self):
        self.state = 1
        self.values = []

    def value(self, new_value=None):
        if new_value is None:
            return self.state
        self.state = new_value
        self.values.append(new_value)


class SensorStub:
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


@pytest.fixture(autouse=True)
def _patch_sleep(monkeypatch):
    # Avoid waiting in tests when retry logic sleeps.
    monkeypatch.setattr(sensors.time, "sleep", lambda _seconds: None)


def test_c_to_f_conversion():
    assert sensors.c_to_f(0) == pytest.approx(32.0)
    assert sensors.c_to_f(25) == pytest.approx(77.0)


def test_control_heater_turns_on_when_below_threshold():
    relay = RelayStub()
    heater_on = hardware.control_heater(relay, False, utils.LOW_THRESHOLD - 5)

    assert heater_on is True
    assert relay.values == [0]


def test_control_heater_turns_off_when_above_threshold():
    relay = RelayStub()
    heater_on = hardware.control_heater(relay, True, utils.HIGH_THRESHOLD + 5)

    assert heater_on is False
    assert relay.values == [1]


def test_control_heater_keeps_state_within_band():
    relay = RelayStub()
    heater_on = hardware.control_heater(
        relay,
        True,
        (utils.LOW_THRESHOLD + utils.HIGH_THRESHOLD) / 2,
    )

    assert heater_on is True
    assert relay.values == []


def test_read_environment_retries_then_succeeds():
    sensor = SensorStub(
        temp_c=20,
        humidity=40,
        failures=[OSError("temporary failure")],
    )

    temp_f, humidity = sensors.read_environment(sensor)

    assert temp_f == pytest.approx(68.0)
    assert humidity == pytest.approx(40)


def test_read_environment_raises_runtime_error_after_failures(monkeypatch):
    sensor = SensorStub(
        temp_c=20,
        humidity=40,
        failures=[ValueError("bad read"), OSError("still bad")],
    )
    monkeypatch.setattr(utils, "MAX_SENSOR_ATTEMPTS", 2)

    with pytest.raises(RuntimeError) as excinfo:
        sensors.read_environment(sensor)

    assert "Sensor failed after" in str(excinfo.value)


def test_validate_config_rejects_invalid_thresholds(monkeypatch):
    monkeypatch.setattr(utils, "LOW_THRESHOLD", 60.0)
    monkeypatch.setattr(utils, "HIGH_THRESHOLD", 55.0)

    with pytest.raises(ValueError):
        utils.validate_config()


def test_main_enforces_periodic_cooldown(monkeypatch):
    relay = RelayStub()
    sensor = SensorStub(temp_c=5, humidity=40)

    class DisplayStub:
        def __init__(self, _oled):
            self.statuses = []
            self.messages = []

        def show_status(self, temp_f, humidity, heater_on):
            self.statuses.append((temp_f, humidity, heater_on))

        def show_message(self, *lines):
            self.messages.append(lines)

    class FakeTime:
        def __init__(self):
            self.now = 0

        def time(self):
            return self.now

        def sleep(self, seconds):
            self.now += seconds

    fake_time = FakeTime()

    monkeypatch.setattr(
        main_module,
        "time",
        types.SimpleNamespace(time=fake_time.time, sleep=fake_time.sleep),
    )
    monkeypatch.setattr(main_module, "POLL_INTERVAL", 60)
    monkeypatch.setattr(
        main_module,
        "initialize_hardware",
        lambda: (sensor, relay, None),
    )
    monkeypatch.setattr(main_module, "DisplayManager", DisplayStub)

    call_count = {"count": 0}

    def fake_read_environment(_sensor):
        call_count["count"] += 1
        if call_count["count"] > 12:
            raise KeyboardInterrupt
        return utils.LOW_THRESHOLD - 10, 35

    monkeypatch.setattr(main_module, "read_environment", fake_read_environment)

    main_module.main()

    assert relay.values[:3] == [0, 1, 0]
