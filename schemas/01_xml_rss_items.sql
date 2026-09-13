-- Fase 2 - Formato XML.
-- Fuente validada en Fase 1: feed RSS de BBC News (World).
-- Cada <item> del feed -> una fila. Tabla relacional simple, sin extension.

CREATE TABLE IF NOT EXISTS xml_rss_items (
    id           BIGSERIAL PRIMARY KEY,
    guid         TEXT NOT NULL UNIQUE,
    title        TEXT NOT NULL,
    link         TEXT NOT NULL,
    pub_date     TIMESTAMPTZ,
    ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- guid es el identificador estable que da el feed (evita duplicar el mismo
-- item si se vuelve a correr la ingesta). pub_date llega como string RFC
-- 822 ("Fri, 13 Sep 2026 10:00:00 GMT") - se parsea a timestamptz en el
-- script de ingesta, no en SQL.
