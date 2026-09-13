-- Fase 2 - Formato geoespacial (OpenStreetMap / Overpass API).
-- Fuente validada en Fase 1: nodos "amenity=cafe" en CABA.
-- Requiere PostGIS (ver 00_extensions.sql).

CREATE TABLE IF NOT EXISTS geo_osm_points (
    id           BIGSERIAL PRIMARY KEY,
    osm_id       BIGINT NOT NULL UNIQUE,
    name         TEXT,
    amenity      TEXT NOT NULL DEFAULT 'cafe',
    location     GEOGRAPHY(Point, 4326) NOT NULL,
    ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_geo_osm_points_location
    ON geo_osm_points USING GIST (location);

-- Decision geometry vs geography: se elige GEOGRAPHY sobre geometry(Point,
-- 4326) porque las consultas de demo planeadas (Fase 5, "cafes a menos de
-- N metros de un punto") son de distancia real sobre la esfera terrestre.
-- geography calcula ST_DWithin/ST_Distance directo en metros sin tener que
-- reproyectar a un SRID metrico local primero, a costa de ser algo mas
-- lento que geometry en calculos - aceptable a la escala de este proyecto
-- (decenas/cientos de filas, no millones).
