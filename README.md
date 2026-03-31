# Air Pollution Monitor API

FastAPI + PostgreSQL service that polls:

- local indoor GAIA device
- WAQI outdoor API

every 300 seconds, stores normalized data in PostgreSQL using UTC timestamps, and exposes an OpenAPI interface for an air pollution dashboard.

## Features

- Indoor current and history endpoints
- Outdoor current and history endpoints
- Latest forecast endpoint based on the latest WAQI message
- Docker Compose deployment with 2 services: `postgres` and `app`
- Pytest unit and API tests
- FastAPI lifespan startup, not deprecated `@app.on_event("startup")`

## API endpoints

- `GET /api/v1/health`
- `GET /api/v1/indoor/current`
- `GET /api/v1/indoor/history?days=7`
- `GET /api/v1/outdoor/current`
- `GET /api/v1/outdoor/history?days=7`
- `GET /api/v1/outdoor/forecast/current`
- `GET /docs`
- `GET /openapi.json`
- `GET /redoc`

## Run with Docker Compose

```bash
cp .env.example .env
# edit WAQI_TOKEN in .env
docker compose up --build
```

Open:

- Swagger UI: http://localhost:8000/docs
- OpenAPI JSON: http://localhost:8000/openapi.json
- ReDoc: http://localhost:8000/redoc

## Run tests locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

pytest
```

## Notes

- Timestamps are stored and returned in UTC.
- Local GAIA payloads do not include a source timestamp, so `recorded_at_utc` is the UTC fetch time.
- WAQI source timestamps are converted to UTC and exposed as `source_time_utc`.
- Forecast data is parsed into child rows and returned from the most recent outdoor message.

## Known gap for production hardening

This package uses `Base.metadata.create_all()` at startup for simplicity. For a production rollout, I recommend adding Alembic migrations as the next step.
