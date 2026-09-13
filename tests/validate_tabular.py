"""
Fase 1 - Validacion aislada: fuentes CSV / Excel / Parquet.

Fuentes elegidas (todas sin key):
- CSV: API de series de tiempo de datos.gob.ar (tipo de cambio BNA vendedor)
- Excel (.xls): INDEC, apertura del IPC
- Parquet: dataset de muestra publico del repo de DuckDB en GitHub

No escribe a ningun lado - solo confirma que cada fuente responde y que se
puede leer a un DataFrame en memoria.

Mapeo a Postgres (ver reglas/02-infra-lakebase-terraform.md): tabla
relacional simple para cada una, sin extension especial.
"""

import io
import sys

import pandas as pd
import requests

CSV_URL = (
    "https://apis.datos.gob.ar/series/api/series/"
    "?ids=168.1_T_CAMBIOR_D_0_0_26&format=csv&limit=10"
)
EXCEL_URL = "https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_aperturas.xls"
PARQUET_URL = (
    "https://raw.githubusercontent.com/duckdb/duckdb/main/"
    "data/parquet-testing/userdata1.parquet"
)


def validate_csv() -> pd.DataFrame:
    print(f"[CSV] GET {CSV_URL}")
    response = requests.get(CSV_URL, timeout=15)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text))
    print(f"[CSV] OK - {len(df)} filas, columnas: {list(df.columns)}")
    print(df.head(3).to_string(index=False))
    return df


def validate_excel() -> pd.DataFrame:
    print(f"[Excel] GET {EXCEL_URL}")
    response = requests.get(EXCEL_URL, timeout=30)
    response.raise_for_status()
    # .xls (formato binario viejo) - motor xlrd, sin sheet_name = primera hoja
    df = pd.read_excel(io.BytesIO(response.content), engine="xlrd")
    print(f"[Excel] OK - {df.shape[0]} filas x {df.shape[1]} columnas")
    print(df.head(3).to_string(index=False))
    return df


def validate_parquet() -> pd.DataFrame:
    print(f"[Parquet] GET {PARQUET_URL}")
    response = requests.get(PARQUET_URL, timeout=30)
    response.raise_for_status()
    df = pd.read_parquet(io.BytesIO(response.content))
    print(f"[Parquet] OK - {df.shape[0]} filas x {df.shape[1]} columnas, "
          f"columnas: {list(df.columns)}")
    print(df.head(3).to_string(index=False))
    return df


if __name__ == "__main__":
    failures = []

    for label, fn in (("CSV", validate_csv), ("Excel", validate_excel), ("Parquet", validate_parquet)):
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 - reporte de validacion, no produccion
            print(f"[{label}] FALLO - {exc}")
            failures.append(label)
        print()

    if failures:
        print(f"Fuentes con problemas: {failures}")
        sys.exit(1)

    print("Mapeo Postgres propuesto: una tabla relacional simple por fuente "
          "(tipos de dato Postgres estandar, sin extension especial).")
