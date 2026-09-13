variable "project_prefix" {
  description = "Prefijo para el nombre de todos los recursos (ver reglas/05-convenciones-repo.md)"
  type        = string
  default     = "lakebase-mf"
}

variable "location" {
  description = "Region de Azure"
  type        = string
  default     = "eastus2"
}

variable "tags" {
  description = "Tags comunes para todos los recursos"
  type        = map(string)
  default = {
    project = "lakebase-multiformat-databricks"
  }
}
