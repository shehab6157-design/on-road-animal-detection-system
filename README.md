# 🔬 On-Road Real-Time Animal Detection & Alert System

> 🏅 Top 100 — 12th National Technology Parade, Israel
> Graduation Project · Jordan University of Science and Technology · 2024–2025

## Overview

A real-time edge-to-cloud road safety system that detects animals on roads and alerts drivers — including nearby vehicles within a 1 km radius — using collaborative cloud networking and edge AI.

## Performance

| Metric | Value |
|---|---|
| Model | YOLOv5s custom fine-tuned |
| Dataset | 10,108 images — Dog, Horse, Cow, Sheep |
| mAP@0.5 | 83% |
| Inference Speed | 280 ms per frame on Raspberry Pi 5 |
| End-to-End Latency | Under 1.2 seconds |
| Alert Broadcast Radius | 1 km via GPS and Haversine formula |
| Hardware Cost | Under $350 per unit |

## Detection Results by Class

| Animal | Precision | Recall | mAP@0.5 |
|---|---|---|---|
| Dog | 0.861 | 0.812 | 0.842 |
| Horse | 0.871 | 0.793 | 0.836 |
| Cow | 0.814 | 0.679 | 0.778 |
| Sheep | 0.759 | 0.651 | 0.753 |

## How It Works

1. Noir camera captures road footage on Raspberry Pi 5
2. YOLOv5 model detects animals in real time at 280ms per frame
3. On detection — audio alert plays immediately for the driver
4. GPS coordinates retrieved from SIM7600 LTE module
5. Detection data published over MQTT with TLS encryption to AWS IoT Core
6. AWS Lambda applies Haversine formula to find all vehicles within 1 km
7. SNS alert sent to all nearby vehicles automatically

## Tech Stack

| Layer | Technology |
|---|---|
| Edge AI | YOLOv5s, Python, OpenCV |
| Hardware | Raspberry Pi 5, Noir Camera, SIM7600 LTE |
| Connectivity | MQTT over TLS, 4G LTE |
| Cloud | AWS IoT Core, Lambda, SNS, DynamoDB |
| Security | X.509 Certificates, TLS 1.2 |
| Location | GPS NMEA 0183, Haversine Formula |

## Team

- Shehab Shibli
- Osama Mohammad Al-Tawra
- Mohammed Yahia
- Naseem Atieh
- Mahmod Mohamad Al-Smadi
- Supervisor: Dr. Fahed Awad

## Recognition

- Top 100 — 12th National Technology Parade, Israel
- Grade B+ on both Graduation Project phases

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-FF9900?style=flat-square&logo=amazonaws&logoColor=white)
![Raspberry Pi](https://img.shields.io/badge/Raspberry_Pi-C51A4A?style=flat-square&logo=raspberrypi&logoColor=white)
![MQTT](https://img.shields.io/badge/MQTT-660066?style=flat-square)
![YOLOv5](https://img.shields.io/badge/YOLOv5-00FFFF?style=flat-square)
