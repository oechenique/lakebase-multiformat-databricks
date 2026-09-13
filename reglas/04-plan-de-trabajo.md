# Plan de trabajo — fase por fase

## Fase 0 — Setup

- [ ] Repo inicializado, `.gitignore` completo desde el primer commit
- [ ] Confirmar que las alertas de budget de Azure siguen activas
- [ ] Crear el Service Principal de Databricks para OAuth M2M, con permiso
      `CAN MANAGE` sobre el futuro proyecto de Lakebase (ver
      `02-infra-lakebase-terraform.md`) — esto es distinto a lo que se hizo
      en los proyectos anteriores, no reusar el flujo de `az login` a solas

## Fase 1 — Validar cada fuente aislada, sin Terraform, sin Lakebase todavía

Para cada uno de los 5 formatos (`01-fuentes-formatos.md`):
- [ ] Confirmar que la fuente candidata responde bien (o buscar alternativa
      si no)
- [ ] Escribir un script mínimo que traiga una muestra y la deje en un
      DataFrame/estructura en memoria, sin escribir a ningún lado todavía
- [ ] Confirmar el mapeo de formato → tipo de tabla/extensión Postgres
      (relacional simple, PostGIS, pgvector)

**No avanzar a la Fase 2 hasta validar los 5 formatos por separado.**

## Fase 2 — Diseño de esquema

- [ ] Una tabla (o conjunto de tablas) por formato, con su tipo de dato
      Postgres correspondiente
- [ ] Para el formato geoespacial: confirmar el tipo `geometry`/`geography`
      de PostGIS a usar
- [ ] Para embeddings: confirmar dimensión del vector según el modelo de
      embeddings elegido, y qué tipo de índice (HNSW vs IVFFlat)

## Fase 3 — Infraestructura (Terraform)

- [ ] Service Principal + credenciales OAuth M2M configuradas como
      variables de entorno
- [ ] `databricks_postgres_project` → branch → endpoint (jerarquía
      correcta, ver `02-infra-lakebase-terraform.md`)
- [ ] `terraform plan` revisado antes de cada `apply`, mismo hábito de
      siempre

## Fase 4 — Ingesta

- [ ] Un script/notebook por formato, escribiendo a su tabla
      correspondiente en Lakebase
- [ ] Habilitar `pgvector` y `PostGIS` con `CREATE EXTENSION`
- [ ] Confirmar que cada formato quedó bien representado con una consulta
      de verificación simple

## Fase 5 — Demostrar las features distintivas

- [ ] Crear una branch de desarrollo, mostrar el aislamiento copy-on-write
- [ ] Sincronizar al menos una tabla hacia Unity Catalog (el puente
      OLTP → OLAP)
- [ ] Una consulta de ejemplo por extensión (similitud vectorial con
      pgvector, consulta espacial con PostGIS)

## Fase 6 — Demo real y corte responsable

- [ ] Grabar evidencia de las 5 ingestas + las features de Fase 5
- [ ] `terraform destroy` en el orden correcto (endpoint → branch →
      proyecto)

## Fase 7 — Documentación y publicación

- [ ] README con el mismo formato que los 3 proyectos anteriores
- [ ] Push, video, posts — mismo combo de siempre
