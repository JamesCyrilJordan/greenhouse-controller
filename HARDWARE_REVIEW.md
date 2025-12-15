# Greenhouse Controller Hardware Configuration Review

## Overview
This document provides a comprehensive review of all hardware pin configurations, device settings, and enable/disable mechanisms for the greenhouse controller system.

## Pin Configuration Summary

### SHT31-D Temperature/Humidity Sensor
- **I2C Bus:** 0
- **SCL Pin:** GP1 (GPIO 1)
- **SDA Pin:** GP0 (GPIO 0)
- **I2C Addresses:** 0x44, 0x45 (auto-detected)
- **Configuration File:** `greenhouse_controller/hardware.py`
- **Constants:** `SENSOR_I2C_BUS`, `SENSOR_SCL_PIN`, `SENSOR_SDA_PIN`
- **Enable Flag:** `ENABLE_SENSOR` in `secrets.py` (default: `True`)
- **Status:** ✅ Required for operation - controller will fail to start if disabled

### Heater Relay
- **Control Pin:** GP16 (GPIO 16)
- **Configuration File:** `greenhouse_controller/hardware.py`
- **Constant:** `RELAY_PIN`
- **Enable Flag:** `ENABLE_HEATER` in `secrets.py` (default: `True`)
- **Logic:** Active LOW (pin LOW = heater ON, pin HIGH = heater OFF)
- **Initial State:** OFF (pin set to HIGH/1)
- **Status:** ✅ Optional - can be disabled if not needed

### Fan Relay
- **Control Pin:** GP17 (GPIO 17)
- **Configuration File:** `greenhouse_controller/hardware.py`
- **Constant:** `FAN_PIN`
- **Enable Flag:** `ENABLE_FAN` in `secrets.py` (default: `True`)
- **Logic:** Active LOW (pin LOW = fan ON, pin HIGH = fan OFF)
- **Initial State:** OFF (pin set to HIGH/1)
- **Status:** ✅ Optional - can be disabled if not needed

### SSD1306 OLED Display
- **I2C Bus:** 0 (⚠️ **FIXED:** was incorrectly set to 1)
- **SCL Pin:** GP5 (GPIO 5)
- **SDA Pin:** GP4 (GPIO 4)
- **I2C Addresses:** 0x3C, 0x3D (auto-detected)
- **Resolution:** 128×64 pixels
- **Configuration File:** `greenhouse_controller/hardware.py`
- **Constants:** `I2C_BUS`, `I2C_SCL_PIN`, `I2C_SDA_PIN`
- **Enable Flag:** `ENABLE_DISPLAY` in `secrets.py` (default: `True`)
- **Status:** ✅ Optional - gracefully falls back to console logging if disabled or unavailable
- **Note:** GPIO 4/5 on Raspberry Pi Pico maps to I2C(0), not I2C(1). I2C(1) uses GPIO 6/7 or 26/27.

### Wi-Fi (Pico W only)
- **Module:** Built-in Wi-Fi on Raspberry Pi Pico W
- **Configuration File:** `wifi_manager.py`
- **Credentials:** `SSID` and `PASSWORD` in `secrets.py`
- **Enable Flag:** `ENABLE_WIFI` in `secrets.py` (default: `True`)
- **Status:** ✅ Optional - controller works without Wi-Fi

## Pin Conflict Analysis

### I2C Bus Configuration
- **Sensor I2C Bus (0):** Uses GP0 (SDA) and GP1 (SCL)
- **Display I2C Bus (0):** Uses GP4 (SDA) and GP5 (SCL)
- **Status:** ✅ Both devices use I2C(0) but with different GPIO pins. MicroPython allows multiple I2C instances on the same bus with different pin mappings. Both devices can coexist as they have different I2C addresses.

### GPIO Pin Usage
- **GP0:** Sensor SDA (I2C Bus 0)
- **GP1:** Sensor SCL (I2C Bus 0)
- **GP4:** Display SDA (I2C Bus 1)
- **GP5:** Display SCL (I2C Bus 1)
- **GP16:** Heater relay control
- **GP17:** Fan relay control
- **Status:** ✅ No pin conflicts - all pins are unique

## Device Enable/Disable System

### Configuration Location
All enable/disable flags are defined in `secrets.py`:

