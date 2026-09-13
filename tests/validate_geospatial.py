"""
Fase 1 - Validacion aislada: fuente geoespacial (OpenStreetMap / Overpass API).

Fuente elegida: Overpass API, consulta de cafes en un bounding box de CABA,
gratis, sin key (ver reglas/01-fuentes-formatos.md - reuso de know-how de
[[rutia]]).

No escribe a ningun lado - solo confirma que la API responde y que se puede
extraer lat/lon en memoria.

Mapeo a Postgres (ver reglas/02-infra-lakebase-terraform.md /
03-conceptos-oltp-postgres.md): tabla con extension PostGIS, columna
`geometry(Point, 4326)` a partir de (lon, lat).
"""

import sys

import requests

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Bounding box aproximado de CABA (Buenos Aires)
QUERY = """
[out:json][timeout:15];
node["amenity"="cafe"](-34.62,-58.40,-34.58,-58.36);
out 10;
"""


def fetch_sample() -> list[dict]:
    # Overpass exige un User-Agent identificable (politica de uso de OSM) -
    # sin esto puede responder 406/429 aunque la query sea valida.
    headers = {"User-Agent": "lakebase-multiformat-databricks/fase1-validation"}
    response = requests.post(
        OVERPASS_URL, data={"data": QUERY}, headers=headers, timeout=20
    )
    response.raise_for_status()
    payload = response.json()

    rows = []
    for element in payload.get("elements", []):
        rows.append(
            {
                "osm_id": element.get("id"),
                "name": element.get("tags", {}).get("name"),
                "lat": element.get("lat"),
                "lon": element.get("lon"),
            }
        )
    return rows


if __name__ == "__main__":
    print(f"[Geo] POST {OVERPASS_URL} (cafes en CABA)")
    rows = fetch_sample()
    print(f"[Geo] OK - {len(rows)} nodos parseados en memoria (sample):")
    for row in rows[:5]:
        print(f"  - {row['name']} @ ({row['lat']}, {row['lon']})")

    if not rows:
        print("[Geo] FALLO - la fuente respondio pero no se encontraron nodos")
        sys.exit(1)

    print("[Geo] Mapeo Postgres propuesto: extension PostGIS, tabla con "
          "columna geometry(Point, 4326) construida desde (lon, lat)")
