"""Unit tests for edge/core.py and the Lambda's distance logic (no hardware needed).
Run from the repo root:  python -m pytest tests
"""
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "edge"))
sys.path.insert(0, os.path.join(ROOT, "cloud"))

from core import Cooldown, best_detection, build_message, parse_cgpsinfo  # noqa: E402

# lambda_function creates boto3 clients at import time; stub boto3 for the test
sys.modules.setdefault("boto3", types.SimpleNamespace(resource=lambda *a, **k: None, client=lambda *a, **k: None))
from lambda_function import haversine  # noqa: E402


def test_parse_valid_fix():
    resp = "AT+CGPSINFO\r\n+CGPSINFO: 3218.4800,N,03550.7400,E,050926,101010.0,600.0,0.0,0.0\r\nOK\r\n"
    gps = parse_cgpsinfo(resp)
    assert gps["fix_status"] == "valid"
    assert abs(gps["latitude"] - 32.308) < 1e-3
    assert abs(gps["longitude"] - 35.8457) < 1e-3


def test_parse_southern_western():
    gps = parse_cgpsinfo("+CGPSINFO: 3352.0000,S,15112.0000,W,,,,,")
    assert gps["latitude"] < 0 and gps["longitude"] < 0


def test_parse_no_fix():
    assert parse_cgpsinfo("+CGPSINFO: ,,,,,,,,\r\nOK")["fix_status"] == "invalid"


def test_best_detection_filters_class_and_threshold():
    rows = [
        {"name": "person", "confidence": 0.99},
        {"name": "sheep", "confidence": 0.60},
        {"name": "cow", "confidence": 0.80},
        {"name": "dog", "confidence": 0.90},
    ]
    assert best_detection(rows, 0.75) == ("dog", 0.90)
    assert best_detection(rows[:2], 0.75) is None


def test_message_matches_lambda_fields():
    gps = {"latitude": 32.3, "longitude": 35.9, "fix_status": "valid"}
    msg = build_message("vehicle-1", gps, "event", animal="cow", confidence=0.8123, now=0)
    for key in ("device_id", "latitude", "longitude", "type"):
        assert key in msg
    assert msg["type"] == "event" and msg["animal"] == "cow" and msg["confidence"] == 0.812


def test_cooldown():
    cd = Cooldown(10)
    assert cd.ready(now=0)
    assert not cd.ready(now=5)
    assert cd.ready(now=10)


def test_haversine_1km_radius():
    # ~0.009 degrees of latitude is about 1 km
    assert haversine(32.0, 35.0, 32.0, 35.0) == 0
    assert 0.95 < haversine(32.0, 35.0, 32.009, 35.0) < 1.05
