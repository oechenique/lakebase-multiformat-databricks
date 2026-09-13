# Bitácora — el trámite real de identidad para Lakebase

Este documento existe porque casi todo lo de acá pasó en el Azure Portal y
el Account Console de Databricks, a mano, con clicks — Claude Code nunca lo
vio, y sin este registro se pierde. Si estás siguiendo este repo y llegaste
al mismo bloqueo, esto te ahorra las horas que a nosotros nos costó.

## El problema de fondo

Una cuenta Microsoft personal (MSA, tipo Gmail) **no puede loguearse** en
`accounts.azuredatabricks.net` (error `AADSTS500200`) — limitación conocida
de Azure/Databricks desde julio 2024, no un bug ni algo específico de esta
cuenta. Sin acceso al Account Console, no se puede crear el Service
Principal con OAuth M2M que Lakebase exige para Terraform.

La solución: crear un usuario **nativo** (no invitado) dentro del mismo
tenant de Entra ID que ya viene con la cuenta MSA, y usar ESE usuario para
todo lo que sigue. No hace falta ningún plan pago de Azure AD/Entra ID
(P1/P2) — el tenant Free que se genera automáticamente con cualquier cuenta
de Azure alcanza.

## Las 4 capas de permiso que hay que entender (y no confundir)

Este fue el error de fondo que más tiempo costó: son **cuatro roles
distintos**, en cuatro lugares distintos, y tener uno no da los otros tres.

| Capa | Dónde se asigna | Qué habilita |
|---|---|---|
| **Global Administrator** (Entra ID) | Azure Portal → Entra ID → Roles | Administrar el tenant/directorio en sí |
| **Owner** (suscripción de Azure) | Azure Portal → Subscriptions → IAM | Administrar recursos de Azure (crear el workspace, etc.) |
| **Admin del Workspace** (Databricks) | Account Console → Workspaces → `<workspace>` → Permissions | Entrar y operar DENTRO de un workspace específico |
| **Metastore Admin** (Unity Catalog) | Account Console → Catalog → `<metastore>` → Admin & Sharing | Crear catálogos, otorgar permisos de UC |

Tener Global Administrator **no** te hace Owner de la suscripción, ni Admin
de un workspace, ni Metastore Admin. Los cuatro roles hay que asignarlos
por separado, a mano, uno por uno. Un Service Principal creado a nivel
cuenta, además, **tampoco** queda automáticamente habilitado en un
workspace específico — hay que agregarlo ahí también, aparte.

## Paso a paso real (con los baches tal como pasaron)

### 1. Crear el usuario nativo en Entra ID

Azure Portal → Microsoft Entra ID → Users → **"+ New user"** → **"Create
new user"** (nunca "Invite external user" — ese crea un invitado, no sirve).

- Usuario: `dbxadmin@<tu-dominio>.onmicrosoft.com`
- Contraseña autogenerada — **copiarla antes de seguir**, no se vuelve a mostrar
- En la pestaña **"Tareas"** del mismo asistente de creación, ya se puede
  asignar el rol **Global Administrator** directamente, sin un paso aparte
  después.

### 2. Asignar Owner sobre la suscripción (aparte, no sale del asistente de arriba)

Subscriptions → tu suscripción → **Access control (IAM)** → Add → Add role
assignment.

**Bache #1**: en la pestaña **"Roles de función de trabajo"** hay ~49
roles que contienen la palabra "Owner" (Azure AI Developer, Azure Migrate
Owner, Sites Owner, etc.) pero **ninguno es el genérico**. El rol que
realmente da acceso total está en la otra pestaña: **"Roles de
administrador con privilegios"**.

**Bache #2**: dentro de esa pestaña, buscar la palabra en inglés `owner`
puede devolver 0 o pocos resultados — el portal en español lo tiene
traducido como **"Propietario"**. Borrar el filtro de búsqueda y buscarlo
a simple vista, o buscar directamente "Propietario".

**Bache #3**: al asignarlo, Azure pide elegir una "Condición" de qué puede
re-delegar ese usuario. Elegimos la opción recomendada: *"Permitir que el
usuario asigne todos los roles excepto los roles de administrador con
privilegios Propietario, UAA y RBAC"* — da todo lo necesario sin quedar en
el escalón de privilegio máximo sin motivo.

### 3. Loguearse al Account Console con el usuario nuevo

`https://accounts.azuredatabricks.net`, con `dbxadmin`, no con la cuenta
MSA. Primer login pidió cambio de contraseña + configurar Microsoft
Authenticator (MFA) — normal, no es un error.

### 4. Crear el Service Principal (Account Console → User management → Service principals → Add service principal)

**Bache #4** (el que más tiempo costó diagnosticar): la página de detalle
del Service Principal muestra un campo **"ID"** numérico (ej.
`144614816285606`) que **no es** el `client_id`/Application ID que pide el
provider de Terraform. El `client_id` real tiene formato UUID
(`xxxxxxxx-xxxx-xxxx-...`). Usar el ID numérico como `client_id` no tira
error inmediato — el provider descarta la autenticación M2M en silencio y
cae en cascada al método de fallback "Azure CLI" (`az login`), autenticando
con la sesión personal del usuario. La señal de alerta es ver el propio
email en el plan de Terraform (`access_control` con un email en vez de un
UUID) en lugar de un error.

### 5. Generar el secreto OAuth (Credentials & secrets → Generate secret)

- Lifetime: usamos 90 días (no el máximo de 730) — para un proyecto de
  portfolio de vida corta no tiene sentido un secreto viviendo 2 años.
