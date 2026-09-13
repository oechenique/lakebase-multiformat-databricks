output "project_name" {
  value = databricks_postgres_project.this.name
}

output "branch_name" {
  value = databricks_postgres_branch.production.name
}

output "endpoint_name" {
  value = databricks_postgres_endpoint.primary.name
}

output "primary_host" {
  description = "Host de conexion read-write del endpoint primary"
  value       = try(databricks_postgres_endpoint.primary.status.hosts.host, null)
}

output "dev_branch_name" {
  value = databricks_postgres_branch.dev.name
}

output "dev_endpoint_name" {
  value = databricks_postgres_endpoint.dev.name
}

output "dev_host" {
  description = "Host de conexion read-write del endpoint dev (branch de desarrollo)"
  value       = try(databricks_postgres_endpoint.dev.status.hosts.host, null)
}

output "uc_catalog_name" {
  description = "Nombre del catalogo de Unity Catalog registrado via Lakehouse Federation"
  value       = databricks_postgres_catalog.lakebase_mf.name
}
