"""Unit tests for hardware initialisation helpers."""

from hardware_stubs import install_stub_modules

install_stub_modules()

import machine
import pytest
import ssd1306
import sht31

from greenhouse_controller import hardware


def test_initialize_display_success(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "greenhouse_controller.hardware.log",
        lambda level, message: logs.append((level, message)),
    )

    oled = hardware.initialize_display()

    assert isinstance(oled, ssd1306.SSD1306_I2C)
    assert logs == [
        (
            "info",
            "Display initialised at address 0x3C on I2C1 (SCL=GP5, SDA=GP4)",
        )
    ]


def test_initialize_display_failure(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "greenhouse_controller.hardware.log",
        lambda level, message: logs.append((level, message)),
    )

    class BrokenDisplay:
        def __init__(self, *_args, **_kwargs):
            raise RuntimeError("boom")

    monkeypatch.setattr(ssd1306, "SSD1306_I2C", BrokenDisplay)

    oled = hardware.initialize_display()

    assert oled is None
    assert logs == [
        ("error", "Display initialisation failed: boom (I2C1, SCL=GP5, SDA=GP4)")
    ]


def test_initialize_display_custom_bus(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "greenhouse_controller.hardware.log",
        lambda level, message: logs.append((level, message)),
    )

    oled = hardware.initialize_display(bus=0, scl_pin=3, sda_pin=2)

    assert isinstance(oled, ssd1306.SSD1306_I2C)
    last_init = machine.I2C.last_init
    assert last_init["channel"] == 0
    assert last_init["scl"].pin_number == 3
    assert last_init["sda"].pin_number == 2
    assert logs == [
        (
            "info",
            "Display initialised at address 0x3C on I2C0 (SCL=GP3, SDA=GP2)",
        )
    ]


def test_initialize_hardware_returns_components(monkeypatch):
    components = hardware.initialize_hardware()

    sensor, relay, fan_relay, display = components

    assert isinstance(sensor, hardware.SHT31Adapter)
    assert isinstance(relay, machine.Pin)
    assert isinstance(fan_relay, machine.Pin)
    assert display is None or isinstance(display, ssd1306.SSD1306_I2C)


def test_initialize_sensor_detects_sht31_and_logs(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "greenhouse_controller.hardware.log",
        lambda level, message: logs.append((level, message)),
    )

    sensor = hardware.initialize_sensor()
    sensor.measure()

    assert sensor.temperature() == pytest.approx(22.0)
    assert sensor.humidity() == pytest.approx(55.0)
    assert logs == [
        (
            "info",
            "SHT31-D initialised at address 0x44 on I2C0 (SCL=GP1, SDA=GP0)",
        )
    ]


def test_initialize_sensor_prefers_alternate_address(monkeypatch):
    monkeypatch.setattr(machine.I2C, "default_addresses", [0x45, 0x3C])
    logs = []
    monkeypatch.setattr(
        "greenhouse_controller.hardware.log",
        lambda level, message: logs.append((level, message)),
    )

    sensor = hardware.initialize_sensor(bus=1, scl_pin=2, sda_pin=3)
    sensor.measure()

    assert sensor.temperature() == pytest.approx(22.0)
    assert logs == [
        (
            "info",
            "SHT31-D initialised at address 0x45 on I2C1 (SCL=GP2, SDA=GP3)",
        )
    ]


def test_initialize_sensor_raises_when_not_found(monkeypatch):
    monkeypatch.setattr(machine.I2C, "default_addresses", [0x3C])

    with pytest.raises(RuntimeError) as excinfo:
        hardware.initialize_sensor()

    assert "SHT31-D not detected" in str(excinfo.value)


def test_initialize_sensor_with_micropython_next(monkeypatch):
    import builtins

    original_next = builtins.next

    def single_arg_next(iterator):
        return original_next(iterator)

    monkeypatch.setattr("builtins.next", single_arg_next)

    logs = []
    monkeypatch.setattr(
        "greenhouse_controller.hardware.log",
        lambda level, message: logs.append((level, message)),
    )

    sensor = hardware.initialize_sensor()
    sensor.measure()

    assert sensor.temperature() == pytest.approx(22.0)
    assert logs == [
        (
            "info",
            "SHT31-D initialised at address 0x44 on I2C0 (SCL=GP1, SDA=GP0)",
        )
    ]


def test_sht31_adapter_respects_driver_methods(monkeypatch):
    driver = sht31.SHT31(machine.I2C(0))
    driver.measure_behaviour = "tuple"
    adapter = hardware.SHT31Adapter(driver)

    adapter.measure()
    assert adapter.temperature() == pytest.approx(22.0)
    assert adapter.humidity() == pytest.approx(55.0)

    class TempOnlyDriver:
        def __init__(self):
            self.temperature = 25.5
            self.humidity = 40.0

        def measure(self):
            return None

    adapter = hardware.SHT31Adapter(TempOnlyDriver())
    adapter.measure()
    assert adapter.temperature() == pytest.approx(25.5)
    assert adapter.humidity() == pytest.approx(40.0)

    class GetTempHumiDriver:
        def get_temp_humi(self):
            return (26.0, 41.0)

    adapter = hardware.SHT31Adapter(GetTempHumiDriver())
    adapter.measure()
    assert adapter.temperature() == pytest.approx(26.0)
    assert adapter.humidity() == pytest.approx(41.0)

    class NoMeasurementDriver:
        pass

    adapter = hardware.SHT31Adapter(NoMeasurementDriver())
    with pytest.raises(RuntimeError):
        adapter.measure()
