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
