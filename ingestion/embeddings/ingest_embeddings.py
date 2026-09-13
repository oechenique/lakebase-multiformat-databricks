"""
Fase 4 - Ingesta texto + embeddings: "Pride and Prejudice" (Project
Gutenberg), troceado en chunks, embeddings via OpenRouter
(openai/text-embedding-3-small, dimension confirmada = 1536 en Fase 1)
-> tabla embeddings_text_chunks (pgvector). Misma fuente validada en
Fase 1 (ver tests/validate_embeddings.py).

Requiere OPENROUTER_API_KEY (ver reglas/05-convenciones-repo.md - nunca
hardcodeada).

Uso (cargar .env y correr en la misma invocacion de shell):
    set -a && source .env && set +a && .venv/Scripts/python ingestion/embeddings/ingest_embeddings.py
"""

import os
import sys
import textwrap
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lakebase import get_connection  # noqa: E402

CORPUS_URL = "https://www.gutenberg.org/files/1342/1342-0.txt"
SOURCE_NAME = "gutenberg-1342-pride-and-prejudice"
CHUNK_SIZE_CHARS = 1000
# Suficiente para una demo real de similitud coseno (Fase 5) sin embeddear
# el libro entero (~700 chunks) y disparar tiempo/costo de la API.
MAX_CHUNKS = 30
OPENROUTER_URL = "https://openrouter.ai/api/v1/embeddings"
EMBEDDING_MODEL = "openai/text-embedding-3-small"
EXPECTED_DIM = 1536  # confirmado en Fase 1, ver tests/validate_embeddings.py

UPSERT_SQL = """
    INSERT INTO embeddings_text_chunks (source, chunk_index, content, embedding)
    VALUES (%(source)s, %(chunk_index)s, %(content)s, %(embedding)s::vector)
    ON CONFLICT (source, chunk_index) DO UPDATE SET
        content   = EXCLUDED.content,
        embedding = EXCLUDED.embedding
"""


def fetch_and_chunk() -> list[str]:
    response = requests.get(CORPUS_URL, timeout=20)
    response.raise_for_status()
    text = response.text

    # Recortar boilerplate de Gutenberg (licencia + indice), anclando en la
    # primera linea real del libro - mismo criterio que Fase 1.
    start = text.find("It is a truth universally acknowledged")
    body = text[start:] if start != -1 else text

    chunks = textwrap.wrap(body, CHUNK_SIZE_CHARS)
    return chunks[:MAX_CHUNKS]


def embed(chunk: str, api_key: str) -> list[float]:
    response = requests.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": EMBEDDING_MODEL, "input": chunk},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def to_pgvector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(repr(x) for x in embedding) + "]"


if __name__ == "__main__":
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("[Embeddings] FALLO - OPENROUTER_API_KEY no esta seteada")
        sys.exit(1)

    print(f"[Embeddings] GET {CORPUS_URL}")
    chunks = fetch_and_chunk()
    print(f"[Embeddings] {len(chunks)} chunks a embeddear ({CHUNK_SIZE_CHARS} chars c/u)")

    conn = get_connection()
    conn.autocommit = True
    inserted = 0
    try:
        with conn.cursor() as cur:
            for i, chunk in enumerate(chunks):
                embedding = embed(chunk, api_key)
                if len(embedding) != EXPECTED_DIM:
                    print(
                        f"[Embeddings] FALLO - dimension inesperada "
                        f"({len(embedding)}, se esperaba {EXPECTED_DIM}) en chunk {i}"
                    )
                    sys.exit(1)

                cur.execute(
                    UPSERT_SQL,
                    {
                        "source": SOURCE_NAME,
                        "chunk_index": i,
                        "content": chunk,
                        "embedding": to_pgvector_literal(embedding),
                    },
                )
                inserted += 1
                time.sleep(0.2)  # no golpear la API de OpenRouter sin necesidad
    finally:
        conn.close()

    print(f"[Embeddings] OK - {inserted} filas insertadas/actualizadas en embeddings_text_chunks")
