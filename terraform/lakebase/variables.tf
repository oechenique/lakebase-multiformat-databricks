variable "project_id" {
  description = "Identificador del proyecto Lakebase (ver reglas/05-convenciones-repo.md para naming)"
  type        = string
  default     = "lakebase-mf-project"
}

variable "display_name" {
  description = "Nombre legible del proyecto, visible en el Account Console"
  type        = string
  default     = "Lakebase Multiformato"
}

variable "pg_version" {
  description = "Version mayor de Postgres"
  type        = number
  default     = 17
}

variable "enable_pg_native_login" {
  description = "Permitir roles nativos de Postgres con password estatica. false por defecto (recomendado); ver reglas/02-infra-lakebase-terraform.md sobre manejo de secrets."
  type        = bool
  default     = false
}

variable "endpoint_min_cu" {
  description = "Compute Units minimas del endpoint primary (autoscaling)"
  type        = number
  default     = 0.5
}

variable "endpoint_max_cu" {
  description = "Compute Units maximas del endpoint primary (autoscaling)"
  type        = number
  default     = 1
}

variable "endpoint_suspend_timeout" {
  description = "Segundos de inactividad antes de escalar a cero computo (ver reglas/02-infra-lakebase-terraform.md, patron de costo: storage siempre activo, compute escala a cero)"
  type        = string
  default     = "300s"
}

variable "dev_branch_ttl" {
  description = "Duracion de vida de la branch de desarrollo de Fase 5 (formato Go duration, ej. '48h'). Expira sola aunque nos olvidemos de destruirla a mano en Fase 6."
  type        = string
  default     = "48h"
}

variable "purge_on_delete" {
  description = "true = borrado permanente inmediato al destruir (sin retencion de 7 dias). Portfolio project de 'crear, mostrar, apagar' (ver reglas/00-overview.md) - no necesitamos la ventana de recuperacion."
  type        = bool
  default     = true
}