- Scope: la única opción real es `all-apis` (advertencia explícita de
  Databricks de que es sin restricción) — no hay un scope más granular en
  esta pantalla. Se acepta conscientemente, compensado por la vida corta
  del secreto y por el permiso acotado que se da después a nivel de
  recurso (`CAN_MANAGE` solo sobre el proyecto puntual, no la cuenta
  entera).

### 6. Agregar el Service Principal al workspace específico

**Bache #5**: crear el SP a nivel de cuenta no alcanza para que pueda
operar en un workspace — hay que agregarlo explícitamente. Account Console
→ Workspaces → `<workspace>` → Permissions → Add permissions → buscar el
SP → tildar **Admin access** (además de Workspace access, que suele venir
tildado por default).

Sin este paso, el `terraform apply` de los recursos de Lakebase falla con
`invalid_client` / `Client authentication failed` directamente contra el
endpoint OIDC del workspace — un error distinto y más adelante en la
cadena que el bache #4 (ese era de client_id mal copiado; este es de
permiso faltante con client_id ya correcto).

### 7. Variables de entorno para Terraform, en PowerShell (no Bash)

Baches puramente de shell, no de Databricks/Azure, pero reales y repetidos:

- La sintaxis `set -a && source .env && set +a` es de Bash — en PowerShell
  tira `InvalidEndOfLine`. Alternativa que funciona:
  ```powershell
  Get-Content .env | ForEach-Object {
      if ($_ -match '^([^=]+)=(.*)$') {
          $value = $matches[2].Trim('"').Trim("'")
          [Environment]::SetEnvironmentVariable($matches[1], $value, "Process")
      }
  }
  ```
  (el `.Trim()` importa: si el `.env` tiene los valores entre comillas, se
  cuelan literales y rompen el parseo de la URL en `DATABRICKS_HOST`)
- Las variables seteadas con scope `"Process"` **no sobreviven** a cerrar
  la ventana de terminal — hay que cargarlas de nuevo en cada sesión nueva.
- Un plan guardado (`tfplan.out`) queda **stale** si pasa tiempo o se
  corre otro `plan`/`refresh` entre medio — la solución es correr
  `terraform apply` directo (sin plan guardado) si el plan guardado ya
  quedó viejo.

### 8. Permisos de Unity Catalog (aparecieron recién en Fase 5, al sincronizar el catálogo)

**Bache #6**: `databricks_postgres_catalog` falla con `User does not have
CREATE CATALOG on Metastore` — tener `CAN_MANAGE` sobre el proyecto de
Lakebase no alcanza; hace falta el permiso a nivel de metastore.

**Bache #7**: para dar ese permiso, `dbxadmin` necesita ser **Metastore
Admin** — que es una CUARTA capa de permiso, distinta de Global
Administrator y de Admin del workspace. Se asigna en Account Console →
Catalog → `<nombre del metastore>` → Admin & Sharing → campo "Metastore
Admin" → seleccionar a `dbxadmin`.

Recién con eso, desde el SQL Editor del workspace:
```sql
GRANT CREATE CATALOG ON METASTORE TO `<client_id-del-service-principal>`;
```

**Bache #8**: incluso después de asignar Metastore Admin, `dbxadmin`
puede seguir sin poder ENTRAR al workspace en sí ("Unable to view page")
si nunca fue agregado como usuario de ESE workspace (ver paso 6 — ahí
solo habíamos agregado al Service Principal, no a `dbxadmin`). Hay que
agregarlo también, con Admin + Workspace access. Si después de agregarlo
el error persiste, cerrar sesión por completo y volver a loguearse — los
permisos nuevos a veces no aplican hasta que se genera un token de sesión
nuevo.

**Bache #9**: aun con el `GRANT CREATE CATALOG` corrido con éxito y el
catálogo creado, el Catalog Explorer (la UI) le puede seguir mostrando a
`dbxadmin` "You are missing required permissions — Requires USE_CATALOG"
al intentar ver datos de muestra — porque el catálogo quedó con el
Service Principal como *owner*, no con `dbxadmin`. Hace falta un grant
explícito aparte, solo para navegación en la UI:
```sql
GRANT USE CATALOG ON CATALOG <catalogo> TO `dbxadmin@...`;
GRANT USE SCHEMA ON SCHEMA <catalogo>.public TO `dbxadmin@...`;
GRANT SELECT ON SCHEMA <catalogo>.public TO `dbxadmin@...`;
```

### 9. Un catálogo huérfano

En el medio del diagnóstico del bache #6, se había creado un catálogo
manual desde la UI (Catalog Explorer → "Create Catalog"), sin relación
real a Lakebase — apareció vacío y generó confusión antes de identificarse
como el problema real (el `terraform apply` de Fase 5 nunca se había
aplicado de verdad). Se borró antes de seguir. Moraleja: si algo en el
Catalog Explorer aparece vacío/raro, primero confirmar si viene de
Terraform o de un click manual anterior, antes de asumir que es un bug.

## Resumen para quien solo quiere la receta corta

1. Crear usuario nativo en Entra ID (no invitado) + Global Administrator.
2. Asignarle Owner en la suscripción (pestaña "Roles de administrador con
   privilegios", no "Roles de función de trabajo").
3. Loguearse al Account Console con ese usuario.
4. Crear el Service Principal ahí — copiar el **Application ID (UUID)**,
   no el ID numérico interno.
5. Generar el secreto OAuth.
6. Agregar tanto al Service Principal **como al usuario nativo** como
   Admin del workspace específico (dos altas separadas).
7. Asignar al usuario nativo como **Metastore Admin** del metastore de
   Unity Catalog (una capa más, distinta de todo lo anterior).
8. Recién ahí, `terraform apply` de los recursos de Lakebase.
