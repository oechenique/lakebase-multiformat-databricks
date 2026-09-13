"""
Fase 4 - Ingesta geoespacial: Overpass API (OpenStreetMap), cafes en CABA
-> tabla geo_osm_points (PostGIS, GEOGRAPHY(Point, 4326)).
Misma fuente validada en Fase 1 (ver tests/validate_geospatial.py).

Uso (cargar .env y correr en la misma invocacion de shell):
    set -a && source .env && set +a && .venv/Scripts/python ingestion/geospatial/ingest_geospatial.py
"""

import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lakebase import get_connection  # noqa: E402

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Bounding box aproximado de CABA (Buenos Aires). "out 100" - suficiente
# para una demo de consultas de distancia (Fase 5) sin sobrecargar el
# servidor publico de Overpass.
QUERY = """
[out:json][timeout:25];
node["amenity"="cafe"](-34.62,-58.40,-34.58,-58.36);
out 100;
"""

UPSERT_SQL = """
    INSERT INTO geo_osm_points (osm_id, name, amenity, location)
    VALUES (
        %(osm_id)s, %(name)s, %(amenity)s,
        ST_SetSRID(ST_MakePoint(%(lon)s, %(lat)s), 4326)::geography
    )
    ON CONFLICT (osm_id) DO UPDATE SET
        name     = EXCLUDED.name,
        location = EXCLUDED.location
"""


def fetch_cafes() -> list[dict]:
    # Overpass exige un User-Agent identificable (politica de uso de OSM) -
    # sin esto puede responder 406/429 aunque la query sea valida (ver
    # gotcha documentado en Fase 1).
    headers = {"User-Agent": "lakebase-multiformat-databricks/fase4-ingestion"}
    response = requests.post(OVERPASS_URL, data={"data": QUERY}, headers=headers, timeout=30)
    response.raise_for_status()
    payload = response.json()

    rows = []
    for element in payload.get("elements", []):
        lat, lon = element.get("lat"), element.get("lon")
        if lat is None or lon is None:
            continue
        rows.append(
            {
                "osm_id": element["id"],
                "name": element.get("tags", {}).get("name"),
                "amenity": element.get("tags", {}).get("amenity", "cafe"),
                "lat": lat,
                "lon": lon,
            }
        )
    return rows


def load(rows: list[dict]) -> int:
    conn = get_connection()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            for row in rows:
                cur.execute(UPSERT_SQL, row)
        return len(rows)
    finally:
        conn.close()


if __name__ == "__main__":
    print(f"[Geo] POST {OVERPASS_URL} (cafes en CABA)")
    rows = fetch_cafes()
    print(f"[Geo] {len(rows)} nodos parseados")

    if not rows:
        print("[Geo] FALLO - no se encontraron nodos")
        sys.exit(1)

    n = load(rows)
    print(f"[Geo] OK - {n} filas insertadas/actualizadas en geo_osm_points")
