import math

from backend.app import FEATURE_NAMES, create_app, validate_features
from backend.utils.advice_generator import get_advice


class FakeModel:
    def predict(self, frame):
        assert tuple(frame.columns) == FEATURE_NAMES
        return [0]

    def predict_proba(self, _frame):
        return [[0.8, 0.2]]


class FakeEncoder:
    def inverse_transform(self, _classes):
        return ["Fusarium_Wilt"]


def make_client():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
            "SENSOR_INGEST_TOKEN": "test-token",
            "MODELS": {"tomato": FakeModel()},
            "LABEL_ENCODERS": {"tomato": FakeEncoder()},
            "RATELIMIT_STORAGE_URI": "memory://",
        }
    )
    return app.test_client()


def valid_features():
    return {
        "moisture": 45,
        "temperature": 22,
        "ph": 6.5,
        "ec": 350,
        "nitrogen": 40,
        "phosphorus": 35,
        "potassium": 50,
    }


def test_validate_features_rejects_non_finite_and_out_of_range_values():
    features = valid_features()
    features["temperature"] = math.inf

    cleaned, error = validate_features(features)

    assert cleaned is None
    assert "finite" in error

    features["temperature"] = 22
    features["ph"] = 15
    assert "between" in validate_features(features)[1]


def test_sensor_ingestion_requires_token_and_returns_latest_reading():
    client = make_client()
    payload = {**valid_features(), "device_id": "field-1"}

    unauthorized = client.post("/api/sensor-readings", json=payload)
    assert unauthorized.status_code == 401

    created = client.post(
        "/api/sensor-readings",
        json=payload,
        headers={"Authorization": "Bearer test-token"},
    )
    assert created.status_code == 201

    latest = client.get("/api/sensor-readings/latest").get_json()["reading"]
    assert latest["device_id"] == "field-1"
    assert latest["moisture"] == 45


def test_prediction_includes_confidence_and_advice():
    client = make_client()

    response = client.post(
        "/predict",
        json={"crop": "tomato", "features": valid_features()},
    )

    assert response.status_code == 200
    result = response.get_json()
    assert result["predicted_disease"] == "Fusarium Wilt"
    assert result["confidence"] == 0.8
    assert "Trichoderma" in result["solution"]


def test_prediction_rejects_invalid_sensor_values():
    features = valid_features()
    features["moisture"] = -1

    response = make_client().post(
        "/predict",
        json={"crop": "tomato", "features": features},
    )

    assert response.status_code == 400
    assert "between" in response.get_json()["error"]


def test_advice_is_crop_specific_for_shared_disease_labels():
    features = valid_features()

    potato_advice = get_advice("potato", features, "Pink_Rot")
    onion_advice = get_advice("onion", features, "Pink Rot")

    assert "mefenoxam" in potato_advice["solution"]
    assert "fosetyl-Al" in onion_advice["solution"]
