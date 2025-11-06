from machine import Pin, I2C
import dht, time
import ssd1306

# --- CONFIG ---
SENSOR_PIN = 15      # DHT data pin
RELAY_PIN = 16       # Relay signal pin
I2C_SCL_PIN = 1      # OLED clock
I2C_SDA_PIN = 0      # OLED data
LOW_THRESHOLD = 50.0 # °F
HIGH_THRESHOLD = 55.0 # °F

# --- SETUP ---
sensor = dht.DHT11(Pin(SENSOR_PIN))  # or DHT22 if you switch sensors
relay = Pin(RELAY_PIN, Pin.OUT)
relay.value(1)  # assume relay is active LOW (1 = off)

i2c = I2C(0, scl=Pin(I2C_SCL_PIN), sda=Pin(I2C_SDA_PIN))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

heater_on = False

def c_to_f(c):
    return c * 9 / 5 + 32

def update_display(temp_f, hum, heater_on):
    oled.fill(0)
    oled.text("Greenhouse Monitor", 0, 0)
    oled.text(f"Temp: {temp_f:.1f} F", 0, 20)
    oled.text(f"Hum:  {hum:.1f} %", 0, 35)
    oled.text(f"Heater: {'ON' if heater_on else 'OFF'}", 0, 50)
    oled.show()

# --- MAIN LOOP ---
while True:
    try:
        sensor.measure()
        temp_c = sensor.temperature()
        hum = sensor.humidity()
        temp_f = c_to_f(temp_c)

        # Heater control with hysteresis
        if not heater_on and temp_f < LOW_THRESHOLD:
            heater_on = True
            relay.value(0)  # active low relay ON
        elif heater_on and temp_f > HIGH_THRESHOLD:
            heater_on = False
            relay.value(1)  # relay OFF

        # Display and serial output
        print(f"Temp: {temp_f:.1f}°F | Humidity: {hum:.1f}% | Heater: {'ON' if heater_on else 'OFF'}")
        update_display(temp_f, hum, heater_on)

    except OSError as e:
        print("Sensor error:", e)
        oled.fill(0)
        oled.text("Sensor error", 0, 0)
        oled.show()
        time.sleep(3)

    time.sleep(2)

