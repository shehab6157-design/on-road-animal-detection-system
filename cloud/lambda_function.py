"""
AWS Lambda: store each device's location in DynamoDB and, on a detection event,
alert every other device within 1 km (Haversine distance) over AWS IoT Core.

Transcribed from Figure 4-9 of the project report.
"""
import json
import math
from decimal import Decimal

import boto3

# Initialize AWS resources
dynamodb = boto3.resource("dynamodb")
iot_client = boto3.client("iot-data")

# DynamoDB table name
TABLE_NAME = "DevicesLocation"
# Topic template for alerts
ALERT_TOPIC_TEMPLATE = "raspberry/{}/alert"


def haversine(lat1, lon1, lat2, lon2):
    """
    Calculate the great-circle distance between two points
    on the Earth surface using the Haversine formula.
    """
    R = 6371  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def lambda_handler(event, context):
    # If the event is from an IoT Rule, the payload is the event itself
    payload = event

    # Extract device info
    device_id = payload["device_id"]
    lat = float(payload["latitude"])
    lon = float(payload["longitude"])
    msg_type = payload.get("type", "event")

    # Reference to DynamoDB table
    table = dynamodb.Table(TABLE_NAME)

    # Always update the device's location.
    # Changed from the report: boto3 rejects Python floats for DynamoDB numbers,
    # so they are stored as Decimal.
    table.put_item(Item={
        "device_id": device_id,
        "latitude": Decimal(str(lat)),
        "longitude": Decimal(str(lon)),
    })

    # If this is an event (detection), find nearby devices and alert them
    if msg_type == "event":
        response = table.scan()
        devices = response["Items"]

        for device in devices:
            other_id = device["device_id"]
            if other_id == device_id:
                continue  # Skip the sender

            other_lat = float(device["latitude"])
            other_lon = float(device["longitude"])
            distance = haversine(lat, lon, other_lat, other_lon)

            if distance <= 1:
                topic = ALERT_TOPIC_TEMPLATE.format(other_id)
                message = {
                    "from_device": device_id,
                    "distance_km": distance,
                }
                iot_client.publish(
                    topic=topic,
                    qos=1,
                    payload=json.dumps(message),
                )

    return {"statusCode": 200, "body": "Alerts sent"}
