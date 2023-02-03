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

import sys, time, json, socket
import dht
import network
import urequests as requests

from machine import Pin, I2C
from ntptime import settime

import BME280
import onewire, ds18x20
from lcd_api import LcdApi
from i2c_lcd import I2cLcd

import config


def start_ap(ap):
    ap.active(True)
    ap.config(essid=config.AP_SSID, password=config.AP_PWD)
    print("Access point configured.")
    print(ap.ifconfig())


def connect_to_wifi():

    is_connected = False
    sta = network.WLAN(network.STA_IF)
    
    start = time.ticks_ms()
    timeout = 10000
    while not sta.isconnected():
        if time.ticks_diff(time.ticks_ms(), start) > timeout:
            print("Timeout")
            print("Couldn't connect to the network. Check your parameters.")
            is_connected = False
            break
        print("Connecting to network...")
        sta.active(True)
        sta.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        while (
            not sta.isconnected() and time.ticks_diff(time.ticks_ms(), start) < timeout
        ):
            print("Connecting")
            time.sleep_ms(500)
    else:
        print("Connected!")
        print("Network configuration:", sta.ifconfig())
        a = sta.config("mac")
        print(
            "MAC {:02x}:{:02x}:{:02x}:{:02x}:{:02x}".format(
                a[0], a[1], a[2], a[3], a[4]
            )
        )
        is_connected = True
        settime()

    return is_connected


def get_env_data(i2c):
    # Measure the environmental data
    # The temperature is calibrated with a factor

    timestamp = (
        round(time.time()) + 946684761
    )  # time difference with the microcontroller

    if config.DHT:
        dht_sensor = dht.DHT22(Pin(config.DHT_PIN))
        dht_sensor.measure()
        cal_factor = config.TEMPCAL_FACTOR
        temperature = dht_sensor.temperature() + cal_factor
        humidity = dht_sensor.humidity()
    else:
        temperature = "N/A"
        humidity = "N/A"
    
    # Future feature: using a DS18B20 temperature sensor
    if config.ONEWIRE:
        print("Using OneWire")
        onewire_sensor = ds18x20.DS18X20(onewire.OneWire(config.ONEWIRE_PIN))
        onewire_devices = onewire.scan()
        onewire_sensor.convert_temp()
        time.sleep_ms(750)
        temperature_onewire = onewire_sensor.read_temp(onewire_devices[0])
        print(f"There are {len(onewire_devices)} 1-wire temperature probes")
        print(f"The temperature measured by the first one on the bus is {temperature_onewire}°C")
    else:
        temperature_onewire = "N/A"
    
    if config.BME280:
        bme_sensor = BME280.BME280(i2c=i2c, address=int(config.BME280_ADDRESS))
        pressure = round(float(bme_sensor.pressure[:-3]))
    else:
        pressure = "N/A"
    
    env_data = {
        "temperature": temperature,
        "humidity": humidity,
        "pressure": pressure,
        "timestamp": timestamp,
    }
    print(f"Environmental data measured: {env_data}")

    return env_data


def control_vacuum_pump(env_data):
    # This function will also control the different solenoid valves

    relay = Pin(config.RELAY_PIN, Pin.OUT)

    if env_data["temperature"] >= config.START_TEMP:
        start_vacuum_pump = True
        relay.value(0)  # use the normally open configuration
    elif env_data["temperature"] <= config.STOP_TEMP:
        start_vacuum_pump = False
        relay.value(1)  # stops the pump
    else:
        pass  # keep the last state

    print(f"Can the pump be started? {start_vacuum_pump}")

    return start_vacuum_pump


def send_data_to_http(env_data, start_vacuum_pump):

    env_data["pump"] = start_vacuum_pump
    env_data_json = json.dumps(env_data)
    print(env_data_json)
    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Accept": "application/json",
    }
    try:
        requests.post(
            url=f"{config.HTTP_SERVER_URL}:{config.HTTP_SERVER_PORT}",
            json=env_data_json,
            headers=headers,
        )
        print("Data written to HTTP server.")
    except:
        print("Could not make a POST request")


def send_data_to_influxdb(env_data, start_vacuum_pump):

    line_protocol_data = f"{config.ORGANIZATION},sensor_id={config.SENSOR_ID} temperature={env_data['temperature']},humidity={env_data['humidity']},pressure={env_data['pressure']},pump_started={start_vacuum_pump} {env_data['timestamp']}"
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
        requests.post(write_url, headers=headers, data=line_protocol_data)
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
            "Temp: {} C\nHumidite: {} %\nPression: {} hPa\nPompe? {} WF {}".format(
                env_data["temperature"],
                env_data["humidity"],
                env_data["pressure"],
                start_vacuum_pump_fr,
                is_connected_fr,
            )
        )
    else:
        lcd.putstr(
            "Temp: {}C\nHumidity: {}%\nPressure: {}hPa\nPump? {} WF {}".format(
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


def run(i2c, lcd, is_connected):

    try:
        env_data = get_env_data(i2c)
        start_vacuum_pump = control_vacuum_pump(env_data)

        display_data(is_connected, env_data, start_vacuum_pump, lcd)

        if is_connected:
            if config.SEND_DATA_HTTP:
                send_data_to_http(env_data, start_vacuum_pump)
            if config.SEND_DATA_INFLUXDB:
                send_data_to_influxdb(env_data, start_vacuum_pump)
        else:
            print(
                "Not connected to the wireless network. Not sending data to a server at the moment."
            )

    except:
        show_error()


def initialize():

    i2c = I2C(scl=Pin(config.SCL_PIN), sda=Pin(config.SDA_PIN), freq=10000)
    ap = network.WLAN(network.AP_IF)  # create access-point interface

    if config.ACTIVATE_AP:
        start_ap(ap)
        print(f"Starting the access point at {config.AP_SSID}.")
    else:
        ap.active(False)  # deactivate the interface
        print("Access point deactivated.")

    if config.LCD:
        lcd = I2cLcd(i2c, int(config.LCD_ADDRESS), config.LCD_TOTALROWS, config.LCD_TOTALCOLUMNS)
        lcd.clear()
        lcd.hide_cursor()
    else:
        lcd = ""

    if config.LANGUAGE == "FR":
        lcd.putstr(
            "Bienvenue!\nSysteme vacuum Norm\n{}\n".format(config.CURRENT_VERSION)
        )
    else:
        lcd.putstr("Welcome!\nVacuum system Norm\n{}".format(config.CURRENT_VERSION))

    if config.CONNECT_WIFI:
        is_connected = connect_to_wifi()
    else:
        is_connected = False
    time.sleep(3)
    # lcd.backlight_off()

    return i2c, lcd, is_connected


i2c, lcd, is_connected = initialize()
while True:
    run(i2c, lcd, is_connected)
    print(f"Waiting {config.DELAY_READING} seconds before the next reading.")
    time.sleep(config.DELAY_READING)