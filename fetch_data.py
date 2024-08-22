import json
import logging
import sqlite3
import time

import paho.mqtt.client as mqtt
import pandas as pd

from utils import print_value, running_on_raspberry_pi, TABLE_NAME, DATABASE_FILE

logging.basicConfig(level=logging.INFO, format="%(asctime)s:%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

MQTT_BROKER = "localhost" if running_on_raspberry_pi() else "192.168.0.183"
MQTT_PORT = 1883
MQTT_TOPIC = "home/energy_monitor"

cost_per_kWh = 0.30


def create_table():
    create_table_cmd = f"""
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
"""
    create_index_cmd = f"CREATE INDEX IF NOT EXISTS idx_timestamp ON {TABLE_NAME} (timestamp);"

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute(create_table_cmd)
    logger.info(f"Executed {create_table_cmd}")
    cursor.execute(create_index_cmd)
    print(f"Executed {create_index_cmd}")

    conn.commit()
    conn.close()


def on_connect(client, userdata, flags, reason_code, properties):
    logger.info(f"MQTT connected with {reason_code=}")
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
            logger.info(f"Failed to write to database: {e}")
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.info(f"Failed to decode JSON message: {e}\n{msg.payload}")


create_table()

mqtt_data_fetcher = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_data_fetcher.on_connect = on_connect
mqtt_data_fetcher.on_message = on_message
mqtt_data_fetcher.connect(MQTT_BROKER, MQTT_PORT, 60)
mqtt_data_fetcher.loop_forever()
