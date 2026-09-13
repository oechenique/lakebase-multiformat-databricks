"""
Fase 4 - Ingesta JSON: Open-Meteo (forecast, bloque "current") ->
tabla json_weather_observations. Misma fuente validada en Fase 1 (ver
tests/validate_api_json.py).

Uso (cargar .env y correr en la misma invocacion de shell):
    set -a && source .env && set +a && .venv/Scripts/python ingestion/api_json/ingest_api_json.py
"""

import sys
from datetime import timezone
from pathlib import Path

import requests
from dateutil import parser as dateutil_parser

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lakebase import get_connection  # noqa: E402

LATITUDE = -34.6
LONGITUDE = -58.4
API_URL = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LATITUDE}&longitude={LONGITUDE}"
    "&current=temperature_2m,wind_speed_10m&hourly=temperature_2m"
)

UPSERT_SQL = """
    INSERT INTO json_weather_observations
        (latitude, longitude, observed_at, temperature_2m, wind_speed_10m)
    VALUES (%(latitude)s, %(longitude)s, %(observed_at)s, %(temperature_2m)s, %(wind_speed_10m)s)
    ON CONFLICT (latitude, longitude, observed_at) DO UPDATE SET
        temperature_2m = EXCLUDED.temperature_2m,
        wind_speed_10m = EXCLUDED.wind_speed_10m
"""


def fetch_observation() -> dict:
    response = requests.get(API_URL, timeout=15)
    response.raise_for_status()
    payload = response.json()
    current = payload.get("current", {})

    # Open-Meteo devuelve "time" en la zona del parametro `timezone` (GMT
    # por default, que es lo que se uso en la request) - se normaliza a UTC.
    observed_at = dateutil_parser.isoparse(current["time"])
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)

    return {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "observed_at": observed_at,
        "temperature_2m": current.get("temperature_2m"),
        "wind_speed_10m": current.get("wind_speed_10m"),
    }


def load(row: dict) -> None:
    conn = get_connection()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute(UPSERT_SQL, row)
    finally:
        conn.close()


if __name__ == "__main__":
    print(f"[JSON] GET {API_URL}")
    row = fetch_observation()

    if row["temperature_2m"] is None:
        print("[JSON] FALLO - la fuente respondio pero sin bloque 'current' valido")
        sys.exit(1)

    print(f"[JSON] observacion: {row}")
    load(row)
    print("[JSON] OK - 1 fila insertada/actualizada en json_weather_observations")
