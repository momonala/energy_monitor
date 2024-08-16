import json
import time
import sqlite3
import pandas as pd
import paho.mqtt.client as mqtt

from utils import print_value, running_on_raspberry_pi

MQTT_BROKER = "localhost" if running_on_raspberry_pi() else "192.168.0.183"
MQTT_PORT = 1883
MQTT_TOPIC = "home/energy_monitor"

cost_per_kWh = 0.30

DATABASE_FILE = "data/energy_data.db"
TABLE_NAME = "energy_measurements"


def create_table():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            timestamp TEXT,
            voltage REAL,
            current REAL,
            power REAL,
            energy REAL,
            frequency REAL,
            pf REAL,
            cost REAL
        )
    """)
    conn.commit()
    conn.close()


def on_connect(client, userdata, flags, reason_code, properties):
    print(f"MQTT connected with {reason_code=}")
    client.subscribe(MQTT_TOPIC)
    time.sleep(1)


def on_message(client, userdata, msg):

    try:
        payload = msg.payload.decode("utf-8")
        data = json.loads(payload)
        data["timestamp"] = pd.Timestamp.now()
        voltage = data.get("voltage", "N/A")
        current = data.get("current", "N/A")
        power = data.get("power", "N/A")
        energy = data.get("energy", "N/A")
        power_factor = data.get("pf", "N/A")
        cost = float(energy) * cost_per_kWh
        data["cost"] = cost

        print(
            f"\r{data['timestamp']}     Voltage: {print_value(voltage)}V     Current: {print_value(current, 3)}A     Power: {print_value(power)}W     Energy: {print_value(energy, 3)}kWh     Power Factor: {print_value(power_factor)}     Cost:  €{print_value(cost, 3)}",
            end="",
        )
        df = pd.DataFrame(data, index=[0])
        try:
            with sqlite3.connect(DATABASE_FILE) as conn:
                df.to_sql(TABLE_NAME, conn, if_exists="append", index=False)
        except sqlite3.Error as e:
            print(f"Failed to write to database: {e}")
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        print(f"Failed to decode JSON message: {e}\n{msg.payload}")


create_table()

mqtt_data_fetcher = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_data_fetcher.on_connect = on_connect
mqtt_data_fetcher.on_message = on_message
mqtt_data_fetcher.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_data_fetcher.loop_forever()
