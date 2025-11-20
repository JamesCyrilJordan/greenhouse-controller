"""Unit tests for the DisplayManager abstraction."""

from hardware_stubs import install_stub_modules

install_stub_modules()

from greenhouse_controller.display import DisplayManager


class OledRecorder:
    def __init__(self, *, fail=False):
        self.fail = fail
        self.draw_calls = 0

    def fill(self, *_):
        self.draw_calls += 1
        if self.fail:
            raise RuntimeError("i2c error")

    def text(self, *_):
        if self.fail:
            raise RuntimeError("text fail")

    def show(self):
        if self.fail:
            raise RuntimeError("show fail")


def test_show_status_draws_and_logs(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "greenhouse_controller.display.log",
        lambda level, message: logs.append((level, message)),
    )
    oled = OledRecorder()
    manager = DisplayManager(oled)

    manager.show_status(72.5, 55.0, True, False)

    assert oled.draw_calls == 1
    assert (
        "info",
        "Temp: 72.5°F | Humidity: 55.0% | Heater: ON | Fan: OFF",
    ) in logs


def test_show_status_falls_back_after_failure(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "greenhouse_controller.display.log",
        lambda level, message: logs.append((level, message)),
    )
    oled = OledRecorder(fail=True)
    manager = DisplayManager(oled)

    manager.show_status(65.0, 40.0, False, True)
    manager.show_status(65.0, 40.0, False, True)

    assert ("error", "Display failure: i2c error") in logs
    assert ("warn", "Display unavailable; status logged to console") in logs
    assert logs[-1] == (
        "info",
        "Temp: 65.0°F | Humidity: 40.0% | Heater: OFF | Fan: ON",
    )


def test_show_message_logs_when_no_display(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "greenhouse_controller.display.log",
        lambda level, message: logs.append((level, message)),
    )
    manager = DisplayManager(None)

    manager.show_message("Line1", "Line2", "Line3")

    assert logs == [("info", "Line1 Line2 Line3")]
