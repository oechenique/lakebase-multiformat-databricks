# Convenciones del repo

## Estructura general propuesta

```
lakebase-multiformat-databricks/
  terraform/               # infra Lakebase (ver 02-infra-lakebase-terraform.md)
  ingestion/                  # un script/notebook por formato
    xml/
    tabular/                    # csv, excel, parquet
    api_json/
    geospatial/
    embeddings/
  schemas/                          # definición SQL de cada tabla
  tests/                              # validación de Fase 1
  reglas/                                # esta misma carpeta
  README.md
  .gitignore
```

## Naming

Mismo criterio que los 3 proyectos anteriores: snake_case para archivos
Python, kebab-case para carpetas, prefijo del proyecto en nombres de
recursos (`lakebase-mf-project`, etc.).

## Secrets

- `client_secret` del Service Principal → Key Vault, nunca en texto plano
- Cualquier API key de las fuentes (si alguna llegara a requerirla) → mismo
  tratamiento
- `.gitignore` completo desde el primer commit (ver
  `02-infra-lakebase-terraform.md`)

## Commits

Un commit por fase completa, no commits sueltos de "wip" — mismo hábito que
viene funcionando bien en los 3 proyectos anteriores.
