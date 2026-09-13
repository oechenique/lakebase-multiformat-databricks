"""
Fase 2 - Aplica los archivos SQL de schemas/ contra el Lakebase real, en
orden alfabetico (00_extensions.sql primero, siempre).

Conexion via OAuth M2M: usa el Service Principal (DATABRICKS_HOST,
DATABRICKS_CLIENT_ID, DATABRICKS_CLIENT_SECRET, las mismas env vars que
Terraform) para pedir un database credential de corta duracion via el SDK
de Databricks (`generate_database_credential`) y lo usa como password de
Postgres. No hay password estatica: enable_pg_native_login = false (ver
terraform/lakebase/variables.tf).

Uso (cargar .env y correr en la misma invocacion de shell):
    set -a && source .env && set +a && .venv/Scripts/python schemas/apply_schema.py
"""

import glob
import os
import sys

import psycopg
from databricks.sdk import WorkspaceClient

# Valores publicos (outputs de `terraform output` en terraform/lakebase/),
# no son secretos - se hardcodean aca para no depender de que Terraform
# este disponible en el momento de la ingesta (Fase 4).
ENDPOINT_NAME = "projects/lakebase-mf-project/branches/production/endpoints/primary"
PGHOST = "ep-rapid-smoke-e1kgxkia.database.eastus2.azuredatabricks.net"
PGDATABASE = "databricks_postgres"
PGPORT = 5432

SCHEMA_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_FILES = sorted(
    f for f in glob.glob(os.path.join(SCHEMA_DIR, "*.sql"))
)


def get_connection() -> psycopg.Connection:
    client = WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        client_id=os.environ["DATABRICKS_CLIENT_ID"],
        client_secret=os.environ["DATABRICKS_CLIENT_SECRET"],
    )
    credential = client.postgres.generate_database_credential(endpoint=ENDPOINT_NAME)
    pguser = os.environ["DATABRICKS_CLIENT_ID"]
    return psycopg.connect(
        dbname=PGDATABASE,
        user=pguser,
        password=credential.token,
        host=PGHOST,
        port=PGPORT,
        sslmode="require",
        connect_timeout=30,
    )


def main() -> int:
    print(
        f"[schema] Conectando -> host={PGHOST} port={PGPORT} "
        f"db={PGDATABASE} endpoint={ENDPOINT_NAME}"
    )
    conn = get_connection()
    conn.autocommit = True

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT current_user, current_database()")
            print(f"[schema] Conexion OK - {cur.fetchone()}")

        for path in SCHEMA_FILES:
            name = os.path.basename(path)
            print(f"[schema] Aplicando {name} ...")
            with open(path, "r", encoding="utf-8") as f:
                sql = f.read()
            with conn.cursor() as cur:
                cur.execute(sql)
            print(f"[schema] OK - {name}")
    finally:
        conn.close()

    print(f"[schema] Listo - {len(SCHEMA_FILES)} archivos aplicados sin errores.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
