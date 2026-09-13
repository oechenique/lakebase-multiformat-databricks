-- Fase 2 - Extensiones de Postgres requeridas por este proyecto.
-- Correr una sola vez por branch de Lakebase, antes de crear las tablas
-- de 04_geospatial_osm_points.sql y 05_embeddings_text_chunks.sql.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
