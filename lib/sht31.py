# sht31.py - MicroPython driver
import time

class SHT31:
    def __init__(self, i2c, addr=0x44):
        self.i2c = i2c
        self.addr = addr

    def _read_data(self):
        self.i2c.writeto(self.addr, b'\x2C\x06')
        time.sleep_ms(15)
        data = self.i2c.readfrom(self.addr, 6)
        return data

    def get_temp_humi(self):
        data = self._read_data()

        # Temperature
        temp_raw = data[0] << 8 | data[1]
        temperature = -45 + (175 * (temp_raw / 65535))

        # Humidity
        hum_raw = data[3] << 8 | data[4]
        humidity = 100 * (hum_raw / 65535)

        return round(temperature, 2), round(humidity, 2)
