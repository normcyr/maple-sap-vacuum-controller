import sys, time
import random
import requests

import config


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
        req_response = requests.post(
            write_url, headers=headers, data=line_protocol_data
        )
        print(req_response.status_code)
        req_response.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("HTTP error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout error:", errt)
    except requests.exceptions.RequestException as err:
        print("Oops... request error:", err)


if __name__ == "__main__":
    while True:
        env_data = {
            "temperature": random.randint(-20, 30),
            "humidity": random.randint(0, 100),
            "pressure": random.randint(980, 1020),
            "timestamp": int(time.time()),
        }
        if env_data["temperature"] >= config.START_TEMP:
            start_vacuum_pump = True
        elif env_data["temperature"] <= config.STOP_TEMP:
            start_vacuum_pump = False
        else:
            pass  # keep the last state

        send_data_to_influxdb(env_data, start_vacuum_pump)
        time.sleep(1)