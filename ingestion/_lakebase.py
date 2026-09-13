"""
Conexion compartida a Lakebase para los scripts de ingesta (Fase 4).
Mismo mecanismo que schemas/apply_schema.py: OAuth M2M via el SDK de
Databricks (generate_database_credential), sin password estatica
(enable_pg_native_login = false en terraform/lakebase/variables.tf).
"""

import os

import psycopg
from databricks.sdk import WorkspaceClient

ENDPOINT_NAME = "projects/lakebase-mf-project/branches/production/endpoints/primary"
PGHOST = "ep-rapid-smoke-e1kgxkia.database.eastus2.azuredatabricks.net"
PGDATABASE = "databricks_postgres"
PGPORT = 5432


def get_connection() -> psycopg.Connection:
    client = WorkspaceClient(
        host=os.environ["DATABRICKS_HOST"],
        client_id=os.environ["DATABRICKS_CLIENT_ID"],
        client_secret=os.environ["DATABRICKS_CLIENT_SECRET"],
    )
    credential = client.postgres.generate_database_credential(endpoint=ENDPOINT_NAME)
    return psycopg.connect(
        dbname=PGDATABASE,
        user=os.environ["DATABRICKS_CLIENT_ID"],
        password=credential.token,
        host=PGHOST,
        port=PGPORT,
        sslmode="require",
        connect_timeout=30,
    )
