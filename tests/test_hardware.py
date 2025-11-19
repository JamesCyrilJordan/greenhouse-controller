"""Unit tests for hardware initialisation helpers."""

from hardware_stubs import install_stub_modules

install_stub_modules()

import dht
import machine
import ssd1306

from greenhouse_controller import hardware


def test_initialize_display_success(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "greenhouse_controller.hardware.log",
        lambda level, message: logs.append((level, message)),
    )

    oled = hardware.initialize_display()

    assert isinstance(oled, ssd1306.SSD1306_I2C)
    assert logs == [("info", "Display initialised")]


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
    assert logs == [("error", "Display initialisation failed: boom")]


def test_initialize_hardware_returns_components(monkeypatch):
    components = hardware.initialize_hardware()

    sensor, relay, fan_relay, display = components

    assert isinstance(sensor, dht.DHT11)
    assert isinstance(relay, machine.Pin)
    assert isinstance(fan_relay, machine.Pin)
    assert display is None or isinstance(display, ssd1306.SSD1306_I2C)
