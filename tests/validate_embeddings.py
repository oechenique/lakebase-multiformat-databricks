"""
Fase 1 - Validacion aislada: fuente de texto + embeddings (estilo RAG, no
espacial - eso es PostGIS, esto es pgvector).

Fuente de texto: "Pride and Prejudice" de Project Gutenberg (corpus publico,
sin key). Embeddings: via OpenRouter (mismo proveedor que
[[asesor-turismo-databricks]]), usando la variable de entorno
OPENROUTER_API_KEY - NUNCA hardcodeada (ver reglas/05-convenciones-repo.md).

No escribe a ningun lado - solo confirma que el corpus se puede descargar y
trocear en memoria, y (si hay API key disponible) que se puede pedir un
embedding real de un chunk de muestra.

Mapeo a Postgres (ver reglas/03-conceptos-oltp-postgres.md): extension
pgvector, tabla (chunk_id, content text, embedding vector(N)), indice HNSW
o IVFFlat sobre `embedding` para busqueda por similitud coseno. N (la
dimension) depende del modelo de embeddings elegido - confirmar una vez
seteada la API key.
"""

import os
import sys
import textwrap

import requests

CORPUS_URL = "https://www.gutenberg.org/files/1342/1342-0.txt"
CHUNK_SIZE_CHARS = 1000
OPENROUTER_URL = "https://openrouter.ai/api/v1/embeddings"
EMBEDDING_MODEL = "openai/text-embedding-3-small"


def fetch_and_chunk(limit_chunks: int = 5) -> list[str]:
    response = requests.get(CORPUS_URL, timeout=20)
    response.raise_for_status()
    text = response.text

    # Recortar boilerplate de Gutenberg (licencia + indice) de forma
    # aproximada, anclando en la primera linea real del libro.
    start = text.find("It is a truth universally acknowledged")
    body = text[start:] if start != -1 else text

    chunks = textwrap.wrap(body, CHUNK_SIZE_CHARS)
    return chunks[:limit_chunks]


def try_embed_sample(chunk: str) -> list[float] | None:
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return None

    response = requests.post(
        OPENROUTER_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": EMBEDDING_MODEL, "input": chunk},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


if __name__ == "__main__":
    print(f"[Embeddings] GET {CORPUS_URL}")
    chunks = fetch_and_chunk()
    print(f"[Embeddings] OK - corpus descargado y troceado en memoria "
          f"({len(chunks)} chunks de muestra, ~{CHUNK_SIZE_CHARS} chars c/u)")
    print(f"[Embeddings] Primer chunk (preview): {chunks[0][:120]!r}...")

    if not chunks:
        print("[Embeddings] FALLO - no se generaron chunks del corpus")
        sys.exit(1)

    embedding = try_embed_sample(chunks[0])
    if embedding is None:
        print(
            "[Embeddings] PARCIAL - OPENROUTER_API_KEY no esta seteada, se "
            "valido solo la descarga + chunking del corpus. Falta confirmar "
            "la llamada real a OpenRouter y la dimension del vector "
            "resultante antes de cerrar Fase 1 para este formato."
        )
    else:
        print(f"[Embeddings] OK - embedding real obtenido, dimension = {len(embedding)}")
        print(
            f"[Embeddings] Mapeo Postgres propuesto: extension pgvector, "
            f"columna vector({len(embedding)}), indice HNSW para similitud coseno"
        )
