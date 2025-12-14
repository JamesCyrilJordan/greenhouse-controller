"""Configuration and credentials for the greenhouse controller.

This file contains Wi-Fi credentials, device enable/disable flags, and
operational configuration parameters. Keep this file secure and do not
commit it to version control.
"""

# Wi-Fi Configuration
SSID = "R0x0"
PASSWORD = "MurtTheWolf"

# Device Enable/Disable Flags
# Set to True to enable a device, False to disable it
ENABLE_SENSOR = True      # SHT31-D temperature/humidity sensor
ENABLE_HEATER = True      # Heater relay control
ENABLE_FAN = True         # Fan relay control
ENABLE_DISPLAY = True     # OLED display (SSD1306)
ENABLE_WIFI = True        # Wi-Fi connectivity

# Temperature Control Thresholds (°F)
LOW_THRESHOLD = 50.0      # Temperature at which heater turns ON
HIGH_THRESHOLD = 55.0     # Temperature at which heater turns OFF
FAN_THRESHOLD = 80.0      # Temperature at which fan turns ON (turns OFF 2°F below)

# Timing Configuration
POLL_INTERVAL = 2         # Seconds between sensor measurements
SENSOR_RETRY_DELAY = 3    # Seconds to wait before retrying after sensor error
MAX_SENSOR_ATTEMPTS = 3   # Maximum sensor read attempts before fatal error

# Heater Cooldown Configuration
COOLDOWN_INTERVAL = 600   # Seconds between mandatory heater cooldowns (10 minutes)
COOLDOWN_DURATION = 60    # Seconds the heater must remain off during cooldown (1 minute)
