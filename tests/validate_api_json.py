"""
Fase 1 - Validacion aislada: fuente JSON desde API publica.

Fuente elegida: Open-Meteo (pronostico del tiempo), API REST simple, sin
key. No necesita relacionarse tematicamente con las demas fuentes (ver
reglas/01-fuentes-formatos.md).

No escribe a ningun lado - solo confirma que la API responde y que el JSON
se puede aplanar a una estructura tabular en memoria.

Mapeo a Postgres (ver reglas/02-infra-lakebase-terraform.md): tabla
relacional simple, sin extension especial.
"""

import sys

import requests

API_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=-34.6&longitude=-58.4"
    "&current=temperature_2m,wind_speed_10m"
    "&hourly=temperature_2m"
)


def fetch_sample() -> dict:
    response = requests.get(API_URL, timeout=15)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    print(f"[JSON] GET {API_URL}")
    payload = fetch_sample()

    current = payload.get("current", {})
    hourly_times = payload.get("hourly", {}).get("time", [])

    print(f"[JSON] OK - current: {current}")
    print(f"[JSON] OK - {len(hourly_times)} puntos horarios en el forecast")

    if not current:
        print("[JSON] FALLO - la fuente respondio pero sin bloque 'current'")
        sys.exit(1)

    print("[JSON] Mapeo Postgres propuesto: tabla relacional simple "
          "(lat, lon, observed_at timestamptz, temperature_2m numeric, "
          "wind_speed_10m numeric)")
