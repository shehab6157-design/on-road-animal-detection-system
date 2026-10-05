# On-Road Real-Time Animal Detection & Alert System

> Top 100 — 12th National Technology Parade, Jordan
> Graduation Project · Jordan University of Science and Technology · 2024–2025

## Overview

A real-time edge-to-cloud road safety system that detects animals on roads and alerts drivers — including nearby vehicles within a 1 km radius — using collaborative cloud networking and edge AI.

## Performance

| Metric | Value |
|---|---|
| Model | YOLOv5s custom fine-tuned |
| Dataset | 10,108 images — Dog, Horse, Cow, Sheep |
| mAP@0.5 | 83% |
| Inference Speed | ~340 ms per frame (about 3 FPS) on Raspberry Pi 5, video test |
| End-to-End Latency | Under 1.2 seconds (design target) |
| Alert Broadcast Radius | 1 km via GPS and Haversine formula |
| Hardware Cost | About $350 per unit |

## Detection Results by Class

| Animal | Precision | Recall | mAP@0.5 |
|---|---|---|---|
| Dog | 0.861 | 0.812 | 0.842 |
| Horse | 0.871 | 0.793 | 0.836 |
| Cow | 0.814 | 0.679 | 0.778 |
| Sheep | 0.759 | 0.651 | 0.753 |

## How It Works

1. Noir camera captures road footage on Raspberry Pi 5
2. YOLOv5 model detects animals at about 340 ms per frame
3. On detection — audio alert plays immediately for the driver
4. GPS coordinates retrieved from SIM7600 LTE module
5. Detection data published over MQTT with TLS encryption to AWS IoT Core
6. AWS Lambda stores each device location in DynamoDB and applies the Haversine formula to find all vehicles within 1 km
7. An alert is published back through AWS IoT Core to each nearby vehicle (`raspberry/<device>/alert`)

```mermaid
flowchart LR
  A[Noir camera<br>Raspberry Pi 5] --> B[YOLOv5s<br>~340 ms per frame]
  B -->|animal detected| C[Audio alert<br>for driver]
  B --> D[GPS fix<br>SIM7600 LTE]
  D -->|MQTT over TLS| E[AWS IoT Core]
  E --> F[Lambda<br>Haversine 1 km]
  F --> G[MQTT alert to<br>nearby vehicles]
```

## Repository structure

```
edge/detect.py            YOLOv5 detection loop on the Raspberry Pi (class + confidence filter)
cloud/gps_publisher.py    Reads GPS from the SIM7600 and publishes to AWS IoT Core over MQTT/TLS
cloud/subscriber.py       Test subscriber for the raspberry/data topic
cloud/lambda_function.py  Lambda: stores device locations in DynamoDB, alerts devices within 1 km
config/data.yaml          YOLOv5 training config (4 classes)
config/wvdial.conf        Cellular dial-up config for the SIM7600
aws/iot-policy.json       Least-privilege IoT policy for the device
aws/iot-rule.sql          IoT rule that forwards messages to Lambda
```

The code is taken from the project report (Chapter 4). Model weights, the dataset and the
AWS certificates are not included.

## How to run

On the Raspberry Pi:

```bash
pip install -r requirements.txt
# put your trained weights at ./best.pt
python edge/detect.py
```

GPS publishing (needs an AWS IoT "Thing" and its X.509 certificates in `./certs/`,
and your endpoint set in the script):

```bash
python cloud/gps_publisher.py
```

In AWS: create the IoT policy from `aws/iot-policy.json`, an IoT rule using `aws/iot-rule.sql`
that triggers `cloud/lambda_function.py`, and a DynamoDB table named `DevicesLocation`.

## Tech Stack

| Layer | Technology |
|---|---|
| Edge AI | YOLOv5s, Python, OpenCV |
| Hardware | Raspberry Pi 5, Noir Camera, SIM7600 LTE |
| Connectivity | MQTT over TLS, 4G LTE |
| Cloud | AWS IoT Core, Lambda, DynamoDB |
| Security | X.509 Certificates, TLS 1.2 |
| Location | GPS NMEA 0183, Haversine Formula |

## Limits and next steps

- **Weakest classes:** sheep (recall 0.651) and cows (recall 0.679) are missed more often than dogs and horses, so a real deployment needs more training images for them.
- **Four classes only:** the model knows dogs, horses, cows and sheep. Other animals are not detected.
- **Prototype, not a product:** the results above come from the graduation project evaluation, not from long-term road trials. Field testing across day, night and weather is the next step.
- **Connectivity:** alerts rely on the 4G LTE link, so coverage gaps on rural roads would delay warnings.
- **Speed:** about 2-3 FPS on the Pi 5 is fine for slow road scenes but below video frame rates. Inference takes over 97% of the time per frame.
- **Integration:** in this version detection and GPS publishing run as separate scripts, and the publisher's message format needs a small mapping to match the Lambda's expected fields (`device_id`, `latitude`, `longitude`).

## Team

- Shehab Shibli
- Osama Mohammad Al-Tawra
- Mohammed Yahia
- Naseem Atieh
- Mahmod Mohamad Al-Smadi
- Supervisor: Dr. Fahed Awad

## Recognition

- Top 100 — 12th National Technology Parade, Jordan
- Grade B+ on both Graduation Project phases

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-FF9900?style=flat-square&logo=amazonaws&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-C51A4A?style=flat-square&logo=raspberrypi&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-660066?style=flat-square)
![YOLOv5](https://img.shields.io/badge/YOLOv5-00FFFF?style=flat-square)
