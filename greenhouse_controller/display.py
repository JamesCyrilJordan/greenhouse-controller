"""Display abstraction for the greenhouse controller."""

from .utils import log

__all__ = ["DisplayManager"]


class DisplayManager:
    """Render controller output to an OLED display (with graceful degradation)."""

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
            log("error", "Display failure: {exc}".format(exc=exc))
            log("warn", fallback_message)
            return False

    def show_status(self, temp_f, humidity, heater_on, fan_on):
        heater_label = "ON" if heater_on else "OFF"
        fan_label = "ON" if fan_on else "OFF"
        message = (
            "Temp: {temp:.1f}°F | Humidity: {hum:.1f}% | Heater: {heater} | Fan: {fan}".format(
                temp=temp_f,
                hum=humidity,
                heater=heater_label,
                fan=fan_label,
            )
        )

        if self._failed:
            log("info", message)
            return

        def draw():
            self._oled.fill(0)
            self._oled.text("Greenhouse Monitor", 0, 0)
            self._oled.text("Temp: {:.1f} F".format(temp_f), 0, 20)
            self._oled.text("Hum:  {:.1f} %".format(humidity), 0, 35)
            self._oled.text("Heater: {}".format(heater_label), 0, 50)
            self._oled.text("Fan: {}".format(fan_label), 64, 50)
            self._oled.show()

        if self._safe_call(draw, "Display unavailable; status logged to console"):
            log("info", message)

    def show_message(self, line1, line2="", line3=""):
        if self._failed:
            log(
                "info",
                "{line1} {line2} {line3}".format(
                    line1=line1,
                    line2=line2,
                    line3=line3,
                ).strip(),
            )
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
