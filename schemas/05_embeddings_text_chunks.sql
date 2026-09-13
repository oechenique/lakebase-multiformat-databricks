-- Fase 2 - Formato texto + embeddings (RAG style, no espacial).
-- Fuente validada en Fase 1: "Pride and Prejudice" (Project Gutenberg),
-- troceado en chunks, embeddings via OpenRouter con
-- openai/text-embedding-3-small -> dimension real confirmada = 1536.
-- Requiere pgvector (ver 00_extensions.sql).

CREATE TABLE IF NOT EXISTS embeddings_text_chunks (
    id            BIGSERIAL PRIMARY KEY,
    source        TEXT NOT NULL,
    chunk_index   INT NOT NULL,
    content       TEXT NOT NULL,
    embedding     VECTOR(1536) NOT NULL,
    ingested_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (source, chunk_index)
);

-- Indice HNSW (no IVFFlat): HNSW no necesita re-entrenarse a medida que
-- crece la tabla (IVFFlat requiere elegir "lists" en funcion del volumen
-- final y degrada si se llena la tabla despues de crear el indice) - mejor
-- default para un dataset que va a crecer incrementalmente en Fase 4.
-- vector_cosine_ops porque la comparacion de similitud elegida es coseno
-- (ver reglas/01-fuentes-formatos.md).
CREATE INDEX IF NOT EXISTS idx_embeddings_text_chunks_embedding
    ON embeddings_text_chunks USING hnsw (embedding vector_cosine_ops);
