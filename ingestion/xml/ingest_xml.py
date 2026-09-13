"""
Fase 4 - Ingesta XML: feed RSS de BBC News (World) -> tabla xml_rss_items.
Misma fuente validada en Fase 1 (ver tests/validate_xml.py).

Uso (cargar .env y correr en la misma invocacion de shell):
    set -a && source .env && set +a && .venv/Scripts/python ingestion/xml/ingest_xml.py
"""

import email.utils
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lakebase import get_connection  # noqa: E402

FEED_URL = "https://feeds.bbci.co.uk/news/world/rss.xml"

UPSERT_SQL = """
    INSERT INTO xml_rss_items (guid, title, link, pub_date)
    VALUES (%(guid)s, %(title)s, %(link)s, %(pub_date)s)
    ON CONFLICT (guid) DO UPDATE SET
        title = EXCLUDED.title,
        link = EXCLUDED.link,
        pub_date = EXCLUDED.pub_date
"""


def fetch_items() -> list[dict]:
    response = requests.get(FEED_URL, timeout=15)
    response.raise_for_status()
    root = ET.fromstring(response.content)

    rows = []
    for item in root.findall("./channel/item"):
        guid = (item.findtext("guid") or "").strip()
        if not guid:
            continue  # sin guid no hay forma confiable de deduplicar

        pub_date_raw = (item.findtext("pubDate") or "").strip()
        pub_date = email.utils.parsedate_to_datetime(pub_date_raw) if pub_date_raw else None

        rows.append(
            {
                "guid": guid,
                "title": (item.findtext("title") or "").strip(),
                "link": (item.findtext("link") or "").strip(),
                "pub_date": pub_date,
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
    print(f"[XML] GET {FEED_URL}")
    rows = fetch_items()
    print(f"[XML] {len(rows)} items parseados")

    if not rows:
        print("[XML] FALLO - no se encontraron items")
        sys.exit(1)

    n = load(rows)
    print(f"[XML] OK - {n} filas insertadas/actualizadas en xml_rss_items")
