import hmac
import logging
import math
import os
from datetime import UTC, datetime
from pathlib import Path

import joblib
import pandas as pd
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import BadRequest, TooManyRequests

from backend.utils.advice_generator import get_advice

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

FEATURE_RANGES = {
    "moisture": (0, 100),
    "temperature": (-50, 100),
    "ph": (0, 14),
    "ec": (0, 1_000_000),
    "nitrogen": (0, 1_000_000),
    "phosphorus": (0, 1_000_000),
    "potassium": (0, 1_000_000),
}
FEATURE_NAMES = tuple(FEATURE_RANGES)

db = SQLAlchemy()
limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger(__name__)


class SensorReading(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String(120), nullable=True)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        index=True,
        default=lambda: datetime.now(UTC),
    )
    moisture = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    ph = db.Column(db.Float, nullable=False)
    ec = db.Column(db.Float, nullable=False)
    nitrogen = db.Column(db.Float, nullable=False)
    phosphorus = db.Column(db.Float, nullable=False)
    potassium = db.Column(db.Float, nullable=False)

    def to_dict(self):
        timestamp = self.timestamp
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        return {
            "id": self.id,
            "device_id": self.device_id,
            "timestamp": timestamp.isoformat(),
            **{name: getattr(self, name) for name in FEATURE_NAMES},
        }


