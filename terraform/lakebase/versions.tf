terraform {
  required_version = ">= 1.9"

  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = ">= 1.100.0, < 2.0.0"
    }
  }
}

# Autenticacion OAuth M2M del Service Principal - SIEMPRE via variables de
# entorno, nunca hardcodeadas (ver reglas/02-infra-lakebase-terraform.md):
#
#   DATABRICKS_HOST="https://<workspace_url>"   (output de terraform/workspace/)
#   DATABRICKS_CLIENT_ID="<client-id-del-service-principal>"
#   DATABRICKS_CLIENT_SECRET="<client-secret-del-service-principal>"
#
# El Service Principal debe tener permiso CAN MANAGE (no CAN USE) sobre el
# proyecto de Lakebase, otorgado desde el Account Console. Sin las 3 env
# vars seteadas, "terraform plan"/"apply" en este directorio fallan al
# autenticar - eso es esperado hasta que el Service Principal exista.
provider "databricks" {}
