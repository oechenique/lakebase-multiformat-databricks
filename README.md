# Ingesta multi-formato a Databricks Lakebase (OLTP)

Cuarto proyecto del portfolio: ingesta de 5-6 formatos de origen distintos
(XML, CSV/Excel/Parquet, JSON de API, geoespacial vía OpenStreetMap, y
texto+embeddings) hacia **Databricks Lakebase**, el motor OLTP (Postgres
gestionado) de Databricks.

Ver `reglas/` para el detalle completo de alcance, infraestructura y plan de
trabajo.

## Estado

En construcción — Fases 0 a 4 cerradas: infra Lakebase viva, esquema
diseñado y aplicado (8 tablas), y las 5 fuentes ingestadas de punta a
punta. Arrancando Fase 5 (branching + sync a Unity Catalog). Ver
`reglas/06-estado-actual.md` para el detalle completo.
