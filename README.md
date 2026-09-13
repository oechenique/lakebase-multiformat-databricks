# Lakebase Multiformato — OLTP gobernado en Databricks

Ingesta de 5 formatos de origen sin relación temática entre sí (XML,
CSV/Excel/Parquet, JSON de API, geoespacial vía OpenStreetMap, y
texto+embeddings) hacia **Databricks Lakebase**, el motor OLTP (Postgres
gestionado, Autoscaling) de Databricks — con las tablas resultantes
consultables en vivo desde Unity Catalog vía Lakehouse Federation.

Cuarto proyecto de una serie de portfolio, después de un pipeline batch
([databricks-medallion-terraform](https://github.com/oechenique/databricks-medallion-terraform)),
un agente conversacional ([asesor-turismo-databricks](https://github.com/oechenique/asesor-turismo-databricks))
y un pipeline de streaming en tiempo real
([streaming-satelites-databricks](https://github.com/oechenique/streaming-satelites-databricks)).
Los tres anteriores son OLAP (Delta Lake); este es el primero que trabaja
sobre un motor OLTP. El pitch acá es distinto al del proyecto de turismo:
las 5 fuentes **no necesitan relacionarse entre sí** — el objetivo es
demostrar versatilidad de ingesta hacia un motor relacional gobernado, no
contar una historia de negocio unificada.

## Arquitectura

```
azurerm_databricks_workspace (terraform/workspace/)
  -> databricks_postgres_project        "lakebase-mf-project"
       -> databricks_postgres_branch    "production"  (branch raíz)
            -> databricks_postgres_endpoint  "primary"
       -> databricks_postgres_branch    "dev"  (fork copy-on-write, ttl=48h)
            -> databricks_postgres_endpoint  "primary"  (auto-provisionado al forkear)
       -> databricks_postgres_catalog   "lakebase_mf_catalog"  (Unity Catalog, Lakehouse Federation)
```

| Capa | Recurso Terraform | Qué gestiona |
|---|---|---|
| Workspace | `azurerm_databricks_workspace` | El workspace de Databricks en sí (Azure) |
| Project | `databricks_postgres_project` | Contenedor de más alto nivel de Lakebase |
| Branch | `databricks_postgres_branch` | Ambiente aislado copy-on-write (`production`, `dev`) |
| Endpoint | `databricks_postgres_endpoint` | El punto de conexión Postgres real (host:puerto) sobre una branch |
| Catalog | `databricks_postgres_catalog` | Registro en Unity Catalog — consulta en vivo desde Databricks SQL/notebooks, sin copiar datos |

Extensiones de Postgres habilitadas: **PostGIS** (geoespacial) y
**pgvector** (embeddings) — ver `schemas/00_extensions.sql`.

## Estructura del repo

```
terraform/
  workspace/      infra base de Azure (resource group + workspace)
  lakebase/       project -> branch -> endpoint -> catalog (Lakebase)
schemas/          definición SQL de cada tabla (una por formato) + script de aplicación
ingestion/        un script por formato + orquestador (run_all.py)
tests/            validación aislada de cada fuente (Fase 1, sin Lakebase)
reglas/           documentación viva del proyecto, fase por fase
```

## Setup — correrlo desde cero

### 1. Infra base (Azure + workspace)

```bash
az login
cd terraform/workspace
terraform init
terraform plan -out=tfplan.out
terraform apply "tfplan.out"
terraform output databricks_workspace_url   # usar en el paso 3
```

### 2. Service Principal con OAuth M2M (manual, una sola vez)

Lakebase exige un Service Principal de Databricks con permiso `CAN MANAGE`
sobre el proyecto — `az login` solo no alcanza para estos recursos. Ver
`reglas/02-infra-lakebase-terraform.md` para el detalle, y
**`reglas/08-bitacora-autenticacion-lakebase.md` si tu cuenta de Azure es
personal/MSA** (ver sección de Troubleshooting más abajo).

### 3. `.env` en la raíz del repo (gitignored, nunca se commitea)

```
DATABRICKS_HOST="https://<tu-workspace>.azuredatabricks.net"
DATABRICKS_CLIENT_ID="<application-id-uuid-del-service-principal>"
DATABRICKS_CLIENT_SECRET="<client-secret>"
OPENROUTER_API_KEY="<solo si vas a correr la ingesta de embeddings>"
```

### 4. Infra de Lakebase

```bash
set -a && source .env && set +a
cd terraform/lakebase
terraform init
terraform plan
terraform apply
```

Crea `project` → `branch production` → `endpoint primary`. No hay
password estática de Postgres (`enable_pg_native_login = false`): toda
conexión usa un token OAuth de corta duración vía el SDK de Databricks
(`generate_database_credential`) — ver `ingestion/_lakebase.py`.

### 5. Esquema

```bash
set -a && source .env && set +a
python -m venv .venv && source .venv/Scripts/activate
pip install -r schemas/requirements.txt -r ingestion/requirements.txt
python schemas/apply_schema.py
```

Aplica los 8 archivos de `schemas/*.sql` en orden (extensiones primero,
después las 7 tablas — una por formato).

### 6. Ingesta de las 5 fuentes

```bash
set -a && source .env && set +a
python ingestion/run_all.py
```

Corre los 5 scripts de `ingestion/` en secuencia (XML → JSON → CSV/Excel/Parquet
→ geoespacial → embeddings), con upsert — correrlo de nuevo no duplica
nada. Salida con filas y tiempo por paso + resumen final.

### 7. Branch de desarrollo + catálogo (Fase 5, opcional)

```bash
cd terraform/lakebase
terraform plan    # agrega branch "dev" (fork de production) + endpoint + catalog
terraform apply
```

El catálogo requiere el privilegio `CREATE CATALOG` sobre el metastore de
la cuenta — no lo tiene el Service Principal por default (ver
Troubleshooting).

## Resultados — las 7 tablas, con datos reales cargados

| Tabla | Formato | Filas | Extensión / tipo destacado |
|---|---|---|---|
| `xml_rss_items` | XML (BBC News RSS) | 23 | relacional simple |
| `json_weather_observations` | JSON API (Open-Meteo) | 1 | relacional simple |
| `tabular_exchange_rate` | CSV (datos.gob.ar) | 200 | relacional simple |
| `tabular_ipc_breakdown` | Excel (INDEC, .xls) | 30.420 | normalizado (fecha, región, categoría) |
| `tabular_userdata` | Parquet (sample DuckDB) | 1.000 | incluye `INET` nativo |
| `geo_osm_points` | Geoespacial (Overpass/OSM) | 100 | PostGIS, `GEOGRAPHY(Point, 4326)` |
| `embeddings_text_chunks` | Texto + embeddings (Gutenberg + OpenRouter) | 30 | pgvector, `VECTOR(1536)` + índice HNSW |

### Decisiones de diseño no triviales

- **`GEOGRAPHY` en vez de `geometry`** para los puntos de OSM: las
  consultas de demo son de distancia real en metros (`ST_DWithin`,
  `ST_Distance`), y `geography` la calcula directo sobre la esfera
  terrestre sin reproyectar — el costo extra de performance no importa a
  esta escala (cientos de filas).
- **IPC de INDEC normalizado** en `(fecha, region, categoria)` en vez de
  replicar el layout ancho del Excel original: el archivo fuente cambia
  de columnas entre publicaciones, y un esquema normalizado no se rompe
  con eso. El parser detecta los 6 bloques de región del `.xls` por
  contenido (no por offsets fijos) y preserva `NULL` donde INDEC marca
  `///` (dato no relevado — ej. varios rubros durante la cuarentena
  2020), en vez de inventar un valor.
- **Índice HNSW (no IVFFlat)** para los embeddings: no necesita
  re-entrenarse a medida que la tabla crece, mejor default para un
  dataset que se ingesta de forma incremental.

## Unity Catalog — el puente OLTP → OLAP

`databricks_postgres_catalog` registra la base de Postgres directamente
como catálogo de Unity Catalog vía **Lakehouse Federation**: las 7 tablas
quedan consultables en vivo desde Databricks SQL/notebooks, sin copiar ni
mover el dato. Ejemplo real corrido contra el catálogo (promedio del
índice IPC por región, último mes cargado):

```sql
select region, count(*) as filas, round(avg(indice), 2) as indice_promedio
from lakebase_mf_catalog.public.tabular_ipc_breakdown
where fecha = (select max(fecha) from lakebase_mf_catalog.public.tabular_ipc_breakdown)
group by region
order by indice_promedio desc
```

## Branching — copy-on-write

La branch `dev` es un fork de `production` (mismo dato al momento de
crearla, `ttl = "48h"` para que expire sola si se olvida destruir a
mano). Aislamiento demostrado insertando una fila marcada en `dev` y
confirmando que nunca aparece en `production` — ver
`reglas/06-estado-actual.md` para el detalle completo de la prueba.

## Queries de ejemplo por extensión

**pgvector — similitud coseno:**

```sql
select chunk_index, left(content, 70),
       round((1 - (embedding <=> (select embedding from embeddings_text_chunks where chunk_index = 5)))::numeric, 4) as similitud
from embeddings_text_chunks
where chunk_index != 5
order by embedding <=> (select embedding from embeddings_text_chunks where chunk_index = 5)
limit 3
```

**PostGIS — distancia real:**

```sql
select name, round(ST_Distance(location, ST_SetSRID(ST_MakePoint(-58.3816, -34.6037), 4326)::geography)::numeric, 1) as distancia_m
from geo_osm_points
where ST_DWithin(location, ST_SetSRID(ST_MakePoint(-58.3816, -34.6037), 4326)::geography, 400)
order by distancia_m
```

## Qué evalúa esto (y por qué está armado así)

| Pregunta típica de entrevista | Dónde está la respuesta |
|---|---|
| ¿Cuándo OLTP y cuándo OLAP? | `reglas/03-conceptos-oltp-postgres.md` — Lakebase (este proyecto) vs. Delta Lake (los 3 anteriores) |
| ¿Cómo modelás datos heterogéneos? | `schemas/*.sql` — una tabla por formato, tipo Postgres específico para cada uno |
| ¿Cómo autenticás sin password estática? | OAuth M2M + `generate_database_credential` — `ingestion/_lakebase.py` |
| ¿Cómo garantizás idempotencia en la ingesta? | `ON CONFLICT ... DO UPDATE` en los 5 scripts de `ingestion/` |
| ¿Cómo conectás OLTP con el lado analítico? | Lakehouse Federation (`databricks_postgres_catalog`), no copia CDC |
| ¿Cómo aislás un ambiente de desarrollo? | Branch copy-on-write (`dev`, fork de `production`) |

## Troubleshooting real — el bloqueo de identidad

Antes de llegar a la infra en sí, hubo un bloqueo real de varias horas:
una cuenta Microsoft personal (MSA) **no puede loguearse** en
`accounts.azuredatabricks.net` (`AADSTS500200`), y sin eso no se puede
crear el Service Principal que Lakebase exige. La solución fue crear un
usuario nativo dentro del mismo tenant Free de Entra ID — pero ese
usuario necesita **cuatro roles distintos, en cuatro lugares distintos**
(Global Administrator en Entra ID, Owner de la suscripción de Azure,
Admin del workspace de Databricks, y Metastore Admin de Unity Catalog),
ninguno de los cuales implica los otros tres. El detalle completo —
los 9 baches reales tal como pasaron, con las pantallas exactas y los
mensajes de error — está en
[`reglas/08-bitacora-autenticacion-lakebase.md`](reglas/08-bitacora-autenticacion-lakebase.md).
Vale la pena leerlo entero si te topás con el mismo bloqueo.

## Capturas

_(reemplazar por las capturas reales antes de publicar)_

- `docs/screenshots/cover.png` — vista general del proyecto Lakebase en el Account Console
- `docs/screenshots/branches.png` — branches `production` y `dev` listadas una al lado de la otra
- `docs/screenshots/unity-catalog.png` — `lakebase_mf_catalog` en Catalog Explorer con las 7 tablas
- `docs/screenshots/postgis-query.png` — resultado de la query de cafés a menos de 400m del Obelisco

## Video

[link] — próximamente.

## Apagar todo

```bash
cd terraform/lakebase
terraform plan -destroy -out=tfdestroy.out
terraform apply "tfdestroy.out"    # orden correcto: endpoint -> branch -> project

cd ../workspace
terraform destroy
```

Lakebase Autoscaling escala cómputo a cero solo, pero el storage sigue
facturando mientras el proyecto exista — no dejar la infra prendida sin
necesidad.
