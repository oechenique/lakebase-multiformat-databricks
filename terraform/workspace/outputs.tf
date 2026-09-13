output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "databricks_workspace_url" {
  description = <<-EOT
    URL del workspace. Usar este valor (con prefijo https://) como
    DATABRICKS_HOST al correr el Terraform de terraform/lakebase/, una vez
    creado el Service Principal OAuth M2M (ver
    reglas/02-infra-lakebase-terraform.md).
  EOT
  value       = "https://${azurerm_databricks_workspace.this.workspace_url}"
}

output "databricks_workspace_id" {
  description = "ID del workspace en el control plane de Databricks (informativo, no requerido por el Terraform de Lakebase)."
  value       = azurerm_databricks_workspace.this.workspace_id
}
