# Plan de despliegue: Render (app) + Supabase (base de datos)

Guía paso a paso para alguien que nunca desplegó nada. Al terminar vas a tener:

- La **base de datos PostgreSQL** en **Supabase** (gratis).
- La **app FastAPI** (`api:app`, con la web `login.html` / `index.html` / `admin.html`) en **Render** (gratis), en una URL tipo `https://scientific-literature-manager.onrender.com`.

```
 Navegador ──HTTPS──▶  Render (uvicorn api:app)  ──Postgres + SSL──▶  Supabase (pooler)
```

> Tiempo estimado: 45–60 minutos la primera vez.

---

## 0. Antes de empezar (checklist)

| Necesitás | Para qué | Cómo verificar |
|---|---|---|
| Cuenta de **GitHub** con acceso al repo `unaj-ar/scientific-literature-manager` | Render descarga el código desde ahí | Abrís el repo en el navegador |
| Cuenta en **Supabase** → https://supabase.com | Base de datos | Login con GitHub |
| Cuenta en **Render** → https://render.com | Servidor de la app | Login con GitHub |
| Python 3.10+ y el proyecto clonado localmente | Crear el primer admin | `python --version` |
| (Opcional) `psql` | Correr SQL desde la terminal | `psql --version` (macOS: `brew install libpq`) |

**Conceptos mínimos**

- **Variable de entorno**: un valor (ej. contraseña) que se le pasa a la app desde afuera, en vez de escribirlo en el código. Localmente están en `.env`; en Render se cargan en el panel.
- **Migración**: archivo `.sql` que crea/modifica tablas. Este proyecto las tiene en `scripts/`.
- **Pooler**: un "intermediario" de Supabase que reparte conexiones a la base. Render **debe** usarlo (ver paso 1.3).

---

## 1. Crear la base de datos en Supabase

### 1.1 Crear el proyecto

1. Entrá a https://supabase.com/dashboard → **New project**.
2. Completá:
   - **Name**: `scientific-literature-manager`
   - **Database Password**: clic en **Generate a password** y **guardala** (gestor de contraseñas). No se puede volver a ver.
   - **Region**: la misma (o la más cercana) que vas a usar en Render. Ej.: `East US (North Virginia)` en Supabase ↔ `Virginia (US East)` en Render. Menos distancia = app más rápida.
3. **Create new project** y esperá ~2 minutos.

### 1.2 Crear las tablas (migraciones)

Orden: **`V002.sql` → `V003.sql` → `V004.sql`**. (`V001.sql` es el esquema viejo: **no** se aplica.)

**Opción A — desde el navegador (recomendada si no sabés `psql`)**

1. Menú izquierdo → **SQL Editor** → **New query**.
2. Abrí `scripts/V002.sql` en PyCharm, copiá todo, pegalo y clic en **Run**. Debe decir `Success. No rows returned`.
3. Repetí con `V003.sql` y luego con `V004.sql` (una query cada uno, en ese orden).
4. Verificá en **Table Editor**: deben existir `authors`, `articles`, `article_authors` y `users`.

> Si `V003.sql` falla con `column "is_active" already exists`, es porque ya lo corriste: no pasa nada, seguí con el siguiente.

**Opción B — desde la terminal con `psql`**

Usá la cadena del paso 1.3 (Session pooler) y:

```bash
cd /Users/alejandro.v/PycharmProjects/pythonRevisionRepositoryProject
export DB_URL='postgresql://postgres.<PROJECT_REF>:<PASSWORD>@aws-0-<REGION>.pooler.supabase.com:5432/postgres?sslmode=require'
psql "$DB_URL" -f scripts/V002.sql
psql "$DB_URL" -f scripts/V003.sql
psql "$DB_URL" -f scripts/V004.sql
psql "$DB_URL" -c '\dt'   # lista las tablas
```

### 1.3 Obtener los datos de conexión (¡importante!)

1. Arriba en el dashboard, botón **Connect**.
2. Pestaña **Connection String** → tipo **URI** → elegí **Transaction pooler** (puerto **6543**).

   > ⚠️ **No uses "Direct connection"** (`db.<ref>.supabase.co`): solo funciona por IPv6 y Render no tiene salida IPv6 → la app no conecta (`could not translate host name` / `Network is unreachable`). El **pooler** sí funciona por IPv4.

3. La cadena se ve así:

   ```
   postgresql://postgres.abcdefghijklmnop:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```

4. Separala en las variables que usa `config/database.py`:

   | Variable | Valor de ejemplo | De dónde sale |
   |---|---|---|
   | `DB_HOST` | `aws-0-us-east-1.pooler.supabase.com` | entre `@` y `:` |
   | `DB_PORT` | `6543` | después del host |
   | `DB_USER` | `postgres.abcdefghijklmnop` | antes de `:` (¡incluye el punto y el ref!) |
   | `DB_PASSWORD` | la contraseña del paso 1.1 | — |
   | `DB_NAME` | `postgres` | al final |

   Como la app usa variables separadas, **no** hace falta "escapar" caracteres raros de la contraseña.

