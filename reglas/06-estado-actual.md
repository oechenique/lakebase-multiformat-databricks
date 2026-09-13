# Estado actual — dónde quedamos

## Última actualización: 2026-09-13 (sesión 4)

## Fases 0, 1, 2 y 4 cerradas. Próxima sesión arranca en Fase 5.

- [x] **Fase 0 (setup + infra)** — cerrada y commiteada (`795a848`). Lakebase
      vivo: `databricks_postgres_project` → `_branch` (`production`) →
      `_endpoint` (`primary`).
- [x] **Fase 1 (validación de fuentes)** — cerrada y commiteada (`e72fd4c`).
      Las 5 fuentes candidatas confirmadas en `tests/`.
- [x] **Fase 2 (diseño de esquema)** — cerrada y commiteada (`6baaba1`,
      `48d9ba6`). 8 tablas en `schemas/*.sql`, aplicadas contra el Lakebase
      real con `schemas/apply_schema.py` (OAuth M2M, sin password estática).
- [x] **Fase 3 (infra Terraform)** — quedó resuelta de hecho dentro de la
      Fase 0 de la sesión 3 (mismo Terraform sirvió para levantar
      proyecto/branch/endpoint). No hay un commit separado de "Fase 3" — no
      hacía falta, el plan de trabajo la anticipaba como paso separado pero
      en la práctica se hizo junto con el setup.
- [x] **Fase 4 (ingesta real)** — cerrada y commiteada (`cf9a32d`). Un
      script por formato en `ingestion/`, corridos contra el Lakebase real:

  | Formato | Script | Tabla | Filas |
  |---|---|---|---|
  | XML | `ingestion/xml/ingest_xml.py` | `xml_rss_items` | 23 |
  | JSON API | `ingestion/api_json/ingest_api_json.py` | `json_weather_observations` | 1 |
  | CSV | `ingestion/tabular/ingest_tabular.py` | `tabular_exchange_rate` | 200 |
  | Excel | `ingestion/tabular/ingest_tabular.py` | `tabular_ipc_breakdown` | 30420 |
  | Parquet | `ingestion/tabular/ingest_tabular.py` | `tabular_userdata` | 1000 |
  | Geoespacial | `ingestion/geospatial/ingest_geospatial.py` | `geo_osm_points` | 100 |
  | Texto+embeddings | `ingestion/embeddings/ingest_embeddings.py` | `embeddings_text_chunks` | 30 |

  Todas verificadas con una consulta real post-carga (conteos, `ST_Distance`
  sobre `geography`, similitud coseno `<=>` sobre `vector` con el índice
  HNSW confirmado en `pg_indexes`).

## Cómo se conecta cualquier script a Lakebase (no hay password estática)

`enable_pg_native_login = false` — la conexión es siempre OAuth M2M via el
SDK de Databricks: `WorkspaceClient(...).postgres.generate_database_credential(endpoint=...)`
devuelve un token de 60 minutos que se usa como password de Postgres, con
usuario = `DATABRICKS_CLIENT_ID` (el Service Principal, que ya es dueño del
proyecto y tiene un rol Postgres bootstrapeado automáticamente desde la
creación del proyecto — no hace falta crear el rol a mano). El helper
compartido está en `ingestion/_lakebase.py` (mismo patrón que
`schemas/apply_schema.py`).

Valores de conexión (públicos, no secretos — outputs de
`terraform output` en `terraform/lakebase/`):

```
host:     ep-rapid-smoke-e1kgxkia.database.eastus2.azuredatabricks.net
port:     5432
database: databricks_postgres
endpoint: projects/lakebase-mf-project/branches/production/endpoints/primary
```

Uso estándar de cualquier script (cargar `.env` y correr en la misma
invocación de shell — las env vars no persisten entre invocaciones
separadas):

```bash
set -a && source .env && set +a && .venv/Scripts/python <script>.py
```

## Decisiones de esquema no triviales (Fase 2), por si hace falta revisitarlas

- **`GEOGRAPHY(Point, 4326)`** en vez de `geometry` para OSM: las consultas
  de demo (Fase 5) son de distancia real en metros, y `geography` la
  calcula directo sin reproyectar — el costo extra de performance no
  importa a esta escala.
- **IPC (Excel) normalizado** en `(fecha, region, categoria)`: el archivo
  de INDEC cambia de columnas entre publicaciones, y el aplanado ancho→largo
  vive en el script de ingesta, no en SQL. El parser de
  `ingestion/tabular/ingest_tabular.py::ingest_excel` detecta los 6 bloques
  de región por contenido (no por offsets fijos) y guarda `NULL` cuando
  encuentra el marcador `///` de INDEC (dato no relevado, ej. varios rubros
  durante la cuarentena 2020) — 36 filas con ese caso confirmadas.
- **`VECTOR(1536)` + índice HNSW** (no IVFFlat) para embeddings: no necesita
  re-entrenarse a medida que crece la tabla.

## Qué falta

1. **Fase 5** (`04-plan-de-trabajo.md`): crear una branch de desarrollo
   (copy-on-write), sincronizar al menos una tabla a Unity Catalog, y una
   consulta de ejemplo por extensión (ya tenemos las de verificación de
   Fase 4 como base — similitud vectorial y distancia PostGIS).
2. Nada bloqueado. Toda la infra y el dato real ya están en Lakebase.
