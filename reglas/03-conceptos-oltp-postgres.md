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

Lo que se escribe en Lakebase puede sincronizarse (vía CDC, change data
capture) hacia tablas Delta en Unity Catalog, quedando disponible para
análisis sin ETL manual. Esto es un buen cierre de demo: mostrar que un dato
que entró por el lado transaccional (Lakebase) también aparece consultable
del lado analítico (Delta/Unity Catalog) — es literalmente la promesa de
"un solo modelo de gobierno para OLTP y OLAP".

## Checklist de autoevaluación

- [ ] ¿Puedo explicar en una frase por qué Lakebase es OLTP y no OLAP, sin
      confundir los términos?
- [ ] ¿Sé qué extensión corresponde a cada uno de los 5 formatos de este
      proyecto?
- [ ] ¿Puedo explicar qué es una branch de Lakebase sin usar la palabra
      "tabla"?
- [ ] ¿Entiendo qué significa que el drift detection sea limitado, y por
      qué eso cambia cómo interactúo con la infra una vez creada?
