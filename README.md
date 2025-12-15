# Greenhouse Environmental Controller

This project provides a MicroPython script that monitors temperature and humidity in a small greenhouse using an SHT31-D sensor. The controller keeps an electric heater within a configurable temperature band and shows live readings on a 128×64 I²C OLED display. When the display is unavailable it gracefully falls back to console logging, making the code usable both on real hardware and during local development.

## Features
- Periodically samples an SHT31-D temperature/humidity sensor with retry logic for transient failures.
- Drives relays connected to both a heater and a ventilation fan to keep the greenhouse within a target temperature range.
- Presents status information on an SSD1306 OLED display (or logs to the console if the display is missing).
- Validates configuration at start-up to avoid misconfigured thresholds.
- Structured logging with timestamps for easier debugging in the field.

## Hardware requirements
- Raspberry Pi Pico or Pico W running MicroPython.
- SHT31-D sensor module connected via I²C using `SENSOR_SCL_PIN`/`SENSOR_SDA_PIN` (defaults `GP1`/`GP0`).
- Relay modules wired to `RELAY_PIN` (default `GP16`) for the heater and `FAN_PIN` (default `GP17`) for the fan. The script assumes active-low relays (setting the pin LOW energises the device).
- Optional 128×64 SSD1306 OLED display connected via I²C (default pins `GP4` for SDA and `GP5` for SCL on I2C bus 1).

Update the pin assignments near the top of `main.py` if your wiring differs. Ensure that the relay is rated for the heater load and that you follow all electrical safety guidelines.

## Deploying on the Pico
1. Flash MicroPython to the Pico using the official instructions from the Raspberry Pi documentation.
2. Copy the following items to the Pico using `mpremote`, `rshell`, Thonny, or your preferred deployment tool:
   - `main.py`
   - The entire `greenhouse_controller/` directory (preserves the heater/fan control logic, display helpers, and sensor utilities)
   - `wifi_manager.py` and `logger.py` if you plan to use Wi-Fi logging; omit them for an offline installation
   - `secrets.py` with your Wi-Fi credentials and device enable/disable settings
3. Configure `secrets.py`:
   - Set your Wi-Fi `SSID` and `PASSWORD`
   - Adjust device enable/disable flags (`ENABLE_SENSOR`, `ENABLE_HEATER`, `ENABLE_FAN`, `ENABLE_DISPLAY`, `ENABLE_WIFI`) as needed
4. If you want the controller to run automatically on boot, store it on the device as `main.py` or invoke `main.main()` from your own boot script.
5. Reset the board; the controller will begin sampling the sensor and toggling the heater as needed.

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

## Branch naming
The primary branch of this repository is `main`, renamed from the legacy `master` name to align with modern Git conventions.

## Configuration reference

### Hardware Pin Configuration

Hardware pin assignments are defined in `greenhouse_controller/hardware.py`:

| Setting | Description | Default |
| ------- | ----------- | ------- |
| `SENSOR_I2C_BUS` | I²C controller number used for the SHT31-D sensor. | `0` |
| `SENSOR_SCL_PIN` / `SENSOR_SDA_PIN` | Pins for the I²C bus used by the SHT31-D sensor. | `1` / `0` |
| `RELAY_PIN` | GPIO pin used to drive the relay controlling the heater. | `16` |
| `FAN_PIN` | GPIO pin used to drive the relay controlling the ventilation fan. | `17` |
| `I2C_BUS` | I²C controller number used for the OLED display. | `0` |
| `I2C_SCL_PIN` / `I2C_SDA_PIN` | Pins for the I²C bus when using the OLED display. | `5` / `4` |
| | **Note:** GPIO 4/5 on Raspberry Pi Pico maps to I2C(0), not I2C(1). | |

### Operational Configuration

All operational configuration values are defined in `secrets.py`:

| Setting | Description | Default |
| ------- | ----------- | ------- |
| `LOW_THRESHOLD` | Temperature in °F at which the heater turns on. | `50.0` |
| `HIGH_THRESHOLD` | Temperature in °F at which the heater turns off. | `55.0` |
| `FAN_THRESHOLD` | Temperature in °F at which the fan turns on (turns off 2°F below this). | `80.0` |
| `POLL_INTERVAL` | Seconds between consecutive sensor reads. | `2` |
| `SENSOR_RETRY_DELAY` | Seconds to wait before retrying after a failed sensor read. | `3` |
| `MAX_SENSOR_ATTEMPTS` | Number of sensor read attempts before the controller reports a fatal error. | `3` |
| `COOLDOWN_INTERVAL` | Seconds between mandatory heater cooldown periods. | `600` (10 min) |
| `COOLDOWN_DURATION` | Seconds the heater must remain off during cooldown. | `60` (1 min) |

### Device Enable/Disable Configuration

Device enable/disable flags are also configured in `secrets.py`:

| Setting | Description | Default |
| ------- | ----------- | ------- |
| `ENABLE_SENSOR` | Enable/disable the SHT31-D temperature/humidity sensor. | `True` |
| `ENABLE_HEATER` | Enable/disable heater relay control. | `True` |
| `ENABLE_FAN` | Enable/disable fan relay control. | `True` |
| `ENABLE_DISPLAY` | Enable/disable OLED display. | `True` |
| `ENABLE_WIFI` | Enable/disable Wi-Fi connectivity. | `True` |

**Note:** The sensor (`ENABLE_SENSOR`) must be enabled for the controller to function. Other devices can be disabled if not needed.

Adjust these configuration values in `secrets.py` to match your greenhouse's needs before deploying the script.

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
