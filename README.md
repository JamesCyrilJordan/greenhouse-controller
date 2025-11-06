# Greenhouse Environmental Controller

This project provides a MicroPython script that monitors temperature and humidity in a small greenhouse using a DHT11 sensor. The controller keeps an electric heater within a configurable temperature band and shows live readings on a 128×64 I²C OLED display. When the display is unavailable it gracefully falls back to console logging, making the code usable both on real hardware and during local development.

## Features
- Periodically samples a DHT11 temperature/humidity sensor with retry logic for transient failures.
- Drives a relay connected to a heater to keep the greenhouse within a target temperature range.
- Presents status information on an SSD1306 OLED display (or logs to the console if the display is missing).
- Validates configuration at start-up to avoid misconfigured thresholds.
- Structured logging with timestamps for easier debugging in the field.

## Hardware requirements
- Raspberry Pi Pico or Pico W running MicroPython.
- DHT11 sensor module connected to the GPIO pin defined in `SENSOR_PIN` (default `GP15`).
- Relay module wired to `RELAY_PIN` (default `GP16`) that controls the heater. The script assumes an active-low relay (setting the pin LOW turns the heater on).
- Optional 128×64 SSD1306 OLED display connected via I²C (default pins `GP0` for SDA and `GP1` for SCL).

Update the pin assignments near the top of `main.py` if your wiring differs. Ensure that the relay is rated for the heater load and that you follow all electrical safety guidelines.

## Deploying on the Pico
1. Flash MicroPython to the Pico using the official instructions from the Raspberry Pi documentation.
2. Copy `main.py` to the Pico using `mpremote`, `rshell`, Thonny, or your preferred deployment tool.
3. If you want the controller to run automatically on boot, store it on the device as `main.py` or invoke `main.main()` from your own boot script.
4. Reset the board; the controller will begin sampling the sensor and toggling the heater as needed.

## Running the script on a computer
The script is primarily intended for MicroPython, but the logic can be exercised on CPython for development as long as the hardware-specific modules are stubbed or mocked. The included unit tests demonstrate how to provide these stubs and can serve as a reference if you want to prototype new behaviour on your computer before deploying to the Pico.

## Testing
Automated tests live under `tests/` and use `pytest`. The tests run against CPython by providing lightweight stubs for the MicroPython modules. To execute the test suite:

```bash
pip install pytest
pytest
```

> **Note:** The repository does not bundle pinned dependencies; installing `pytest` is sufficient to run the suite.

## Project structure
```
main.py     # MicroPython application entry point
README.md   # Project documentation
LICENSE     # License information
```

## Configuration reference
The key configuration values are defined near the top of `main.py`:

| Setting | Description | Default |
| ------- | ----------- | ------- |
| `SENSOR_PIN` | GPIO pin used for the DHT11 data line. | `15` |
| `RELAY_PIN` | GPIO pin used to drive the relay controlling the heater. | `16` |
| `I2C_SCL_PIN` / `I2C_SDA_PIN` | Pins for the I²C bus when using the OLED display. | `1` / `0` |
| `LOW_THRESHOLD` | Temperature in °F at which the heater turns on. | `50.0` |
| `HIGH_THRESHOLD` | Temperature in °F at which the heater turns off. | `55.0` |
| `POLL_INTERVAL` | Seconds between consecutive sensor reads. | `2` |
| `SENSOR_RETRY_DELAY` | Seconds to wait before retrying after a failed sensor read. | `3` |
| `MAX_SENSOR_ATTEMPTS` | Number of sensor read attempts before the controller reports a fatal error. | `3` |

Adjust these constants to match your greenhouse's needs before deploying the script.

## Logging format
Console logs include millisecond timestamps and a level indicator, for example:

```
[ 123456789 ms] INFO  Heater turned ON
```

This format simplifies correlating events with external data sources such as power draw or humidity charts.

## Safety considerations
- Verify that the relay module provides adequate isolation from mains voltage.
- Secure all wiring inside the greenhouse to prevent contact with water or plant material.
- Always test the controller with the heater disconnected to confirm it behaves as expected before putting it into production.
