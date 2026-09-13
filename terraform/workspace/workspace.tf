# Workspace definitivo del proyecto.
#
# El acceso al Account Console de Databricks (necesario para crear el
# Service Principal OAuth M2M con CAN MANAGE sobre el proyecto de Lakebase)
# ya no depende de este workspace: se resolvio dando de alta un usuario
# nativo de Entra ID con Owner + Global Administrator (ver
# reglas/07-decision-acceso-lakebase.md). Este workspace es simplemente la
# infra base del proyecto, mismo patron que en los 3 proyectos anteriores
# del portfolio.
#
# SKU Premium desde el arranque - Azure retiro Standard para workspaces
# nuevos.

resource "azurerm_databricks_workspace" "this" {
  name                        = "${var.project_prefix}-dbx"
  resource_group_name         = azurerm_resource_group.main.name
  location                    = azurerm_resource_group.main.location
  sku                         = "premium"
  managed_resource_group_name = "${var.project_prefix}-dbx-managed-rg"
  tags                        = var.tags
}
