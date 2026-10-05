"""
Read GPS from the SIM7600 LTE module and publish it to AWS IoT Core over MQTT/TLS.

Transcribed from Figure 4-6 of the project report.
Set ENDPOINT and the certificate paths before running. Never commit the
certificate or private key files (see .gitignore).
"""
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder
import time, json, serial

# ===== AWS IoT Core Settings =====
ENDPOINT = "YOUR-ENDPOINT-ats.iot.YOUR-REGION.amazonaws.com"  # AWS IoT endpoint
CLIENT_ID = "Raspberry-Pi"                                    # Unique client/device identifier
TOPIC = "raspberry/data"                                      # MQTT topic to publish data
CERT_PATH = "./certs/device-certificate.pem.crt"              # Device certificate path
KEY_PATH = "./certs/device-private.pem.key"                   # Device private key path
ROOT_CA = "./certs/AmazonRootCA1.pem"                         # Root CA certificate path

# ===== GPS Settings =====
GPS_PORT = "/dev/ttyUSB3"   # Serial port for SIM7600 GPS
GPS_BAUD = 115200           # Baud rate for GPS communication
SERIAL_TIMEOUT = 0.5        # Serial timeout in seconds (less than 1s)

# 1) Open serial port once for communication with SIM7600
ser = serial.Serial(GPS_PORT, GPS_BAUD, timeout=SERIAL_TIMEOUT)

# 2) Turn on GPS once
ser.write(b"AT+CGPS=1,1\r\n")  # Enable GPS with hot start
time.sleep(3)                   # Initial wait time for GPS fix acquisition (cold start)


def get_gps():
    """Request GPS coordinates quickly without toggling GPS power each time."""
    ser.write(b"AT+CGPSINFO\r\n")  # Request GPS information
    time.sleep(0.3)                 # Reduced wait time from 1s to 0.3s for faster response
    resp = ser.read(ser.in_waiting or 1).decode(errors="ignore")
    for line in resp.splitlines():
        if line.startswith("+CGPSINFO:"):
            parts = line[len("+CGPSINFO:"):].strip().split(",")
            if len(parts) >= 4 and parts[0] and parts[2]:
                # Convert GPS coordinates from ddmm.mmmm format to decimal degrees
                raw_lat = float(parts[0])
                lat = int(raw_lat // 100) + (raw_lat % 100) / 60
                if parts[1] == "S": lat = -lat  # Southern hemisphere correction
                raw_lon = float(parts[2])
                lon = int(raw_lon // 100) + (raw_lon % 100) / 60
                if parts[3] == "W": lon = -lon  # Western hemisphere correction
                return {
                    "latitude": round(lat, 6),
                    "longitude": round(lon, 6),
                    "fix_status": "valid",
                }
    # Return default invalid GPS coordinates if no valid data is found
    return {
        "latitude": 0.0,
        "longitude": 0.0,
        "fix_status": "invalid",
    }


# ===== MQTT Connection Setup =====
event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

# Build a secure MQTT connection using certificates
mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=CERT_PATH,
    pri_key_filepath=KEY_PATH,
    client_bootstrap=client_bootstrap,
    ca_filepath=ROOT_CA,
    client_id=CLIENT_ID,
    clean_session=False,
    keep_alive_secs=30,
)


def main():
    print("Connecting to AWS IoT Core...")
    mqtt_connection.connect().result()  # Establish MQTT connection
    print("Connected!")

    try:
        while True:
            gps = get_gps()  # Fast GPS data retrieval
            # Prepare the message payload
            message = {
                "device": CLIENT_ID,
                "message": "WARNING: Real-time animal detection",
                "location": gps,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            print("Publishing:", message)
            # Publish message to the MQTT topic with QoS 1 (at least once)
            mqtt_connection.publish(TOPIC, json.dumps(message), qos=mqtt.QoS.AT_LEAST_ONCE)
            time.sleep(5)  # Delay between publishes; adjust as needed
    except KeyboardInterrupt:
        print("\nShutting down...")
        mqtt_connection.disconnect().result()  # Disconnect cleanly
        # 3) Turn off GPS when shutting down
        ser.write(b"AT+CGPS=0\r\n")
        ser.close()  # Close serial connection
        print("Done.")


if __name__ == "__main__":
    main()
