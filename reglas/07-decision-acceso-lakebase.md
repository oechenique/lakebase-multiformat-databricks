# Decisión — camino elegido para destrabar el acceso a Lakebase

## Decisión

Se elige el **camino completo**: resolver el trámite de identidad en Entra ID
para poder crear el Service Principal con OAuth M2M, y gestionar Lakebase
100% por Terraform, igual que [[databricks-medallion-terraform]],
[[asesor-turismo-databricks]] y [[streaming-satelites-databricks]].

Se descarta (por ahora) la alternativa de crear el proyecto Lakebase a mano
desde la UI del workspace. Esa alternativa es técnicamente válida — un
usuario del workspace puede crear un proyecto sin pasar por el Account
Console ni necesitar el Service Principal — pero rompe el patrón de "toda la
infra como código" que viene siendo el hilo conductor de los 4 proyectos del
portfolio, y el drift detection limitado de Lakebase (ver
`02-infra-lakebase-terraform.md`) hace más frágil mezclar recursos creados a
mano con recursos gestionados por Terraform más adelante.

## Confirmación técnica (no es una limitación de la cuenta, es un requisito real de Databricks)

Se verificó en la documentación oficial de Databricks/Microsoft Learn que el
Service Principal con OAuth M2M **no es un workaround para cuentas MSA**: es
un requisito explícito de Databricks para gestionar recursos de Lakebase
(`databricks_postgres_project`, `_branch`, `_endpoint`) por Terraform, para
cualquier tipo de cuenta. La guía oficial de "Get started with Terraform for
Lakebase" pide configurar `DATABRICKS_CLIENT_ID` / `DATABRICKS_CLIENT_SECRET`
de un Service Principal antes del primer `terraform apply` — no hay atajo
con `az login` ni con un token personal de usuario para este recurso en
particular. Esto confirma que `02-infra-lakebase-terraform.md` estaba bien
planteado desde el principio.

## Confirmación sobre el trámite de Entra ID en cuenta Free/personal

También se confirmó que el trámite de crear un usuario nativo en Entra ID no
requiere ningún plan pago de Azure AD/Entra ID (P1/P2) ni una suscripción
"empresarial": toda cuenta de Azure, incluida una personal (MSA) como la de
Gastón, tiene un tenant de Microsoft Entra ID generado automáticamente en el
tier Free, y la persona que se dio de alta en ese tenant ya es Global
Administrator de él por default. El bloqueo nunca fue de permisos o de
plan — es que el Account Console de Databricks rechaza específicamente el
*tipo* de identidad MSA (error `AADSTS500200`), sin importar el rol. Un
usuario nativo creado dentro de ese mismo tenant Free (no una cuenta
invitada) resuelve el problema de tipo de identidad sin necesitar upgradear
nada.

## Próximos pasos (retomando el plan ya escrito en `06-estado-actual.md`)

Sin cambios respecto al plan ya documentado — se reconfirma como la ruta a
seguir:

1. Crear el usuario nativo en Entra ID (Azure Portal → Entra ID → Users →
   New user → "Create new user", no invitado).
2. Asignarle rol **Owner** sobre la suscripción de Azure.
3. Asignarle rol **Global Administrator** en Entra ID.
4. Loguearse a `accounts.azuredatabricks.net` con ese usuario nativo.
5. Crear el Service Principal OAuth M2M con `CAN MANAGE` sobre el futuro
   proyecto de Lakebase.
6. Recrear el workspace bootstrap (o el workspace definitivo) por Terraform
   si hace falta.

Los pasos 1-5 son manuales, en el Azure Portal y en el Account Console de
Databricks — no delegables a Claude Code. El paso 6 en adelante sí es
trabajo de Terraform/código.
