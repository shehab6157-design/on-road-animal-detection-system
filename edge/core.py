"""
Hardware-free helpers for the integrated pipeline (edge/main.py).
Kept separate so they can be unit-tested without a camera, GPS or AWS.
"""
import time

TARGET_CLASSES = ("sheep", "cow", "horse", "dog")


def parse_cgpsinfo(resp):
    """Parse a SIM7600 AT+CGPSINFO response into decimal degrees.

    Same conversion as cloud/gps_publisher.py (ddmm.mmmm -> degrees).
    Returns a dict with latitude, longitude and fix_status.
    """
    for line in resp.splitlines():
        if line.startswith("+CGPSINFO:"):
            parts = line[len("+CGPSINFO:"):].strip().split(",")
            if len(parts) >= 4 and parts[0] and parts[2]:
                raw_lat = float(parts[0])
                lat = int(raw_lat // 100) + (raw_lat % 100) / 60
                if parts[1] == "S":
                    lat = -lat
                raw_lon = float(parts[2])
                lon = int(raw_lon // 100) + (raw_lon % 100) / 60
                if parts[3] == "W":
                    lon = -lon
                return {"latitude": round(lat, 6), "longitude": round(lon, 6), "fix_status": "valid"}
    return {"latitude": 0.0, "longitude": 0.0, "fix_status": "invalid"}


def best_detection(rows, threshold, targets=TARGET_CLASSES):
    """Return (name, confidence) of the most confident target animal, or None.

    rows: iterable of dicts with 'name' and 'confidence' (one per YOLOv5 box).
    """
    best = None
    for r in rows:
        if r["name"] in targets and r["confidence"] >= threshold:
            if best is None or r["confidence"] > best[1]:
                best = (r["name"], float(r["confidence"]))
    return best


def build_message(device_id, gps, msg_type="location", animal=None, confidence=None, now=None):
    """Build the MQTT payload in the format cloud/lambda_function.py expects:
    top-level device_id, latitude, longitude and type ("event" or "location")."""
    msg = {
        "device_id": device_id,
        "latitude": gps["latitude"],
        "longitude": gps["longitude"],
        "type": msg_type,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
    }
    if animal is not None:
        msg["animal"] = animal
        msg["confidence"] = round(confidence, 3)
    return msg


class Cooldown:
    """Allow an action at most once every `seconds` (avoids sending an alert
    for every frame while the same animal stays in view)."""

    def __init__(self, seconds):
        self.seconds = seconds
        self._last = None

    def ready(self, now=None):
        now = time.monotonic() if now is None else now
        if self._last is None or now - self._last >= self.seconds:
            self._last = now
            return True
        return False
