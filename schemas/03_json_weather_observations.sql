-- Fase 2 - Formato JSON desde API publica.
-- Fuente validada en Fase 1: Open-Meteo (forecast), bloque "current".
-- Tabla relacional simple, sin extension.

CREATE TABLE IF NOT EXISTS json_weather_observations (
    id                BIGSERIAL PRIMARY KEY,
    latitude          NUMERIC(6, 3) NOT NULL,
    longitude         NUMERIC(6, 3) NOT NULL,
    observed_at       TIMESTAMPTZ NOT NULL,
    temperature_2m    NUMERIC(5, 2),
    wind_speed_10m    NUMERIC(5, 2),
    ingested_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (latitude, longitude, observed_at)
);

-- lat/lon quedan como NUMERIC simple (no PostGIS): esta fuente identifica
-- un punto de consulta fijo, no hace consultas espaciales - el geoespacial
-- "real" del proyecto es la fuente OSM/Overpass (04_geospatial_osm_points.sql).
