"""Unit tests for the greenhouse controller logic."""

import importlib
import sys
import types
from pathlib import Path

import pytest

from hardware_stubs import RelayStub, SensorStub, install_stub_modules


install_stub_modules()
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
hardware = importlib.import_module("greenhouse_controller.hardware")
sensors = importlib.import_module("greenhouse_controller.sensors")
utils = importlib.import_module("greenhouse_controller.utils")
main_module = importlib.import_module("main")


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


def test_control_fan_turns_on_and_off_with_hysteresis():
    fan = RelayStub()

    fan_on = hardware.control_fan(fan, False, utils.FAN_THRESHOLD + 5)

    assert fan_on is True
    assert fan.values == [0]

    fan_on = hardware.control_fan(fan, fan_on, utils.FAN_THRESHOLD - 2)

    assert fan_on is False
    assert fan.values[-1] == 1


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
    fan = RelayStub()
    sensor = SensorStub(temp_c=5, humidity=40)

    class DisplayStub:
        def __init__(self, _oled):
            self.statuses = []
            self.messages = []

        def show_status(self, temp_f, humidity, heater_on, fan_on):
            self.statuses.append((temp_f, humidity, heater_on, fan_on))

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
        lambda: (sensor, relay, fan, None),
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
    assert fan.values[0] == 1  # stays off in cool conditions


def test_main_handles_sensor_errors_and_shutdown(monkeypatch):
    relay = RelayStub()
    fan = RelayStub()

    class DisplayRecorder:
        def __init__(self):
            self.statuses = []
            self.messages = []

        def show_status(self, temp_f, humidity, heater_on, fan_on):
            self.statuses.append((temp_f, humidity, heater_on, fan_on))

        def show_message(self, *lines):
            self.messages.append(lines)

    display = DisplayRecorder()

    events = iter(
        [
            ("error", None),
            ("data", (utils.LOW_THRESHOLD - 5, 35)),
            ("interrupt", None),
        ]
    )

    def fake_read_environment(_sensor):
        event, payload = next(events)
        if event == "error":
            raise RuntimeError("temporary failure")
        if event == "interrupt":
            raise KeyboardInterrupt
        return payload

    sleep_calls = []

    fake_time = types.SimpleNamespace(
        time=lambda: 0,
        sleep=lambda seconds: sleep_calls.append(seconds),
    )

    monkeypatch.setattr(main_module, "time", fake_time)
    monkeypatch.setattr(main_module, "POLL_INTERVAL", 0)
    monkeypatch.setattr(main_module, "COOLDOWN_INTERVAL", 10_000)
    monkeypatch.setattr(main_module, "COOLDOWN_DURATION", 0)
    monkeypatch.setattr(main_module, "SENSOR_RETRY_DELAY", 5)
    monkeypatch.setattr(main_module, "read_environment", fake_read_environment)
    monkeypatch.setattr(main_module, "initialize_hardware", lambda: (None, relay, fan, None))
    monkeypatch.setattr(main_module, "DisplayManager", lambda _oled: display)
    monkeypatch.setattr(main_module, "control_heater", hardware.control_heater)
    monkeypatch.setattr(main_module, "validate_config", lambda: None)

    main_module.main()

    assert sleep_calls[:2] == [5, 0]
    assert relay.values == [0, 1]
    assert fan.values == [1]  # off on shutdown
    assert display.messages[0][:2] == ("Sensor error", "temporary failure")
    assert display.statuses == [(utils.LOW_THRESHOLD - 5, 35, True, False)]
    assert display.messages[-1] == ("Controller", "Shutting down")