```python
ENABLE_SENSOR = True      # SHT31-D temperature/humidity sensor
ENABLE_HEATER = True      # Heater relay control
ENABLE_FAN = True         # Fan relay control
ENABLE_DISPLAY = True     # OLED display (SSD1306)
ENABLE_WIFI = True        # Wi-Fi connectivity
```

### Implementation Details

1. **Sensor (`ENABLE_SENSOR`)**
   - If disabled: `initialize_sensor()` returns `None`
   - Controller will raise `RuntimeError` on startup if sensor is disabled
   - **Recommendation:** Always keep enabled (required for operation)

2. **Heater (`ENABLE_HEATER`)**
   - If disabled: `initialize_relay()` returns `None`
   - `control_heater()` safely handles `None` relay
   - Cooldown logic is skipped when heater is disabled
   - **Use case:** Disable during summer months or when testing

3. **Fan (`ENABLE_FAN`)**
   - If disabled: `initialize_fan()` returns `None`
   - `control_fan()` safely handles `None` relay
   - **Use case:** Disable if fan hardware is not installed

4. **Display (`ENABLE_DISPLAY`)**
   - If disabled: `initialize_display()` returns `None`
   - `DisplayManager` gracefully falls back to console logging
   - **Use case:** Disable to save power or when display is not needed

5. **Wi-Fi (`ENABLE_WIFI`)**
   - If disabled: Wi-Fi module is not initialized
   - `wifi_manager` functions return early or `False`
   - **Use case:** Disable for offline operation or to save power

## Configuration Validation

### Temperature Thresholds
- **LOW_THRESHOLD:** 50.0°F (heater turns ON below this)
- **HIGH_THRESHOLD:** 55.0°F (heater turns OFF above this)
- **FAN_THRESHOLD:** 80.0°F (fan turns ON above this, OFF 2°F below)
- **Validation:** `LOW_THRESHOLD` must be < `HIGH_THRESHOLD` (checked at startup)

### Timing Configuration
- **POLL_INTERVAL:** 2 seconds (sensor read frequency)
- **SENSOR_RETRY_DELAY:** 3 seconds (delay before retrying failed reads)
- **MAX_SENSOR_ATTEMPTS:** 3 (max retries before fatal error)
- **COOLDOWN_INTERVAL:** 600 seconds (10 minutes between cooldowns)
- **COOLDOWN_DURATION:** 60 seconds (1 minute heater off time)

## Safety Features

1. **Relay Initialization:** All relays start in OFF state (HIGH/1)
2. **Shutdown Handling:** Relays are turned OFF in `finally` block
3. **Null Checks:** All control functions handle `None` relays gracefully
4. **Sensor Validation:** Sensor readings are validated before use
5. **Cooldown Protection:** Mandatory heater cooldown periods prevent overheating

## Recommendations

### Pin Configuration
- ✅ Current pin assignments are well-organized and conflict-free
- ✅ Separate I2C buses for sensor and display prevent conflicts
- ✅ GPIO pins are clearly separated (sensor: 0-1, display: 4-5, relays: 16-17)

### Enable/Disable System
- ✅ System gracefully handles disabled devices
- ✅ Sensor must remain enabled (enforced at startup)
- ✅ Other devices can be safely disabled as needed

### Potential Improvements
1. Consider adding pin configuration to `secrets.py` for easier customization
2. Add runtime device status reporting
3. Consider adding watchdog timer for sensor failures
4. Add configuration validation for enable flags (e.g., warn if heater disabled but fan enabled)

## Files Modified for Enable/Disable Support

1. **secrets.py** - Added enable/disable flags
2. **wifi_manager.py** - Added `ENABLE_WIFI` check
3. **greenhouse_controller/hardware.py** - Added enable checks for all devices
4. **main.py** - Added graceful handling of disabled devices
5. **README.md** - Updated documentation with enable/disable information

## Testing Recommendations

1. Test with all devices enabled (normal operation)
2. Test with heater disabled (should still read sensor and control fan)
3. Test with fan disabled (should still read sensor and control heater)
4. Test with display disabled (should fall back to console logging)
5. Test with Wi-Fi disabled (should operate offline)
6. Test sensor failure handling (should retry and log errors)
7. Test shutdown sequence (all relays should turn OFF)

