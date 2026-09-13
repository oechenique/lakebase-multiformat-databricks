"""
Fase 4 - Orquestador de las 5 ingestas, solo para presentacion/demo.

No es un pipeline nuevo ni cambia nada de la arquitectura: corre, en
secuencia, los mismos 5 scripts de ingestion/ tal cual existen y se
corren a mano (cada uno como subproceso independiente, mismo comando de
siempre), y prolija la salida para grabar en una sola toma: formato,
fuente, filas insertadas/actualizadas, tiempo por paso, y un resumen
final con el total. Los 5 scripts hacen upsert (ON CONFLICT ... DO
UPDATE), asi que correr esto de nuevo en camara no duplica ni rompe nada.

Uso (cargar .env y correr en la misma invocacion de shell):
    set -a && source .env && set +a && .venv/Scripts/python ingestion/run_all.py
"""

import re
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# (etiqueta, fuente, script) - mismo orden simple -> complejo de Fase 4.
STEPS = [
    ("XML", "BBC News World (RSS)", REPO_ROOT / "ingestion" / "xml" / "ingest_xml.py"),
    ("JSON API", "Open-Meteo (forecast)", REPO_ROOT / "ingestion" / "api_json" / "ingest_api_json.py"),
    (
        "CSV / Excel / Parquet",
        "datos.gob.ar + INDEC + sample DuckDB",
        REPO_ROOT / "ingestion" / "tabular" / "ingest_tabular.py",
    ),
    ("Geoespacial", "Overpass API (OpenStreetMap)", REPO_ROOT / "ingestion" / "geospatial" / "ingest_geospatial.py"),
    (
        "Texto + embeddings",
        "Project Gutenberg + OpenRouter",
        REPO_ROOT / "ingestion" / "embeddings" / "ingest_embeddings.py",
    ),
]

# Cada script ya imprime una linea "[Formato] OK - N fila(s) ..." por
# tabla que toca (ingest_tabular.py imprime 3, una por sub-formato) - se
# suman todas las que aparezcan en la salida de cada paso, sin duplicar
# ninguna logica de conteo.
OK_LINE = re.compile(r"^\[[^\]]+\]\s*OK\s*-\s*(\d+)\s*filas?\b", re.MULTILINE)

SEPARATOR = "=" * 72


def run_step(label: str, source: str, script: Path) -> tuple[bool, int, float]:
    print(f"\n{SEPARATOR}")
    print(f">> {label}  ({source})")
    print(SEPARATOR)

    start = time.perf_counter()
    proc = subprocess.Popen(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    output_lines = []
    for line in proc.stdout:
        print(line, end="")
        output_lines.append(line)
    proc.wait()
    elapsed = time.perf_counter() - start

    ok = proc.returncode == 0
    output = "".join(output_lines)
    rows = sum(int(n) for n in OK_LINE.findall(output))
    return ok, rows, elapsed


def print_summary(results: list[tuple[str, str, bool, int, float]], total_elapsed: float) -> None:
    print(f"\n{SEPARATOR}")
    print("RESUMEN - Fase 4: ingesta de los 5 formatos")
    print(SEPARATOR)

    total_rows = 0
    for label, source, ok, rows, elapsed in results:
        status = "OK" if ok else "FALLO"
        print(f"  [{status:5}] {label:<24} {source:<32} {rows:>7} filas   {elapsed:6.1f}s")
        total_rows += rows

    print("-" * 72)
    print(f"  TOTAL: {total_rows} filas insertadas/actualizadas en {total_elapsed:.1f}s")
    print(SEPARATOR)


def main() -> int:
    print("Fase 4 - Ingesta de los 5 formatos a Lakebase (corrida completa)")

    overall_start = time.perf_counter()
    results: list[tuple[str, str, bool, int, float]] = []

    for label, source, script in STEPS:
        ok, rows, elapsed = run_step(label, source, script)
        results.append((label, source, ok, rows, elapsed))
        if not ok:
            print(f"\n[run_all] FALLO en '{label}' - se detiene la corrida (ver salida arriba).")
            print_summary(results, time.perf_counter() - overall_start)
            return 1

    print_summary(results, time.perf_counter() - overall_start)
    return 0


if __name__ == "__main__":
    sys.exit(main())
