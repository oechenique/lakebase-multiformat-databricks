"""
Fase 1 - Validacion aislada: fuente XML.

Fuente elegida: feed RSS de BBC News (World), XML estandar, sin key.
No escribe a ningun lado - solo confirma que la fuente responde y que se
puede parsear a una estructura en memoria.

Mapeo a Postgres (ver reglas/02-infra-lakebase-terraform.md): tabla
relacional simple, sin extension especial. Cada <item> del feed -> una fila.
"""

import sys
import xml.etree.ElementTree as ET

import requests

FEED_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"


def fetch_sample(limit: int = 5) -> list[dict]:
    response = requests.get(FEED_URL, timeout=15)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    items = root.findall("./channel/item")[:limit]

    rows = []
    for item in items:
        rows.append(
            {
                "title": (item.findtext("title") or "").strip(),
                "link": (item.findtext("link") or "").strip(),
                "pub_date": (item.findtext("pubDate") or "").strip(),
                "guid": (item.findtext("guid") or "").strip(),
            }
        )
    return rows


if __name__ == "__main__":
    print(f"[XML] GET {FEED_URL}")
    rows = fetch_sample()
    print(f"[XML] OK - {len(rows)} items parseados en memoria (sample):")
    for row in rows:
        print(f"  - {row['pub_date']} | {row['title']}")

    if not rows:
        print("[XML] FALLO - la fuente respondio pero no se encontraron items")
        sys.exit(1)

    print("[XML] Mapeo Postgres propuesto: tabla relacional simple "
          "(title text, link text, pub_date timestamptz, guid text unique)")
