"""
Integrated pipeline: camera -> YOLOv5 -> driver alert -> GPS -> AWS IoT Core.

Connects the separate scripts from the report into one loop, following the
report's pseudocode (Figure 3-3):
  - run YOLOv5 on each frame
  - if an animal is detected: play an audio alert, read GPS, publish a
    detection "event" to AWS IoT Core, log it locally
  - every few seconds: publish a "location" update so the Lambda knows where
    this vehicle is (needed to find vehicles within 1 km)
  - listen on raspberry/<DEVICE_ID>/alert for warnings from nearby vehicles

Messages use the fields cloud/lambda_function.py expects
(device_id, latitude, longitude, type), so no change to the Lambda is needed.

Run from the repo root on the Raspberry Pi:
    DEVICE_ID=vehicle-1 python edge/main.py
"""
import csv
import json
import os
import shutil
import subprocess
import time

import cv2
import serial
import torch
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder

from core import Cooldown, best_detection, build_message, parse_cgpsinfo

# ===== Settings =====
DEVICE_ID = os.environ.get("DEVICE_ID", "Raspberry-Pi")
ENDPOINT = os.environ.get("IOT_ENDPOINT", "YOUR-ENDPOINT-ats.iot.YOUR-REGION.amazonaws.com")
CERT_PATH = "./certs/device-certificate.pem.crt"
KEY_PATH = "./certs/device-private.pem.key"
ROOT_CA = "./certs/AmazonRootCA1.pem"
DATA_TOPIC = "raspberry/data"                 # matched by aws/iot-rule.sql
ALERT_TOPIC = f"raspberry/{DEVICE_ID}/alert"  # where the Lambda sends nearby warnings

MODEL_PATH = "best.pt"
CONFIDENCE_THRESHOLD = 0.75
EVENT_COOLDOWN_S = 10       # one alert per animal sighting, not one per frame
LOCATION_EVERY_S = 5        # same interval as gps_publisher.py
GPS_PORT, GPS_BAUD = "/dev/ttyUSB3", 115200
ALERT_SOUND = "alert.wav"   # optional; played with aplay if present
LOG_FILE = "detections.csv"


def play_alert():
    """Audio alert for the driver (report: speaker on the Pi)."""
    if os.path.exists(ALERT_SOUND) and shutil.which("aplay"):
        subprocess.Popen(["aplay", "-q", ALERT_SOUND])
    else:
        print("\a*** ANIMAL ALERT ***")


def log_detection(msg):
    """Log each detection locally, as in the report's pseudocode."""
    new = not os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["timestamp", "animal", "confidence", "latitude", "longitude"])
        if new:
            w.writeheader()
        w.writerow({k: msg.get(k) for k in w.fieldnames})


def on_nearby_alert(topic, payload, **kwargs):
    data = json.loads(payload)
    print(f"Warning from {data.get('from_device')} about {data.get('distance_km', 0):.2f} km away")
    play_alert()


def main():
    # GPS (SIM7600) - turn on once, as in gps_publisher.py
    ser = serial.Serial(GPS_PORT, GPS_BAUD, timeout=0.5)
    ser.write(b"AT+CGPS=1,1\r\n")
    time.sleep(3)

    def read_gps():
        ser.write(b"AT+CGPSINFO\r\n")
        time.sleep(0.3)
        return parse_cgpsinfo(ser.read(ser.in_waiting or 1).decode(errors="ignore"))

    # AWS IoT Core over MQTT/TLS with X.509 certificates
    elg = io.EventLoopGroup(1)
    bootstrap = io.ClientBootstrap(elg, io.DefaultHostResolver(elg))
    conn = mqtt_connection_builder.mtls_from_path(
        endpoint=ENDPOINT, cert_filepath=CERT_PATH, pri_key_filepath=KEY_PATH,
        ca_filepath=ROOT_CA, client_bootstrap=bootstrap, client_id=DEVICE_ID,
        clean_session=False, keep_alive_secs=30,
    )
    conn.connect().result()
    sub_future, _ = conn.subscribe(topic=ALERT_TOPIC, qos=mqtt.QoS.AT_LEAST_ONCE, callback=on_nearby_alert)
    sub_future.result()
    print(f"Connected as {DEVICE_ID}, listening on {ALERT_TOPIC}")

    def publish(msg):
        conn.publish(DATA_TOPIC, json.dumps(msg), qos=mqtt.QoS.AT_LEAST_ONCE)

    # Model and camera
    model = torch.hub.load("ultralytics/yolov5", "custom", path=MODEL_PATH)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise SystemExit("Error: Cannot open camera")

    event_cd = Cooldown(EVENT_COOLDOWN_S)
    location_cd = Cooldown(LOCATION_EVERY_S)

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Error: Cannot read frame")
                break

            rows = model(frame).pandas().xyxy[0].to_dict("records")
            hit = best_detection(rows, CONFIDENCE_THRESHOLD)

            if hit and event_cd.ready():
                play_alert()  # driver is warned first, before any network call
                gps = read_gps()
                msg = build_message(DEVICE_ID, gps, "event", animal=hit[0], confidence=hit[1])
                log_detection(msg)
                if gps["fix_status"] == "valid":
                    publish(msg)
                    print("Published event:", msg)
                else:
                    print("No GPS fix - detection logged locally, not sent")
            elif location_cd.ready():
                gps = read_gps()
                if gps["fix_status"] == "valid":
                    publish(build_message(DEVICE_ID, gps, "location"))
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        cap.release()
        conn.disconnect().result()
        ser.write(b"AT+CGPS=0\r\n")
        ser.close()


if __name__ == "__main__":
    main()
