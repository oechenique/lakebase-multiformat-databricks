# Estado actual — dónde quedamos

## Última actualización: 2026-09-11 (sesión 3, cierre del día)

## Fase 0 CERRADA. Lakebase está vivo. Próxima sesión arranca en Fase 2.

- [x] Repo inicializado (`git init`), `.gitignore` completo, estructura de
      carpetas y README mínimo creados. **Todavía sin commitear** — se
      commitea cuando se revise esto con la cabeza descansada (ver nota al
      final sobre el commit pendiente).
- [x] Alertas de budget de Azure confirmadas activas ($50 y $100).
- [x] Entra ID + Service Principal OAuth M2M + workspace definitivo — hecho
      por Gastón a mano.
- [x] **`terraform apply` de `terraform/lakebase/` — APLICADO** (ver abajo,
      excepción puntual de esta sesión: lo corrió Claude Code, no Gastón).

## Excepción a la convención de apply — por qué pasó distinto hoy

Gastón autorizó explícitamente, por única vez y por horario ("cortando por
hoy, cansado"), que Claude Code corriera el `apply` de
`terraform/lakebase/` en vez de pasarle el plan para que lo corra él mismo.
**Esto no cambia la convención general** (ver `feedback_terraform_apply` en
memoria) — sigue siendo la norma que el apply lo corre Gastón en su propia
terminal; hoy fue una autorización puntual y explícita, con condición de
parar sin forzar nada si el plan o el apply mostraban algo raro.

## Lakebase — infra real, aplicada hoy

`terraform/lakebase/` se aplicó con éxito: **4 recursos creados, 0 errores**.

```
databricks_postgres_project.this        -> projects/lakebase-mf-project
databricks_postgres_branch.production   -> projects/lakebase-mf-project/branches/production
databricks_postgres_endpoint.primary    -> projects/lakebase-mf-project/branches/production/endpoints/primary
databricks_permissions.project          -> CAN_MANAGE para el SP (autogestionado, ver main.tf)
```

Output `primary_host` (para armar la connection string en Fase 2/4):
`ep-rapid-smoke-e1kgxkia.database.eastus2.azuredatabricks.net`

Antes de aplicar se corrió `terraform plan` fresco (el plan viejo había
quedado stale) y se verificó a mano que `service_principal_name` en el
`databricks_permissions.project` resolviera a un UUID real del Service
Principal (`8dc75b14-ab3b-49bc-a4b0-b88868c24d3b`) y no a un email humano
— esa había sido la señal de alerta de auth rota en la sesión anterior (ver
`project_lakebase_multiformat` en memoria para el detalle completo del
gotcha de autenticación en Azure, no hace falta repetirlo acá).

**Recordatorio operativo para cualquier comando futuro sobre estos stacks**:
las credenciales viven en el `.env` de la **raíz** del repo (no dentro de
`terraform/lakebase/`), y las env vars nunca persisten entre invocaciones
separadas de PowerShell — hay que cargarlas y correr el comando de
Terraform en la misma invocación siempre.

## Fase 1 — cerrada (sesión anterior), sin cambios hoy

Las 5 fuentes siguen validadas de punta a punta en `tests/` (ver detalle
completo en `project_lakebase_multiformat` en memoria si hace falta
repasar cuáles son). Dato clave para Fase 2: dimensión del embedding =
**1536** (`text-embedding-3-small`) → columna `pgvector` será
`vector(1536)` con índice HNSW.

## Qué falta — todo lo de infra está resuelto, sigue el trabajo de datos

1. **Revisar y commitear Fase 0** cuando Gastón tenga la cabeza descansada
   (ver `05-convenciones-repo.md` — un commit por fase completa). El repo
   entero sigue sin ningún commit todavía; vale la pena revisar el diff
   completo antes de commitear, no solo lo de hoy.
2. **Arrancar Fase 2** (diseño de esquema, `04-plan-de-trabajo.md`): ahora
   sí hay un Lakebase real contra el cual probar cada tabla — una por
   formato, con su tipo de dato Postgres correspondiente, `geometry(Point,
   4326)` para OSM/PostGIS, `vector(1536)` para embeddings/pgvector.
3. Nada bloqueado. La próxima sesión puede arrancar directo en Fase 2 sin
   pasos manuales previos.
