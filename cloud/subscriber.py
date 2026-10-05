"""
Subscribe to the raspberry/data topic on AWS IoT Core and print incoming messages.

Transcribed from Figure 4-7 of the project report.
"""
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder
import json
import time

ENDPOINT = "YOUR-ENDPOINT-ats.iot.YOUR-REGION.amazonaws.com"
CLIENT_ID = "Raspberry-Pi"
TOPIC = "raspberry/data"
CERT_PATH = "./certs/device-certificate.pem.crt"
KEY_PATH = "./certs/device-private.pem.key"
ROOT_CA = "./certs/AmazonRootCA1.pem"


def on_message_received(topic, payload, **kwargs):
    print(f"Received message: {json.loads(payload)}")  # Debug line


# Build MQTT connection
mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=CERT_PATH,
    pri_key_filepath=KEY_PATH,
    ca_filepath=ROOT_CA,
    client_id=CLIENT_ID,
    on_message_received=on_message_received,
)

# Connect and subscribe
print("Connecting...")
connect_future = mqtt_connection.connect()
connect_future.result()
print(f"Subscribing to {TOPIC}...")
subscribe_future, _ = mqtt_connection.subscribe(
    topic=TOPIC,
    qos=mqtt.QoS.AT_LEAST_ONCE,
    callback=on_message_received,
)
subscribe_future.result()
print("Waiting for messages...")

# Keep the connection alive
while True:
    time.sleep(1)
