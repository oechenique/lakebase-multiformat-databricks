# Infraestructura — Lakebase + Terraform

## La diferencia de autenticación (lo más importante, no descubrirlo a los golpes)

En los 3 proyectos anteriores, `az login` + el provider `databricks`
apuntando a `azure_workspace_resource_id` alcanzaba para todo. **Con
Lakebase esto NO alcanza.** Los recursos de Lakebase requieren:

1. Un **Service Principal** de Databricks configurado para **OAuth
   machine-to-machine (M2M)**
2. Ese Service Principal necesita permiso **`CAN MANAGE`** sobre el
   proyecto de Lakebase (`CAN USE` no alcanza — no permite crear/modificar
   recursos)
3. Las credenciales del Service Principal (`client_id` + `client_secret`)
   se pasan al provider vía variables de entorno:
   ```
   DATABRICKS_HOST
   DATABRICKS_CLIENT_ID
   DATABRICKS_CLIENT_SECRET
   ```

Configurar esto es el primer paso real de la Fase 3 (infra) — no asumir que
la sesión de `az login` que ya tenemos de los proyectos anteriores sirve acá
también.

## Modelo de recursos: Autoscaling, no Provisioned

Desde marzo de 2026, todo Lakebase nuevo se crea en modelo **Autoscaling**
(el modelo viejo "Provisioned" queda para instancias legacy). Los recursos
de Terraform correspondientes son:

- `databricks_postgres_project` — el contenedor de más alto nivel
- `databricks_postgres_branch` — un ambiente aislado (copy-on-write) dentro
  del proyecto; al crear el proyecto, Databricks automáticamente aprovisiona
  una branch por defecto llamada `production` con un endpoint `primary`
- `databricks_postgres_endpoint` — el punto de conexión (lectura-escritura
  o solo lectura) sobre una branch
- `databricks_postgres_catalog` — el registro en Unity Catalog para que la
  data sea consultable también desde el lado analítico
- `databricks_postgres_synced_table` — sincronización de tablas hacia
  Delta, si se quiere mostrar el puente OLTP → OLAP

**No usar `databricks_database_instance`** — ese es el recurso legacy del
modelo Provisioned, no corresponde para un proyecto nuevo hoy.

## Orden de creación (jerarquía padre-hijo)

Proyecto → Branch → Endpoint → Catálogo/Tablas. Terraform requiere crear en
ese orden, y **destruir en el orden inverso** (hijos antes que padres) — a
diferencia de los proyectos anteriores donde Terraform resolvía solo casi
toda la dependencia.

## Un detalle a tener en cuenta: drift detection limitado

La documentación oficial advierte: los cambios hechos fuera de Terraform
(por UI, CLI o API) **no siempre se detectan** por el drift detection
estándar de Terraform para recursos de Lakebase. Esto significa: evitar
tocar nada manualmente desde el portal una vez que la infra esté gestionada
por Terraform — a diferencia de otros recursos de Azure, acá "tocar a mano y
después corregir con Terraform" es más propenso a dejar el estado
inconsistente.

## Costos — patrón distinto a los proyectos anteriores

Lakebase Autoscaling **escala a cero cómputo cuando no hay actividad**, pero
sigue teniendo un costo base de almacenamiento mientras el proyecto exista.
No es como el Databricks Workspace clásico (donde el costo caro es el
cómputo del cluster) — acá lo más parecido al patrón conocido es: crear,
usar, demostrar, y `terraform destroy` cuando se termina, igual que
siempre, pero sin la urgencia de "el compute nunca para" que tuvimos con
Lakeflow Pipelines en modo continuo en el proyecto de streaming.

## .gitignore — mismo hábito no negociable

```
**/.terraform/*
*.tfstate
*.tfstate.*
*.tfvars
!*.tfvars.example
.terraform.lock.hcl
*.tfplan.out
tfplan.out
tfdestroy.out
*.out
.env
.env.*
__pycache__/
*.pyc
```

El `client_secret` del Service Principal va a Key Vault, nunca en texto
plano ni en ningún archivo de plan — mismo criterio que aprendimos con el
incidente de OpenRouter en el proyecto de Turismo.
