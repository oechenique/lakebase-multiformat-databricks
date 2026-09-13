-- Fase 2 - Formato CSV.
-- Fuente validada en Fase 1: API de series de datos.gob.ar
-- (serie 168.1_T_CAMBIOR_D_0_0_26, tipo de cambio BNA vendedor).
-- Una fila por fecha publicada. Tabla relacional simple, sin extension.

CREATE TABLE IF NOT EXISTS tabular_exchange_rate (
    id                          BIGSERIAL PRIMARY KEY,
    fecha                       DATE NOT NULL UNIQUE,
    tipo_cambio_bna_vendedor    NUMERIC(12, 4) NOT NULL,
    ingested_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);
