# Fuentes de datos por formato

Mismo principio que guió las elecciones en los 3 proyectos anteriores: **cero
fricción de credenciales cuando sea posible**, y todo a validar de forma
aislada en la Fase 1 antes de construir nada — estos son candidatos, no
decisiones cerradas.

## XML

Candidatos:
- Un feed RSS/Atom público (es XML estándar, cualquier medio o institución
  tiene uno, sin key)
- API de PubMed (búsquedas científicas, devuelve XML, sin key)
- Datasets de organismos públicos que publican en XML (a confirmar
  disponibilidad real en Fase 1)

## CSV / Excel / Parquet

Candidatos:
- **datos.gob.ar** (portal de datos abiertos de Argentina) — CSV directo,
  sin key, temática libre
- Datasets públicos en Parquet del "Registry of Open Data on AWS" u otro
  bucket público — confirmar acceso de solo lectura sin credenciales de AWS
- Excel: cualquier dataset de un organismo público que lo publique en ese
  formato (a buscar en Fase 1, es el formato menos común de encontrar
  gratis y sin fricción)

## JSON desde una API pública

Candidatos (reusando el mismo criterio "sin key" de los proyectos
anteriores):
- Cualquier API REST pública simple, sin necesidad de que temáticamente se
  relacione con las demás fuentes — el objetivo es demostrar el patrón de
  ingesta, no contar una historia conjunta

## Geoespacial — OpenStreetMap

- **Overpass API** — consultas sobre datos de OSM, gratis, sin key. Gastón
  ya tiene experiencia directa con esto de [[rutia]], así que es reusar
  know-how, no aprender de cero.
- Se ingesta a una tabla con la extensión **PostGIS** habilitada en
  Lakebase (confirmada como soportada — ver `03-conceptos-oltp-postgres.md`)

## Texto + embeddings (RAG/LLM style — no espaciales)

- Un corpus de texto público (ej. Project Gutenberg, artículos de
  Wikipedia) trozado en chunks
- Embeddings generados con un modelo vía OpenRouter (mismo proveedor que
  ya se usó en [[asesor-turismo-databricks]] y en el curso de
  certificación — coherencia de stack)
- Guardado en una tabla con la extensión **`pgvector`** de Lakebase, con
  búsqueda de similitud coseno

## Nota sobre coherencia temática

A diferencia del proyecto de Turismo, **acá los datos NO necesitan
relacionarse entre sí**. El pitch del proyecto es "demuestro que puedo
modelar e ingestar cualquier formato hacia un motor gobernado", no una
historia de negocio unificada. Está bien que el feed RSS no tenga nada que
ver con los datos de OpenStreetMap.
