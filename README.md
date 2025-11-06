# Pico W Greenhouse Monitor (DHT22)

Reads temperature/humidity using a DHT22 on a Raspberry Pi Pico W and serves:
- `/`  → tiny HTML dashboard (auto-refresh)
- `/api` → JSON: `{"temperature_c": ..., "humidity": ..., "timestamp": "..."}`

## Hardware
- Pico W
- DHT22 with 10kΩ pull-up between DATA and 3V3
- DATA → GP15, VCC → 3V3(OUT), GND → GND

## First-time setup
1) Flash MicroPython to Pico W.
2) Copy `src/secrets.py.example` → `src/secrets.py` and fill in your Wi-Fi:
```py
WIFI_SSID = "YourSSID"
WIFI_PASSWORD = "YourPassword"
SENSOR_PIN = 15  # GP15