**¿Por qué Transaction pooler (6543)?** La app abre una conexión por request y la cierra (`get_db()` en `config/database.py`). El modo transacción está pensado justo para eso y soporta muchas conexiones cortas. psycopg2 funciona sin cambios.

### 1.4 Seguridad recomendada en Supabase

Supabase expone por defecto las tablas de `public` en una API REST propia ("Data API"). Esta app **no** la usa (habla directo con Postgres), así que conviene cerrarla. En **SQL Editor**:

```sql
ALTER TABLE authors         ENABLE ROW LEVEL SECURITY;
ALTER TABLE articles        ENABLE ROW LEVEL SECURITY;
ALTER TABLE article_authors ENABLE ROW LEVEL SECURITY;
ALTER TABLE users           ENABLE ROW LEVEL SECURITY;
```

Sin políticas, la Data API no puede leer nada; la app sigue funcionando porque se conecta como `postgres`, que es dueño de las tablas. Así desaparece el aviso rojo "RLS disabled" del dashboard.

---

## 2. Crear el primer usuario administrador

`scripts/create_admin.py` se corre **una vez desde tu máquina**, apuntando a Supabase.

1. Hacé copia de tu `.env` local: `cp .env .env.local.bak`
2. Editá `.env` con los valores del paso 1.3:

   ```dotenv
   DB_HOST=aws-0-us-east-1.pooler.supabase.com
   DB_PORT=6543
   DB_USER=postgres.abcdefghijklmnop
   DB_PASSWORD=tu_password_de_supabase
   DB_NAME=postgres
   PGSSLMODE=require
   ```

   > `PGSSLMODE=require` lo lee automáticamente psycopg2 (libpq) y fuerza conexión cifrada, sin tocar código.

3. Corré (te pide la contraseña del admin dos veces, mínimo 8 caracteres):

   ```bash
   source venv/bin/activate
   python -m scripts.create_admin --username admin --email admin@tu-dominio.com
   ```

   Salida esperada: `Administrador 'admin' creado con id 1.`

4. Volvé a tu `.env` local: `mv .env.local.bak .env`

> El `.env` está en `.gitignore`: **nunca** lo subas a GitHub.

---

## 3. Preparar el repositorio

El repo ya trae lo necesario:

- `requirements.txt` → Render instala dependencias con `pip install -r requirements.txt`.
- `render.yaml` → "Blueprint": describe el servicio para que Render lo cree solo.

Lo único que hace falta es que el código esté **en GitHub, en la rama que vas a desplegar** (normalmente `main`):

```bash
git status                 # que no haya cambios sin commitear
git push origin <tu-rama>  # luego merge a main por Pull Request
```

> Render despliega una rama concreta. Si trabajás en `fase1`, hacé el PR a `main` antes, o elegí `fase1` en Render (solo para pruebas).

---

## 4. Crear el servicio en Render

### Opción A — Blueprint (recomendada, usa `render.yaml`)

1. https://dashboard.render.com → **New +** → **Blueprint**.
2. **Connect GitHub** y autorizá a Render a ver `unaj-ar/scientific-literature-manager` (si es de una organización, puede requerir que un admin de `unaj-ar` apruebe la app de Render).
3. Elegí el repo y la rama → Render lee `render.yaml` y muestra el servicio `scientific-literature-manager`.
4. Te pide las variables marcadas `sync: false`. Completalas con los valores del paso 1.3:

   | Key | Value |
   |---|---|
   | `DB_HOST` | `aws-0-us-east-1.pooler.supabase.com` |
   | `DB_PORT` | `6543` |
   | `DB_USER` | `postgres.abcdefghijklmnop` |
   | `DB_PASSWORD` | tu password de Supabase |
   | `DB_NAME` | `postgres` |

   `SECRET_KEY` se genera solo (`generateValue: true`) y `PYTHON_VERSION` ya vale `3.12.7`.

5. **Apply** → arranca el primer deploy.
6. Después, en el servicio → **Environment** → **Add Environment Variable**: `PGSSLMODE` = `require` → **Save Changes** (redeploya solo).

### Opción B — Manual (sin Blueprint)

1. **New +** → **Web Service** → elegí el repo.
2. Completá:

   | Campo | Valor |
   |---|---|
   | Name | `scientific-literature-manager` |
   | Region | la misma zona que Supabase |
   | Branch | `main` |
   | Runtime / Language | `Python 3` |
   | Build Command | `pip install -r requirements.txt` |
   | Start Command | `uvicorn api:app --host 0.0.0.0 --port $PORT` |
   | Instance Type | `Free` |

3. **Advanced** → **Health Check Path**: `/login.html`.
4. **Environment Variables**: las 5 `DB_*` de arriba + `PGSSLMODE=require` + `PYTHON_VERSION=3.12.7` + `SECRET_KEY` (generalo con el comando de abajo).

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

5. **Create Web Service**.

> ⚠️ El Start Command **no** es `gunicorn run:app` (eso es de Flask y falla con código 127). Esta app es FastAPI: `uvicorn api:app`.

---

## 5. Verificar que funciona

1. En Render → pestaña **Logs**. Lo bueno se ve así:

   ```
   ==> Running 'uvicorn api:app --host 0.0.0.0 --port $PORT'
   INFO:     Uvicorn running on http://0.0.0.0:10000
   ==> Your service is live 🎉
   ```

