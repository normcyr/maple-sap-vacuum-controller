import sys, time, json
import random
import requests

import config


def send_data_to_http(env_data, start_vacuum_pump):

    env_data["pump"] = start_vacuum_pump
    env_data_json = json.dumps(env_data)
    headers = {
        "Content-Type": "text/plain; charset=utf-8",
        "Accept": "application/json",
    }
    try:
        req_response = requests.post(
            url=f"{config.HTTP_SERVER_URL}:{config.HTTP_SERVER_PORT}",
            json=env_data_json,
            headers=headers,
        )
        print(env_data_json)
        print("Data written to HTTP server.")
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

        send_data_to_http(env_data, start_vacuum_pump)
        time.sleep(1)