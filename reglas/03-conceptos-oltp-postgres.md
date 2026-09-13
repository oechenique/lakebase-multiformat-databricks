# OLTP vs OLAP, y las piezas de Postgres que hacen falta entender

## La distinción central (el error a no cometer en el video)

| | OLTP | OLAP |
|---|---|---|
| Qué es | Transacciones puntuales, rápidas | Consultas analíticas sobre grandes volúmenes |
| Ejemplo de operación | `INSERT`, `UPDATE`, `SELECT` de un registro | `GROUP BY`, agregaciones sobre millones de filas |
| Latencia objetivo | Milisegundos | Segundos (aceptable para análisis) |
| En este portfolio | Lakebase (este proyecto) | Delta Lake (los 3 proyectos anteriores) |

Lakebase **no reemplaza** al Lakehouse — lo complementa. La pregunta de
entrevista real detrás de esto: *"¿cuándo usarías OLTP y cuándo OLAP?"* —
respuesta: OLTP cuando una aplicación necesita leer/escribir registros
individuales rápido (el carrito de compras, el estado de sesión de un
usuario, el chat de un agente); OLAP cuando necesitás agregar/analizar datos
históricos a gran escala.

## Extensiones de Postgres que usa este proyecto

Lakebase es Postgres estándar con soporte de extensiones — confirmado que
soporta:

- **`pgvector`** — búsqueda por similitud vectorial. Se usa para el
  formato "texto + embeddings" (ver `01-fuentes-formatos.md`). Soporta
  índices HNSW e IVFFlat para acelerar la búsqueda.
- **`PostGIS`** — funciones geoespaciales. Se usa para el formato
  "OpenStreetMap".

Ambas se instalan con `CREATE EXTENSION` una vez que el proyecto está
creado — no requieren nada especial de Terraform, es SQL estándar corrido
contra la base.

## Branching — la característica distintiva de Lakebase frente a un Postgres tradicional

Lakebase permite crear **branches** de la base de datos — copias
"copy-on-write" aisladas, al estilo `git branch`. Esto es interesante para
mostrar en el video: se puede crear una branch de desarrollo, probar
cambios de esquema sin tocar la branch de producción, y descartarla sin
costo si algo sale mal. Vale la pena un momento del video mostrando esto —
es la feature que más diferencia a Lakebase de "un RDS cualquiera".

## Sincronización a Unity Catalog — el puente OLTP → OLAP

**Corrección (confirmada en Fase 5 contra la documentación oficial y la
API real)**: el mecanismo NO es CDC hacia una copia materializada en
Delta como se asumía originalmente en este archivo.
`databricks_postgres_synced_table` existe, pero sincroniza en la
dirección **contraria** (Unity Catalog Delta → Postgres, vía Change Data
Feed, para servirle datos analíticos ya materializados a una app OLTP) —
no sirve para este caso de uso.

El puente real OLTP → OLAP es **`databricks_postgres_catalog`**
(Lakehouse Federation): registra la base de Postgres directamente como un
catálogo de Unity Catalog, y las tablas quedan consultables **en vivo**
desde Databricks SQL/notebooks sin copiar ni mover los datos. Esto es un
buen cierre de demo igual: mostrar que un dato que entró por el lado
transaccional (Lakebase) también aparece consultable del lado analítico
(Unity Catalog) — es la misma promesa de "un solo modelo de gobierno para
OLTP y OLAP", solo que vía federación en vez de una copia física.

## Checklist de autoevaluación

- [ ] ¿Puedo explicar en una frase por qué Lakebase es OLTP y no OLAP, sin
      confundir los términos?
- [ ] ¿Sé qué extensión corresponde a cada uno de los 5 formatos de este
      proyecto?
- [ ] ¿Puedo explicar qué es una branch de Lakebase sin usar la palabra
      "tabla"?
- [ ] ¿Entiendo qué significa que el drift detection sea limitado, y por
      qué eso cambia cómo interactúo con la infra una vez creada?
