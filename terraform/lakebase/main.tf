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
