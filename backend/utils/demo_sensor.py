import random
from datetime import UTC, datetime


def generate_demo_reading():
    return {
        "device_id": "demo-field-1",
        "timestamp": datetime.now(UTC).isoformat(),
        "moisture": round(random.uniform(30, 70), 1),
        "temperature": round(random.uniform(18, 32), 1),
        "ph": round(random.uniform(5.5, 7.5), 1),
        "ec": round(random.uniform(200, 800), 1),
        "nitrogen": round(random.uniform(20, 80), 1),
        "phosphorus": round(random.uniform(15, 60), 1),
        "potassium": round(random.uniform(25, 100), 1),
    }
