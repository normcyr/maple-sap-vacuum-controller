"""
Maple Sap Vacuum Controller
Software to control a maple sap vacuum system using an ESP8266 controller
Copyright (C) 2022  Normand Cyr (norm@normandcyr.com)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import sys, time
import dht
import network
import urequests

from machine import Pin, I2C
from ntptime import settime

import BME280
from lcd_api import LcdApi
from i2c_lcd import I2cLcd

import config


def connect_to_wifi():
    ap = network.WLAN(network.AP_IF)  # create access-point interface
    ap.active(False)  # deactivate the interface

    sta_if = network.WLAN(network.STA_IF)

    start = time.ticks_ms()
    timeout = 10000
    while not sta_if.isconnected():
        if time.ticks_diff(time.ticks_ms(), start) > timeout:
            print("Timeout")
            is_connected = False
            break
        print("Connecting to network...")
        sta_if.active(True)
        sta_if.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        while (
            not sta_if.isconnected()
            and time.ticks_diff(time.ticks_ms(), start) < timeout
        ):
            print("Connecting")
            time.sleep_ms(500)
    else:
        print("Connected!")
        print("Network configuration:", sta_if.ifconfig())
        a = sta_if.config("mac")
        print(
            "MAC {:02x}:{:02x}:{:02x}:{:02x}:{:02x}".format(
                a[0], a[1], a[2], a[3], a[4]
            )
        )
        is_connected = True
        settime()

    return is_connected


def get_env_data(dht_sensor, bme_sensor):
    # Measure the environmental data
    # The temperature is calibrated with a factor

    dht_sensor.measure()
    cal_factor = config.TEMP_CALFACTOR
    env_data = {
        "temperature": dht_sensor.temperature() + cal_factor,
        "humidity": dht_sensor.humidity(),
        # "temperature": float(bme_sensor.temperature[:-1]),
        # "humidity": float(bme_sensor.humidity[:-1]),
        "pressure": round(float(bme_sensor.pressure[:-3])),
    }
    print(f"Environmental data measured: {env_data}")

    return env_data


def control_vacuum_pump(start_vacuum_pump):
    # This function will also control the different solenoid valves

    relay = Pin(config.RELAY_PIN, Pin.OUT)

    if start_vacuum_pump:
        relay.value(0)  # use the normally open configuration
    else:
        relay.value(1)  # stops the pump

    print(f"Pump can be started? {start_vacuum_pump}")


def send_data_to_influxdb(env_data, start_vacuum_pump):

    timestamp = (
        round(time.time()) + 946684761
    )  # time difference with the microcontroller
    line_protocol_data = f"{config.ORGANIZATION},sensor_id={config.SENSOR_ID} temperature={env_data['temperature']},humidity={env_data['humidity']},pressure={env_data['pressure']},pump_started={start_vacuum_pump} {timestamp}"
    print(line_protocol_data)

    baseurl = f"http://{config.INFLUXDB_URL}:{config.INFLUXDB_PORT}"
    precision = "s"
    write_url = (
        baseurl
        + f"/api/v2/write?org={config.ORGANIZATION}&bucket={config.BUCKET}&precision={precision}"
    )
    headers = {
        "Authorization": f"Token {config.INFLUXDB_TOKEN}",
        "Content-Type": "text/plain; charset=utf-8",
        "Accept": "application/json",
    }

    try:
        urequests.post(write_url, headers=headers, data=line_protocol_data)
        print("Data written to InfluxDB.")
    except:
        print("Could not connect or write to InfluxDB.")


def display_data(is_connected, env_data, start_vacuum_pump, lcd):
    # Print the environmental data to the LCD display

    lcd.clear()
    lcd.hide_cursor()
    if config.LANGUAGE == "FR":
        if start_vacuum_pump:
            start_vacuum_pump_fr = "oui"
        else:
            start_vacuum_pump_fr = "non"
        if is_connected:
            is_connected_fr = "oui"
        else:
            is_connected_fr = "non"
        lcd.putstr(
            "Temp: {} C\nHumidite: {} %\nPression: {} hPa\nPompe? {} Wifi? {}".format(
                env_data["temperature"],
                env_data["humidity"],
                env_data["pressure"],
                start_vacuum_pump_fr,
                is_connected_fr,
            )
        )
    else:
        lcd.putstr(
            "Temp: {}C\nHumidity: {}%\nPressure: {}hPa\nPump? {} Wifi? {}".format(
                env_data["temperature"],
                env_data["humidity"],
                env_data["pressure"],
                start_vacuum_pump,
                is_connected,
            )
        )


def show_error():
    # The LED from the ESP8266 will flash upon error

    led = Pin(config.LED_PIN, Pin.OUT)
    for i in range(5):
        led.off()
        time.sleep(0.5)
        led.on()
        time.sleep(0.5)
    led.on()


def run(dht_sensor, i2c, bme_sensor, lcd):

    try:
        env_data = get_env_data(dht_sensor, bme_sensor)

        if env_data["temperature"] >= 1:
            start_vacuum_pump = True
        else:
            start_vacuum_pump = False

        control_vacuum_pump(start_vacuum_pump)
        is_connected = connect_to_wifi()
        display_data(is_connected, env_data, start_vacuum_pump, lcd)
        if is_connected:
            send_data_to_influxdb(env_data, start_vacuum_pump)
        else:
            print(
                "Not connected to the wireless network. Cannot write data to InfluxDB at the moment."
            )

    except:
        show_error()


def initialize():
    dht_sensor = dht.DHT22(Pin(config.DHT_PIN))  # D6 on Wemos D1 mini

    i2c = I2C(scl=Pin(config.SCL_PIN), sda=Pin(config.SDA_PIN), freq=10000)

    bme_sensor = BME280.BME280(i2c=i2c, address=int(config.BMP280_ADDRESS))
    lcd = I2cLcd(
        i2c, int(config.LCD_ADDRESS), config.LCD_TOTALROWS, config.LCD_TOTALCOLUMNS
    )

    lcd.clear()
    lcd.hide_cursor()
    if config.LANGUAGE == "FR":
        lcd.putstr("Bienvenue!\nSysteme vacuum Norm\nv0.1.0 2022-12-27 \n")
    else:
        lcd.putstr("Welcome!\nVacuum system Norm\nv0.1.0 2022-12-27 \n")
    time.sleep(5)
    lcd.backlight_off()

    return dht_sensor, i2c, bme_sensor, lcd


dht_sensor, i2c, bme_sensor, lcd = initialize()
while True:
    run(dht_sensor, i2c, bme_sensor, lcd)
    time.sleep(30)