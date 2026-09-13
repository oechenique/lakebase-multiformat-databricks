-- Fase 2 - Formato Excel (.xls).
-- Fuente validada en Fase 1: INDEC, "sh_ipc_aperturas.xls" (apertura del
-- IPC por region y categoria de gasto).
--
-- Diseno normalizado (fecha, region, categoria) en vez de replicar el
-- layout ancho del Excel original (una columna por categoria): el archivo
-- fuente cambia de columnas cuando INDEC agrega/renombra categorias, y un
-- esquema normalizado no se rompe con eso. El aplanado ancho -> largo pasa
-- en el script de ingesta (Fase 4), no en SQL.

CREATE TABLE IF NOT EXISTS tabular_ipc_breakdown (
    id           BIGSERIAL PRIMARY KEY,
    fecha        DATE NOT NULL,
    region       TEXT NOT NULL,
    categoria    TEXT NOT NULL,
    indice       NUMERIC(12, 4),
    ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (fecha, region, categoria)
);
