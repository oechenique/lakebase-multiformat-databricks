"""
Fase 4 - Ingesta CSV / Excel / Parquet -> 3 tablas (una por sub-formato).
Mismas fuentes validadas en Fase 1 (ver tests/validate_tabular.py):

- CSV: datos.gob.ar, serie de tipo de cambio BNA vendedor
       -> tabular_exchange_rate
- Excel (.xls): INDEC, apertura del IPC - hoja "Indices aperturas"
       (niveles de indice, no variaciones %) -> tabular_ipc_breakdown
- Parquet: sample userdata1.parquet del repo de DuckDB -> tabular_userdata

Uso (cargar .env y correr en la misma invocacion de shell):
    set -a && source .env && set +a && .venv/Scripts/python ingestion/tabular/ingest_tabular.py
"""

import datetime as dt
import io
import sys
from pathlib import Path

import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _lakebase import get_connection  # noqa: E402

CSV_URL = (
    "https://apis.datos.gob.ar/series/api/series/"
    "?ids=168.1_T_CAMBIOR_D_0_0_26&format=csv&last=200"
)
EXCEL_URL = "https://www.indec.gob.ar/ftp/cuadros/economia/sh_ipc_aperturas.xls"
EXCEL_SHEET_INDEX = 2  # "Indices aperturas": niveles de indice, no variaciones %
PARQUET_URL = (
    "https://raw.githubusercontent.com/duckdb/duckdb/main/"
    "data/parquet-testing/userdata1.parquet"
)


def ingest_csv() -> int:
    print(f"[CSV] GET {CSV_URL}")
    response = requests.get(CSV_URL, timeout=30)
    response.raise_for_status()
    df = pd.read_csv(io.StringIO(response.text))
    df["indice_tiempo"] = pd.to_datetime(df["indice_tiempo"]).dt.date

    conn = get_connection()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO tabular_exchange_rate (fecha, tipo_cambio_bna_vendedor)
                VALUES (%s, %s)
                ON CONFLICT (fecha) DO UPDATE SET
                    tipo_cambio_bna_vendedor = EXCLUDED.tipo_cambio_bna_vendedor
                """,
                list(df.itertuples(index=False, name=None)),
            )
    finally:
        conn.close()
    return len(df)


def _region_blocks(df: pd.DataFrame, region_rows: list[int]) -> list[tuple[int, str, int, int]]:
    """(fila_encabezado, nombre_region, primera_fila_categoria, fin_exclusivo).

    No se asume una cantidad fija de filas en blanco entre el encabezado de
    region y la primera categoria (varia segun la publicacion real de
    INDEC) - se detecta por contenido: filas con columna 0 no vacia forman
    el bloque, hasta la proxima fila vacia o el proximo encabezado.
    """
    blocks = []
    n_rows = len(df)
    for i, rr in enumerate(region_rows):
        region_name = str(df.iat[rr, 0]).strip()
        end = region_rows[i + 1] if i + 1 < len(region_rows) else n_rows
        r = rr + 1
        while r < end and pd.isna(df.iat[r, 0]):
            r += 1
        cat_start = r
        while r < end and pd.notna(df.iat[r, 0]):
            r += 1
        blocks.append((rr, region_name, cat_start, r))
    return blocks


def ingest_excel() -> int:
    print(f"[Excel] GET {EXCEL_URL}")
    response = requests.get(EXCEL_URL, timeout=30)
    response.raise_for_status()
    xls = pd.ExcelFile(io.BytesIO(response.content), engine="xlrd")
    df = xls.parse(xls.sheet_names[EXCEL_SHEET_INDEX], header=None)

    region_rows = df.index[df[0].astype(str).str.startswith("Regi", na=False)].tolist()
    blocks = _region_blocks(df, region_rows)

    rows: list[tuple] = []
    for header_row, region_name, cat_start, cat_end in blocks:
        date_cols = [
            c for c in range(1, df.shape[1]) if isinstance(df.iat[header_row, c], dt.datetime)
        ]
        for cat_row in range(cat_start, cat_end):
            categoria = str(df.iat[cat_row, 0]).strip()
            for col in date_cols:
                fecha = df.iat[header_row, col].date()
                value = df.iat[cat_row, col]
                # "///" (y otros marcadores no numericos) = dato no
                # relevado por INDEC ese periodo (ej. rubros sin
                # relevamiento durante la cuarentena 2020) - se guarda NULL,
                # no se inventa un valor.
                indice = value if isinstance(value, (int, float)) else None
                rows.append((fecha, region_name, categoria, indice))

    conn = get_connection()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO tabular_ipc_breakdown (fecha, region, categoria, indice)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (fecha, region, categoria) DO UPDATE SET
                    indice = EXCLUDED.indice
                """,
                rows,
            )
    finally:
        conn.close()
    return len(rows)


def ingest_parquet() -> int:
    print(f"[Parquet] GET {PARQUET_URL}")
    response = requests.get(PARQUET_URL, timeout=30)
    response.raise_for_status()
    df = pd.read_parquet(io.BytesIO(response.content))
    df = df.where(pd.notna(df), None)

    columns = [
        "id", "registration_dttm", "first_name", "last_name", "email", "gender",
        "ip_address", "cc", "country", "birthdate", "salary", "title", "comments",
    ]
    rows = list(df[columns].itertuples(index=False, name=None))

    conn = get_connection()
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO tabular_userdata
                    (id, registration_dttm, first_name, last_name, email, gender,
                     ip_address, cc, country, birthdate, salary, title, comments)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    registration_dttm = EXCLUDED.registration_dttm,
                    first_name        = EXCLUDED.first_name,
                    last_name         = EXCLUDED.last_name,
                    email             = EXCLUDED.email,
                    gender            = EXCLUDED.gender,
                    ip_address        = EXCLUDED.ip_address,
                    cc                = EXCLUDED.cc,
                    country           = EXCLUDED.country,
                    birthdate         = EXCLUDED.birthdate,
                    salary            = EXCLUDED.salary,
                    title             = EXCLUDED.title,
                    comments          = EXCLUDED.comments
                """,
                rows,
            )
    finally:
        conn.close()
    return len(rows)


if __name__ == "__main__":
    failures = []

    for label, fn in (("CSV", ingest_csv), ("Excel", ingest_excel), ("Parquet", ingest_parquet)):
        try:
            n = fn()
            print(f"[{label}] OK - {n} filas insertadas/actualizadas")
        except Exception as exc:  # noqa: BLE001 - reporte de ingesta, no produccion
            print(f"[{label}] FALLO - {exc}")
            failures.append(label)
        print()

    if failures:
        print(f"Fuentes con problemas: {failures}")
        sys.exit(1)
