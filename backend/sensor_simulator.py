import argparse
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from backend.utils.demo_sensor import generate_demo_reading

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def main():
    load_dotenv(PROJECT_ROOT / ".env")

    parser = argparse.ArgumentParser(
        description="Send simulated soil readings to the local Soil Advisor API."
    )
    parser.add_argument(
        "--url",
        default=os.getenv("API_BASE_URL", "http://127.0.0.1:5000"),
        help="Base URL of the API (default: http://127.0.0.1:5000)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=20,
        help="Seconds between readings (default: 20)",
    )
    args = parser.parse_args()
    if args.interval <= 0:
        parser.error("--interval must be greater than zero")

    token = os.getenv("SENSOR_INGEST_TOKEN")
    if not token:
        parser.error("Set SENSOR_INGEST_TOKEN in .env before starting the simulator")

    endpoint = f"{args.url.rstrip('/')}/api/sensor-readings"
    print(f"Sending simulated sensor readings to {endpoint}; press Ctrl+C to stop.")
    try:
        while True:
            payload = generate_demo_reading()
            try:
                response = requests.post(
                    endpoint,
                    json=payload,
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=5,
                )
            except requests.RequestException as error:
                print(f"Could not send sensor reading: {error}", file=sys.stderr)
                return 1

            if response.status_code != 201:
                print(
                    f"API rejected sensor reading "
                    f"({response.status_code}): {response.text}",
                    file=sys.stderr,
                )
                return 1

            print(
                f"Sent reading at {payload['timestamp']} "
                f"(moisture {payload['moisture']}%)."
            )
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nSensor simulator stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
