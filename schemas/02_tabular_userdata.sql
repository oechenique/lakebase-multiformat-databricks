-- Fase 2 - Formato Parquet.
-- Fuente validada en Fase 1: userdata1.parquet (dataset de muestra publico
-- del repo de DuckDB en GitHub) - columnas fijas y conocidas del dataset.

CREATE TABLE IF NOT EXISTS tabular_userdata (
    id                  BIGINT PRIMARY KEY,
    registration_dttm   TIMESTAMPTZ,
    first_name          TEXT,
    last_name           TEXT,
    email               TEXT,
    gender              TEXT,
    ip_address          INET,
    cc                  TEXT,
    country             TEXT,
    birthdate           TEXT,
    salary              NUMERIC(12, 2),
    title               TEXT,
    comments            TEXT,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- birthdate queda como TEXT: el dataset mezcla formatos de fecha
-- inconsistentes entre filas (no todos parseables a DATE sin normalizar
-- primero). cc (numero de tarjeta) tambien es TEXT a proposito, nunca
-- numeric - se trata como identificador, no como cantidad.
-- ip_address usa el tipo nativo INET de Postgres (valida el formato en
-- el insert, no solo texto plano).