2. Abrí la URL del servicio (arriba a la izquierda, `https://<nombre>.onrender.com`):
   - `/` → pantalla de login.
   - `/docs` → Swagger de la API.
3. Logueate con el admin del paso 2 → deberías ver el panel; entrá a `/admin.html` para gestionar usuarios.
4. Prueba rápida de la API desde la terminal:

   ```bash
   URL=https://scientific-literature-manager.onrender.com
   TOKEN=$(curl -s -X POST "$URL/login" \
     -d 'username=admin&password=TU_PASSWORD' | python -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
   curl -s "$URL/articles" -H "Authorization: Bearer $TOKEN"
   ```

5. En Supabase → **Table Editor** → `users` / `articles`: los datos creados desde la web aparecen ahí.

---

## 6. Deploys siguientes (el día a día)

- Por defecto **Auto-Deploy = On**: cada `git push` / merge a la rama configurada redeploya solo.
- Manual: servicio → **Manual Deploy** → **Deploy latest commit**.
- Volver atrás: **Events** → deploy anterior → **Rollback**.
- **Cambios de base de datos**: Render no corre migraciones. Si agregás un `scripts/V005.sql`, aplicalo en Supabase (**SQL Editor** o `psql`) **antes** de mergear el código que lo necesita.

---

## 7. Problemas comunes

| Síntoma (en Logs) | Causa | Solución |
|---|---|---|
| `gunicorn: command not found` (exit 127) | Start Command incorrecto | `uvicorn api:app --host 0.0.0.0 --port $PORT` |
| `could not translate host name "db.xxx.supabase.co"` / `Network is unreachable` | Usaste la conexión directa (IPv6) | Usá el **pooler**: `aws-0-<region>.pooler.supabase.com` |
| `FATAL: Tenant or user not found` | `DB_USER` sin el ref | Debe ser `postgres.<PROJECT_REF>`, no solo `postgres` |
| `password authentication failed` | Contraseña errónea | Supabase → **Project Settings → Database → Reset database password** y actualizala en Render |
| `relation "users" does not exist` | No se corrieron las migraciones | Paso 1.2 |
| `No open ports detected` / timeout del health check | La app no escucha en `$PORT` o `0.0.0.0` | Revisá el Start Command |
| La primera carga tarda ~1 minuto | Plan free de Render "duerme" tras 15 min sin tráfico | Normal; o pasar a plan pago |
| `Token inválido` para todos tras un redeploy | Cambió `SECRET_KEY` | Volver a loguearse; no regenerar la clave sin motivo |
| Supabase dice "Project paused" | Plan free pausa tras ~7 días sin actividad | **Restore project** en el dashboard |

---

## 8. Seguridad antes de abrirlo al público

Detectado en el código actual (recomendaciones, no bloquean el deploy):

1. **CORS abierto** (`api.py`: `allow_origins=["*"]` con `allow_credentials=True`). Como la web se sirve desde el mismo dominio, se puede restringir a la URL de Render.
2. **`SECRET_KEY` con valor por defecto** (`services/auth_service.py`). Si falta la variable, usa `"super_secret_key_cambiar_en_prod"`. Verificá en Render → **Environment** que exista.
3. **`gunicorn` en `requirements.txt`** no se usa; se puede quitar.
4. **Contraseña de Supabase**: solo en Render y en tu gestor de contraseñas; nunca en el repo ni en chats.
5. **Backups**: el plan free de Supabase tiene backups diarios limitados; para datos importantes, exportá periódicamente:
   ```bash
   pg_dump "$DB_URL" --no-owner -f backup_$(date +%F).sql
   ```

---

## 9. Resumen de valores (plantilla para completar)

```text
Supabase project ref : ____________________
Pooler host          : aws-0-__________.pooler.supabase.com
DB_PORT              : 6543
DB_USER              : postgres.____________
DB_NAME              : postgres
Render URL           : https://____________.onrender.com
Rama desplegada      : main
Admin inicial        : ____________
```

---

## Referencias oficiales

- Render — Deploy de FastAPI: https://render.com/docs/deploy-fastapi
- Render — Blueprints (`render.yaml`): https://render.com/docs/blueprint-spec
- Render — Variables de entorno: https://render.com/docs/configure-environment-variables
- Render — Plan gratuito (sleep, límites): https://render.com/docs/free
- Render — Health checks: https://render.com/docs/health-checks
- Supabase — Conectarse a Postgres (pooler vs directa): https://supabase.com/docs/guides/database/connecting-to-postgres
- Supabase — IPv4/IPv6: https://supabase.com/docs/guides/platform/ipv4-address
- Supabase — SQL Editor: https://supabase.com/docs/guides/database/overview
- Supabase — Row Level Security: https://supabase.com/docs/guides/database/postgres/row-level-security
- FastAPI — Conceptos de despliegue: https://fastapi.tiangolo.com/deployment/concepts/
- psycopg2 / libpq — variables `PGSSLMODE`: https://www.postgresql.org/docs/current/libpq-envars.html
