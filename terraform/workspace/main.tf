resource "azurerm_resource_group" "main" {
  name     = "${var.project_prefix}-rg"
  location = var.location
  tags     = var.tags
}
