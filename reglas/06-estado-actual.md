# Estado actual — dónde quedamos

## Última actualización: 2026-09-13 (sesión 5)

## Fases 0, 1, 2, 4 y 5 cerradas. Próxima sesión arranca en Fase 6.

- [x] **Fase 5 (branching + Unity Catalog + queries de extensión)** —
      cerrada y commiteada (`eb4486e` + aplicado en sesión 5, sin commit de
      código adicional para el punto 2/3 ya que solo fue infra + queries).
  - **Branch `dev`** (`projects/lakebase-mf-project/branches/dev`, fork
    copy-on-write de `production`, `ttl = "48h"`) + su endpoint
    `primary` (host `ep-dawn-firefly-e15fdr0a.database.eastus2.azuredatabricks.net`).
    Aislamiento demostrado insertando una fila marcada
    (`guid = 'fase5-branch-isolation-test'`) en `xml_rss_items` en `dev`
    (23→24 filas) y confirmando que `production` se mantuvo en 23 filas
    sin la fila marcada.
  - **Catálogo de Unity Catalog** `catalogs/lakebase_mf_catalog`
    (`databricks_postgres_catalog.lakebase_mf` en Terraform), registrando
    la base `databricks_postgres` de la branch `production` vía
    **Lakehouse Federation** — consulta en vivo, no copia de datos. Las 8
    tablas quedan visibles bajo `lakebase_mf_catalog.public.*`.
    Verificado con una consulta analítica real sobre
    `tabular_ipc_breakdown` (promedio de índice IPC por región, último
    mes) corrida vía Databricks SQL Statement Execution API contra el
    "Serverless Starter Warehouse" ya existente en el workspace.
  - **Corrección importante a `reglas/03-conceptos-oltp-postgres.md`**:
    el puente OLTP→OLAP de Lakebase NO es CDC hacia una copia Delta como
    se asumía originalmente — `databricks_postgres_synced_table` de hecho
    sincroniza en la dirección contraria (Unity Catalog Delta → Postgres,
    para servirle datos analíticos ya materializados a una app OLTP). El
    mecanismo real y correcto es `databricks_postgres_catalog`
    (Lakehouse Federation).
  - Query pgvector (mejorada de Fase 4): top-3 vecinos por similitud
    coseno del chunk 5 de `embeddings_text_chunks` (similitudes
    0.7865/0.7238/0.7223).
  - Query PostGIS (mejorada de Fase 4): cafés a menos de 400m del
    Obelisco vía `ST_DWithin`/`ST_Distance` sobre `geo_osm_points` (4
    resultados, 131.8m–236.3m).
  - **Gotchas nuevos de esta fase, por si hace falta re-derivarlos**:
    - Una branch nueva (fork) auto-provisiona su propio endpoint
      `primary` implícito, igual que `production` en Fase 0 — hay que
      adoptarlo con `endpoint_id = "primary"` + `replace_existing = true`
      en vez de crear un endpoint con otro id (error real visto:
      `read_write endpoint already exists`).
    - `databricks_postgres_branch` para una branch que NO es la raíz del
      proyecto requiere expiración explícita en `spec` (`ttl`,
      `expire_time` o `no_expiry`) — la API rechaza la creación sin uno
      de los tres.
    - `databricks_postgres_catalog` requiere el privilegio `CREATE
      CATALOG` sobre el metastore de la cuenta. El Service Principal del
      proyecto (auth OAuth M2M de siempre) **no tiene ningún acceso al
      metastore por default, ni siquiera lectura** — no puede
      auto-otorgarse el permiso por Terraform. Lo resolvió Gastón a mano
      con `GRANT CREATE CATALOG ON METASTORE TO`
      `` `8dc75b14-ab3b-49bc-a4b0-b88868c24d3b`; `` corrido como admin de
      cuenta en un SQL Editor — permiso de cuenta de una sola vez, no
      vale la pena resolverlo por Terraform con un segundo `provider`
      block solo para esto.
    - `terraform apply <planfile>` con un plan guardado (`-out=...`)
      queda "stale" apenas se corre cualquier otro `plan`/`refresh` de
      por medio (bump del serial del state) — más simple correr
      `terraform apply` directo (sin plan file) cuando plan y apply van a
      pasar en pasos separados de todos modos.

- [x] **Fase 0 (setup + infra)** — cerrada y commiteada (`795a848`). Lakebase
      vivo: `databricks_postgres_project` → `_branch` (`production`) →
      `_endpoint` (`primary`).
- [x] **Fase 1 (validación de fuentes)** — cerrada y commiteada (`e72fd4c`).
      Las 5 fuentes candidatas confirmadas en `tests/`.
- [x] **Fase 2 (diseño de esquema)** — cerrada y commiteada (`6baaba1`,
      `48d9ba6`). 7 tablas (8 archivos SQL contando `00_extensions.sql`)
      en `schemas/*.sql`, aplicadas contra el Lakebase real con
      `schemas/apply_schema.py` (OAuth M2M, sin password estática).
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

1. **Fase 6** (`04-plan-de-trabajo.md`): grabar evidencia de las 5
   ingestas + las features de Fase 5 (aislamiento de branch, catálogo UC,
   ambas queries), y después `terraform destroy` en el orden correcto.
   **Ojo**: la branch `dev` está protegida contra recreación accidental
   por Terraform gracias al `ttl = "48h"` (expira sola), pero el destroy
   normal de Terraform la borra igual sin esperar el TTL - no hace falta
   ningún paso especial para ella en el destroy, a diferencia de la
   branch `production` en la guía oficial (que usa `is_protected = true`,
   algo que este proyecto nunca activó).
2. Nada bloqueado. Toda la infra, el dato real, la branch dev y el
   catálogo UC ya están en Lakebase.