def validate_features(features):
    if not isinstance(features, dict):
        return None, "Features must be a JSON object."

    cleaned = {}
    for name, (minimum, maximum) in FEATURE_RANGES.items():
        value = features.get(name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None, f"Feature '{name}' must be a number."
        if not math.isfinite(value):
            return None, f"Feature '{name}' must be finite."
        if not minimum <= value <= maximum:
            return None, f"Feature '{name}' must be between {minimum} and {maximum}."
        cleaned[name] = float(value)
    return cleaned, None


def _load_models():
    model_dir = PROJECT_ROOT / "ml_training"
    models = {}
    label_encoders = {}
    for crop in ("tomato", "potato", "onion"):
        models[crop] = joblib.load(model_dir / f"rf_{crop}.pkl")
        label_encoders[crop] = joblib.load(model_dir / f"le_{crop}.pkl")
    return models, label_encoders


def _database_url():
    database_url = os.getenv("DATABASE_URL", "sqlite:///farm.db")
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql://", 1)
    return database_url


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_URI=_database_url(),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SENSOR_INGEST_TOKEN=os.getenv("SENSOR_INGEST_TOKEN"),
        RATELIMIT_DEFAULT="1000 per day, 600 per hour",
        RATELIMIT_STORAGE_URI=os.getenv("RATELIMIT_STORAGE_URI", "memory://"),
        CORS_ORIGINS=os.getenv("CORS_ORIGINS", ""),
    )
    if test_config:
        app.config.update(test_config)
    if os.getenv("APP_ENV") == "production" and not app.config[
        "SQLALCHEMY_DATABASE_URI"
    ].startswith("postgresql"):
        raise RuntimeError("Production requires a PostgreSQL DATABASE_URL.")
    if os.getenv("APP_ENV") == "production" and not app.config.get(
        "SENSOR_INGEST_TOKEN"
    ):
        raise RuntimeError("Production requires a SENSOR_INGEST_TOKEN.")

    if "MODELS" in app.config and "LABEL_ENCODERS" in app.config:
        models = app.config["MODELS"]
        label_encoders = app.config["LABEL_ENCODERS"]
    else:
        models, label_encoders = _load_models()

    app.extensions["models"] = models
    app.extensions["label_encoders"] = label_encoders
    db.init_app(app)
    limiter.init_app(app)

    origins = [
        origin.strip()
        for origin in app.config["CORS_ORIGINS"].split(",")
        if origin.strip()
    ]
    if origins:
        CORS(app, origins=origins)

    with app.app_context():
        db.create_all()

    @app.get("/health")
    @limiter.exempt
    def health():
        return jsonify({"status": "ok"})

    @app.get("/api/sensor-readings/latest")
    def latest_sensor_reading():
        reading = db.session.execute(
            select(SensorReading).order_by(SensorReading.timestamp.desc()).limit(1)
        ).scalar_one_or_none()
        return jsonify({"reading": reading.to_dict() if reading else None})

    @app.get("/api/sensor-readings")
    def sensor_readings():
        try:
            limit = int(request.args.get("limit", 24))
        except ValueError:
            return jsonify({"error": "Limit must be an integer."}), 400
        if not 1 <= limit <= 100:
            return jsonify({"error": "Limit must be between 1 and 100."}), 400

        readings = db.session.execute(
            select(SensorReading)
            .order_by(SensorReading.timestamp.desc())
            .limit(limit)
        ).scalars()
        return jsonify({"readings": [reading.to_dict() for reading in readings]})

    @app.post("/api/sensor-readings")
    @limiter.limit("30 per minute")
    def create_sensor_reading():
        expected_token = app.config.get("SENSOR_INGEST_TOKEN")
        if not expected_token:
            return jsonify({"error": "Sensor ingestion is not configured."}), 503
        supplied_token = request.headers.get("Authorization", "")
        supplied_token = supplied_token.removeprefix("Bearer ").strip()
        if not hmac.compare_digest(supplied_token, expected_token):
            return jsonify({"error": "Unauthorized sensor."}), 401

        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json."}), 400
        payload = request.get_json()
        if not isinstance(payload, dict):
            return jsonify({"error": "Request body must be a JSON object."}), 400
        features, error = validate_features(payload)
        if error:
            return jsonify({"error": error}), 400

        timestamp = datetime.now(UTC)
        if "timestamp" in payload:
            try:
                timestamp = datetime.fromisoformat(str(payload["timestamp"]))
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=UTC)
            except ValueError:
                return jsonify({"error": "Timestamp must be an ISO 8601 date."}), 400

        reading = SensorReading(
            device_id=str(payload.get("device_id", ""))[:120] or None,
            timestamp=timestamp,
            **features,
        )
        db.session.add(reading)
        db.session.commit()
        return jsonify({"reading": reading.to_dict()}), 201

    @app.post("/predict")
    @limiter.limit("30 per minute")
    def predict():
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json."}), 400
        payload = request.get_json()
        if not isinstance(payload, dict):
            return jsonify({"error": "Request body must be a JSON object."}), 400
        crop = payload.get("crop")
        if not isinstance(crop, str) or crop not in app.extensions["models"]:
            return jsonify({"error": "Unsupported crop."}), 400
        features, error = validate_features(payload.get("features"))
        if error:
            return jsonify({"error": error}), 400

        try:
            model = app.extensions["models"][crop]
            encoder = app.extensions["label_encoders"][crop]
            frame = pd.DataFrame([features], columns=FEATURE_NAMES)
            predicted_class = model.predict(frame)[0]
            disease_name = str(
                encoder.inverse_transform([predicted_class])[0]
            ).replace("_", " ").strip().title()
            confidence = float(max(model.predict_proba(frame)[0]))
            advice = get_advice(crop, features, disease_name)
        except (AttributeError, IndexError, KeyError, TypeError, ValueError):
            logger.exception("Prediction failed for crop %s", crop)
            return jsonify({"error": "Prediction could not be generated."}), 500

        return jsonify(
            {
                "predicted_disease": disease_name,
                "confidence": confidence,
                **advice,
            }
        )

    @app.get("/api/github")
    @limiter.limit("10 per minute")
    def github_proxy():
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return jsonify({"error": "GitHub token is not configured."}), 503
        try:
            response = requests.get(
                "https://api.github.com/repos/Leeli14/Soil",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5,
            )
            response.raise_for_status()
            return jsonify(response.json()), response.status_code
        except requests.RequestException:
            logger.exception("GitHub API request failed")
            return jsonify({"error": "GitHub API request failed."}), 502

    @app.errorhandler(BadRequest)
    def invalid_json(_error):
        return jsonify({"error": "Request body must contain valid JSON."}), 400

    @app.errorhandler(TooManyRequests)
    def rate_limit_exceeded(_error):
        return jsonify({"error": "Too many requests. Please retry later."}), 429

    @app.errorhandler(SQLAlchemyError)
    def database_error(_error):
        db.session.rollback()
        logger.exception("Database request failed")
        return jsonify({"error": "Database request failed."}), 503

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
