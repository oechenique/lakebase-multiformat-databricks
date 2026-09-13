# Ingesta multi-formato a Databricks Lakebase (OLTP) — Overview

## Qué es esto

El cuarto proyecto del portfolio, después de [[databricks-medallion-terraform]]
(batch), [[asesor-turismo-databricks]] (agente + MCP) y
[[streaming-satelites-databricks]] (streaming en tiempo real). Este cierra
con la pata que faltaba: **modelado de datos + motor relacional**, la parte
más "DBA" de Data Engineering.

## El pitch correcto del video (ojo con esto)

**Lakebase es OLTP, no OLAP.** Son conceptos opuestos, y decirlo al revés en
el video es el error que un espectador con conocimiento va a marcar en los
comentarios:

- **OLAP** (Online Analytical Processing) = el mundo que ya mostramos en los
  3 proyectos anteriores — Delta Lake, agregaciones, consultas analíticas
  sobre grandes volúmenes.
- **OLTP** (Online Transaction Processing) = Lakebase — transacciones
  rápidas, `INSERT`/`UPDATE`/`SELECT` puntual, baja latencia, como el motor
  detrás de una aplicación real.

El pitch: *"hoy vamos a hablar de OLTP en Databricks con su nuevo Lakebase —
cómo complementa al Lakehouse analítico con una base transaccional real de
Postgres, gestionada, con branching e integración nativa a Unity Catalog"*.
Ver `03-conceptos-oltp-postgres.md` para profundizar esto antes de grabar.

## La idea central del proyecto

Tomar 5-6 formatos de origen **completamente distintos y sin relación
temática entre sí** (a diferencia del proyecto de Turismo, acá no hace falta
que los datos cuenten una historia conjunta) y demostrar que se pueden
modelar, transformar e ingestar todos hacia un mismo motor relacional
gobernado. El valor está en la **versatilidad de ingesta**, no en el
storytelling de negocio.

Formatos candidatos (a confirmar/ajustar en Fase 1, ver
`01-fuentes-formatos.md`):
- XML
- CSV / Excel / Parquet
- JSON desde una API pública
- Datos geoespaciales (OpenStreetMap)
- Texto + embeddings (estilo RAG/LLM — no vectores espaciales, eso es
  PostGIS, esto es `pgvector`)

## Filosofía de diseño (heredada de los tres proyectos anteriores)

- **Nada hardcodeado** — fuentes, credenciales, nombres de tablas,
  parametrizable.
- **Validar cada fuente aislada antes de integrar** — mismo hábito que ya
  demostró su valor en los 3 proyectos previos.
- **`.gitignore` completo desde el primer commit** — el incidente de
  secrets expuestos en [[asesor-turismo-databricks]] no se repite acá.
- **Correr, mostrar, apagar** — Lakebase Autoscaling escala a cero cuando no
  hay actividad, así que el patrón de costo es distinto al de un Workspace
  clásico: revisar `02-infra-lakebase-terraform.md` para el detalle real de
  cuánto cuesta dejarlo prendido.

## Diferencia de autenticación — la lección más importante para no perder tiempo

A diferencia de los 3 proyectos anteriores (donde `az login` alcanzaba para
que el provider `databricks` se autentique), **Lakebase requiere un Service
Principal configurado para OAuth machine-to-machine (M2M) con permiso `CAN
MANAGE` sobre el proyecto**. Esto hay que configurarlo desde el arranque —
ver `02-infra-lakebase-terraform.md`.

## Índice de este directorio

- `01-fuentes-formatos.md` — candidatos de fuente por formato, a validar
- `02-infra-lakebase-terraform.md` — Terraform, autenticación M2M, modelo
  Autoscaling
- `03-conceptos-oltp-postgres.md` — OLTP vs OLAP, extensiones de Postgres,
  branching, sync a Unity Catalog
- `04-plan-de-trabajo.md` — roadmap fase por fase
- `05-convenciones-repo.md` — estructura, naming, secrets
