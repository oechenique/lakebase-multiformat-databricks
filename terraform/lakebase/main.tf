# Jerarquia Lakebase Autoscaling: Proyecto -> Branch -> Endpoint (ver
# reglas/02-infra-lakebase-terraform.md). Al crear el proyecto, Databricks
# aprovisiona automaticamente una branch "production" con un endpoint
# "primary" implicitos - los declaramos igual con replace_existing = true
# para que Terraform tome control de esos recursos en vez de intentar
# crear otros nuevos (patron documentado por Databricks: "Get started with
# Terraform for Lakebase").

resource "databricks_postgres_project" "this" {
  project_id      = var.project_id
  purge_on_delete = var.purge_on_delete

  spec = {
    display_name           = var.display_name
    pg_version             = var.pg_version
    enable_pg_native_login = var.enable_pg_native_login
  }
}

# El SP que corre este apply ya queda como "project owner" con CAN MANAGE
# automaticamente (comportamiento default de Lakebase), pero lo declaramos
# de forma explicita para no depender de ese comportamiento implicito: si
# el proyecto se recrea, se importa, o el permiso se pierde por cualquier
# motivo, Terraform lo reconcilia solo en el proximo apply (ver
# reglas/02-infra-lakebase-terraform.md y la guia oficial "Typical Lakebase
# project setup with Terraform"). user_name resuelve al Application ID del
# SP autenticado - nunca hardcodeado.
data "databricks_current_user" "me" {}

resource "databricks_permissions" "project" {
  database_project_name = databricks_postgres_project.this.status.project_id

  access_control {
    service_principal_name = data.databricks_current_user.me.user_name
    permission_level       = "CAN_MANAGE"
  }
}

resource "databricks_postgres_branch" "production" {
  branch_id        = "production"
  parent           = databricks_postgres_project.this.name
  replace_existing = true
}

resource "databricks_postgres_endpoint" "primary" {
  endpoint_id      = "primary"
  parent           = databricks_postgres_branch.production.name
  replace_existing = true

  spec = {
    endpoint_type            = "ENDPOINT_TYPE_READ_WRITE"
    autoscaling_limit_min_cu = var.endpoint_min_cu
    autoscaling_limit_max_cu = var.endpoint_max_cu
    suspend_timeout_duration = var.endpoint_suspend_timeout
  }
}

# Fase 5 - Branch de desarrollo: fork copy-on-write de "production", NO un
# branch nuevo de cero. "parent" es el proyecto (namespace donde vive la
# branch, igual que "production"); "spec.source_branch" es la branch de la
# que se clona el estado - eso es lo que hace esto copy-on-write en vez de
# una branch vacia. No se marca is_protected: es descartable en Fase 6.
resource "databricks_postgres_branch" "dev" {
  branch_id = "dev"
  parent    = databricks_postgres_project.this.name
  spec = {
    source_branch = databricks_postgres_branch.production.name
    ttl           = var.dev_branch_ttl
  }
}

# Al hacer fork de una branch, Lakebase auto-provisiona un endpoint
# "primary" en la branch nueva (mismo comportamiento implicito que
# production/primary en Fase 0) - se adopta con replace_existing = true
# en vez de intentar crear un endpoint "dev" nuevo, que choca con "solo
# un endpoint read-write por branch" (error real visto: "read_write
# endpoint already exists").
resource "databricks_postgres_endpoint" "dev" {
  endpoint_id      = "primary"
  parent           = databricks_postgres_branch.dev.name
  replace_existing = true

  spec = {
    endpoint_type            = "ENDPOINT_TYPE_READ_WRITE"
    autoscaling_limit_min_cu = var.endpoint_min_cu
    autoscaling_limit_max_cu = var.endpoint_max_cu
    suspend_timeout_duration = var.endpoint_suspend_timeout
  }
}

# Fase 5 - Puente OLTP -> OLAP: registra la base "databricks_postgres" de
# la branch production como catalogo de Unity Catalog via Lakehouse
# Federation. Esto NO es una copia CDC hacia Delta (eso es lo que hace
# databricks_postgres_synced_table, pero en la direccion contraria: UC ->
# Postgres, para servir datos analiticos ya materializados hacia una app -
# ver documentacion oficial "Typical Lakebase project setup with
# Terraform"). Registrar el catalogo hace que las 8 tablas de schemas/
# queden consultables en vivo desde Databricks SQL/notebooks, sin mover
# los datos - correccion respecto al supuesto original de
# reglas/03-conceptos-oltp-postgres.md (que asumia CDC hacia Delta).
resource "databricks_postgres_catalog" "lakebase_mf" {
  catalog_id = "lakebase_mf_catalog"
  spec = {
    postgres_database          = "databricks_postgres"
    branch                     = databricks_postgres_branch.production.name
    create_database_if_missing = false
  }
}
