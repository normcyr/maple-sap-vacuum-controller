import sys, time
import random
import requests as urequests

import config


def send_data_to_influxdb(env_data, start_vacuum_pump):

    timestamp = round(time.time())
    line_protocol_data = "{},sensor_id={} temperature={},humidity={},pressure={},pump_started={} {}".format(
        config.ORGANIZATION,
        config.SENSOR_ID,
        env_data["temperature"],
        env_data["humidity"],
        env_data["pressure"],
        start_vacuum_pump,
        timestamp,
    )
    print(line_protocol_data)

    baseurl = "http://{}:{}".format(config.INFLUXDB_URL, config.INFLUXDB_PORT)
    precision = "s"
    write_url = baseurl + "/api/v2/write?org={}&bucket={}&precision={}".format(
        config.ORGANIZATION, config.BUCKET, precision
    )
    headers = {
        "Authorization": "Token {}".format(config.INFLUXDB_TOKEN),
        "Content-Type": "text/plain; charset=utf-8",
        "Accept": "application/json",
    }

    try:
        req_response = urequests.post(
            write_url, headers=headers, data=line_protocol_data
        )
        print(req_response.status_code)
    except urequests.exceptions.RequestException as e:  # This is the correct syntax
        print(e)
        print(
            "The InfluxDB server does not seem to be running. Cannot write data to InfluxDB."
        )
        pass


if __name__ == "__main__":
    while True:
        env_data = {
            "temperature": random.randint(-20, 30),
            "humidity": random.randint(0, 100),
            "pressure": random.randint(980, 1020),
        }
        start_vacuum_pump = random.choice([True, False])

        send_data_to_influxdb(env_data, start_vacuum_pump)
        time.sleep(1)