# Soil Advisor

Soil Advisor is a Flutter app that displays field sensor readings and provides
crop-specific soil-borne disease predictions, irrigation guidance, and
fertilization recommendations. The Flutter client communicates with a Flask
API. The API stores sensor readings in PostgreSQL and runs the crop models in
`ml_training/`.

## Architecture

- Flutter app: crop selection, sensor dashboard, recent moisture trend, and
  prediction advice.
- Flask API: sensor ingestion, latest/history endpoints, input validation, and
  model inference.
- PostgreSQL: persistent sensor readings. In local development, SQLite is used
  if `DATABASE_URL` is not set.
- The ESP32 sends readings to the API; it no longer writes directly to a cloud
  database.

## Run locally

### Backend

Use Python 3.12 and PostgreSQL for a production-like local setup. The included
model artifacts were serialized with scikit-learn 1.6.1, so keep that version
when loading or retraining them:

1. Create a database, for example `farm_advisory`.
2. Copy `.env.example` to `.env` and set `DATABASE_URL` and a long,
   unpredictable `SENSOR_INGEST_TOKEN`.
3. Install and start the API:

   ```sh
   python -m venv .venv
   . .venv/bin/activate
   pip install -r backend/requirements.txt
   python -m backend.app
   ```

The API listens on `http://localhost:5000`. For a quick local demo, omit
`DATABASE_URL` to use the ignored `farm.db` SQLite file. The database table is
created on startup; use a migration tool before making production schema
changes.

For a production WSGI server, run `gunicorn --bind 0.0.0.0:$PORT backend.app:app`.

### Flutter

Install Flutter 3.29 or newer, then run:

```sh
flutter pub get
flutter run --dart-define=API_BASE_URL=http://localhost:5000
```

For Android emulators use `http://10.0.2.2:5000`. For a deployed app, set
`API_BASE_URL` to the HTTPS URL of the deployed API at build time:

```sh
flutter build web \
  --dart-define=API_BASE_URL=https://your-api.example.com
```

The backend's `CORS_ORIGINS` setting must contain the exact origin(s) of
browser-based clients, comma-separated. Native mobile clients do not use CORS.

## Sensor API

The ESP32 should send a JSON POST to `/api/sensor-readings` with
`Authorization: Bearer <SENSOR_INGEST_TOKEN>`:

```json
{
  "device_id": "field-1",
  "moisture": 42.5,
  "temperature": 24.0,
  "ph": 6.4,
  "ec": 350,
  "nitrogen": 40,
  "phosphorus": 35,
  "potassium": 50
}
```

An optional ISO 8601 `timestamp` can be included. Read the latest value from
`GET /api/sensor-readings/latest`, recent values from
`GET /api/sensor-readings?limit=24` (maximum 100), and check availability with
`GET /health`. `POST /predict` accepts a crop (`tomato`, `potato`, or `onion`)
and the same seven numeric features.

Inputs currently assume moisture is a percentage, temperature is in Celsius,
and pH is in the 0–14 range. EC and nutrient readings are constrained to
non-negative numeric values up to 1,000,000. Adjust `FEATURE_RANGES` in
`backend/app.py` if your sensors use different units.

## Security and deployment

- Deploy the API on a Python-capable service and pair it with a managed
  PostgreSQL database. Host the built Flutter web files on any static web host;
  these services replace the removed Firebase hosting/database setup.
- Never commit `.env`, database credentials, ingestion tokens, or service
  account keys. Rotate any credentials that have already been committed.
- Configure PostgreSQL, `SENSOR_INGEST_TOKEN`, `CORS_ORIGINS`, and
  `RATELIMIT_STORAGE_URI` through your deployment platform's secret/config
  manager. Use a shared rate-limit backend such as Redis when running multiple
  API instances.
- Sensor ingestion requires its bearer token. Readings and prediction routes
  are rate-limited but currently public; add user authentication/authorization
  before using this for private or multi-farm data.
- Serve the API over HTTPS, restrict network access to PostgreSQL, and back up
  the database regularly.
- The trained model files are trusted Python pickle artifacts. Only deploy
  model files produced and reviewed by this project.

## Tests and checks

```sh
flutter analyze
flutter test
python -m pip install -r backend/requirements.txt
python -m ruff check backend
python -m pytest backend/tests
```

GitHub Actions runs the Flutter and Python checks on pushes and pull requests.
