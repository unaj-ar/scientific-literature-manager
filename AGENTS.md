# AGENTS.md — Scientific Literature Manager

Guía para agentes de IA que trabajen en este repositorio. Describe el proyecto **tal como es hoy**. Lo que se quiere lograr pero todavía no existe está marcado como **Objetivo** y se reúne en la sección 12.

---

## 1. Qué es

Aplicación para gestionar literatura científica (revisión sistemática): alta, priorización y búsqueda de artículos y autores, con login, roles (`admin`, `researcher`) y una consola web de administración de usuarios.

Funcionalidad detallada: [.claude/docs/documento-funcional.md](.claude/docs/documento-funcional.md).

## 2. Stack real

| Herramienta | Versión | Notas |
|---|---|---|
| Python | 3.10+ | El CI prueba 3.10, 3.11 y 3.12. El `venv` local es 3.9.6: recrearlo con 3.10+ |
| API | FastAPI + Uvicorn | `api.py`; sirve también las páginas de `ui/` |
| Validación | Pydantic v2 | Esquemas de entrada en `api.py` |
| Base de datos | PostgreSQL 14+ | `psycopg2-binary` con SQL escrito a mano (no hay ORM) |
| Auth | PyJWT (HS256) + `pwdlib[argon2]` | Token de 60 minutos; hash Argon2 |
| Config | `python-dotenv` | Variables en `.env` (no se versiona) |
| Tests | `pytest`, `httpx` | `requirements-dev.txt` |
| Calidad | `ruff` | Solo en el CI (`ruff check .`); no hay archivo de configuración |
| Seguridad en CI | Bandit y OWASP Dependency-Check | `.github/workflows/owasp-scan.yml` |

## 3. Comandos

```bash
# Entorno
python3 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt

# API + web (puerto 8000)
uvicorn api:app --reload

# CLI de consola (sin autenticación)
python main.py

# Tests
pytest

# Lint (como el CI)
ruff check .

# Crear o promover un administrador (pide la contraseña por consola)
python -m scripts.create_admin --username <usuario> --email <email>
```

URLs locales: web `http://127.0.0.1:8000/`, Swagger `http://127.0.0.1:8000/docs`.

No hay endpoint `/health` ni archivo de configuración de `ruff`, `black` o `mypy`.

### Variables de entorno (`.env`)

`DB_HOST` (por defecto `localhost`), `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` y `SECRET_KEY` (JWT). **Nunca** copiar valores de `.env` al chat, a un commit ni a un PR.

La base local corre en un contenedor Docker (`postgres-db`, puerto 5432). `psql` por socket no funciona: usar `psql -h localhost -p 5432 -U postgres -d <DB_NAME>`.

## 4. Estructura

El código está en la raíz del repo (no hay paquete contenedor):

```text
api.py                  # Rutas FastAPI, dependencias y permisos
main.py                 # Punto de entrada de la CLI
article_manager.py      # Versión antigua y monolítica; no usar (candidata a borrarse)
config/database.py      # get_connection() y la dependencia get_db()
repository/             # Acceso a datos (SQL con psycopg2)
  article_repository.py
  user_repository.py
services/               # Reglas de negocio
  literature_service.py
  user_service.py
  auth_service.py       # Hash, JWT y get_current_user
  permissions.py        # Roles y permisos (mapa en código)
ui/                     # index.html, login.html, admin.html, cli.py
scripts/                # Migraciones V00x.sql y create_admin.py
tests/                  # pytest (estructura plana)
.claude/docs/           # Documento funcional y diagrama de arquitectura (arquitectura.mmd)
.claude/plans/          # Planes (ver sección 10)
.claude/skills/         # Skills del proyecto (enlaces a .agents/skills/)
```

Flujo de capas: `api.py` (HTTP) → `services/` (negocio) → `repository/` (SQL). Los servicios no conocen HTTP salvo por `HTTPException` (ver sección 7); los repositorios no tienen reglas de negocio.

## 5. Base de datos y migraciones

- **No hay Alembic.** Las migraciones son scripts SQL numerados en `scripts/`: aplicar **en orden** `V002.sql` → `V003.sql` → `V004.sql`.
- `V001.sql` es el esquema antiguo (con `authors` dentro de `articles`): **no aplicar**. `schema.sql` duplica `V002`.
- Los scripts nuevos son idempotentes: `IF NOT EXISTS`, `ADD COLUMN IF NOT EXISTS`, restricciones dentro de un bloque `DO $$ … $$`. (`V003` aún no lo es; corregirlo.)
- Los enums van como `VARCHAR` con `CHECK`, no como tipo `ENUM` de PostgreSQL.
- Cada cambio de esquema va en un `V00N.sql` nuevo, en el mismo PR que el código que lo usa. Nunca editar un script ya aplicado.
- Baja lógica: columnas `is_active` y `deleted_at`. Las consultas de lectura deben filtrar por `is_active` (hoy `articles` no lo hace).
- Todo SQL usa parámetros (`%s`), nunca f-strings con datos del usuario.

## 6. Auth, roles y permisos

- Roles: `admin` y `researcher`. Columna `users.role` con `CHECK`.
- Permisos en `services/permissions.py` (mapa rol → permisos): `articles:read`, `articles:create`, `users:manage`. Para uno nuevo, agregarlo al mapa y a la tabla del documento funcional.
- Los endpoints se protegen con `Depends(require_permission(<permiso>))` (en `api.py`). Esa dependencia consulta la base en cada request: bajas y cambios de rol rigen al instante.
- `POST /register` es público y **siempre** crea `researcher`. Solo un admin puede crear admins (`POST /users`).
- Reglas del servicio: un admin no cambia su propio rol ni se da de baja; no se degrada ni se da de baja al último admin activo.
- Las contraseñas se guardan solo como hash. Los errores de login no distinguen entre usuario inexistente, inactivo o contraseña incorrecta.

## 7. Errores

- Los servicios lanzan `HTTPException` con el código correcto: 400 datos inválidos, 401 autenticación, 403 sin permiso, 404 no encontrado, 409 duplicado, 422 validación de Pydantic.
- No devolver al cliente el texto de excepciones internas (hoy `POST /articles` lo hace: pendiente de corregir).
- **Objetivo:** excepciones de negocio propias y un handler global (sección 12).

## 8. Tests

- Servicios: `pytest` + `unittest.mock.MagicMock` sobre el repositorio, sin base de datos ni app (`tests/test_literature_service.py`, `tests/test_user_soft_delete.py`).
- API: `fastapi.testclient.TestClient` con `app.dependency_overrides[api.get_user_repository]` apuntando al `FakeUserRepo` en memoria de `tests/conftest.py`. Sin PostgreSQL. Para artículos, reemplazar `api.service` con un mock.
- Nunca abrir una conexión a la base real en un test.
- Cada cambio de comportamiento lleva su test. Estructura AAA y nombres `test_<qué>_<resultado>`.
- Suite actual: 30 tests, unos 2 segundos.
- No hay tests de repositorios ni de integración con PostgreSQL (ver sección 12).

## 9. Convenciones de código

Seguir los skills del proyecto: `python-code-style` (línea de 120, docstrings estilo Google, `ruff`), `python-design-patterns` (KISS, responsabilidad única, composición), `python-testing-patterns` y `postgres`.

- Código, comentarios, docstrings, nombres y mensajes de commit en **inglés**. El código antiguo tiene mensajes en español; no mezclar en código nuevo.
- Type hints en las firmas nuevas. Guard clauses: validar primero y salir temprano.
- Fechas: `datetime.now(timezone.utc)`. `datetime.utcnow()` está deprecado (aparece en `user_repository.py` y `auth_service.py`; reemplazar al tocarlos).
- Logging con `logging.getLogger(__name__)`; no usar `print` en código nuevo fuera de la CLI.
- Los servicios devuelven datos (dict o DTO), no respuestas HTTP.
- No guardar secretos ni valores por defecto inseguros: `SECRET_KEY` hoy tiene uno y debe volverse obligatoria.

## 10. Documentación y planes

- Documento funcional: `.claude/docs/documento-funcional.md`. Si cambia el comportamiento, actualizarlo en el mismo PR.
- **Cuando se pida un plan, se guarda como Markdown en `.claude/plans/`** (nombre en kebab-case, en español) y se resume en el chat con la ruta.
- Plan vigente: [.claude/plans/PLAN_CORRECCIONES.md](.claude/plans/PLAN_CORRECCIONES.md).

## 11. Git, PRs y CI

- **No hacer commit, push ni abrir PRs sin pedido expreso.** Nunca `--no-verify`, `push --force`, rebase de ramas con PR, ni push directo a `develop` o `main`.
- Ramas `<tipo>/<tema>` en kebab-case; commits `<tipo>: <Descripción en imperativo>` de hasta 72 caracteres, sin punto final y sin `Co-Authored-By`. Si hay ticket de Jira, va como scope: `feat(KEY-123): …`.
- PR contra `develop`, con la descripción en español. Aclarar si la rama trae trabajo que todavía no está en la base.
- Actualizar una rama con PR: `git merge origin/develop`, no rebase. Merge con merge commit.
- Los commits van firmados. Ninguna credencial en el repo (`.env` está en `.gitignore`).
- El CI (`.github/workflows/`): `ci.yml` (ruff + pytest en 3.10–3.12), `owasp-scan.yml`, `secret-scan.yml` y `run-agent.yml` (manual). Antes de pedir revisión: `ruff check .` y `pytest` en verde.

## 12. Objetivos (todavía no existen)

Pendientes del plan de correcciones. No asumir que ya están implementados:

- `SECRET_KEY` obligatoria por entorno y CORS restringido (hoy `*`).
- Autenticación en la CLI o su retiro.
- Manejo de errores con excepciones propias y handler global; sin filtrar errores internos.
- Tests de repositorios contra una base de prueba y tests de integración.
- Configuración de `ruff` (y evaluar `mypy`) en `pyproject.toml`.
- Unificar las migraciones (borrar `V001.sql` y `schema.sql`, hacer `V003.sql` idempotente) y evaluar Alembic.
- Eliminar `article_manager.py`.
- Soft delete real de artículos, o quitar la columna `is_active` de `articles`.
- Artículos por usuario o globales (decisión pendiente).
- Recrear el `venv` con Python 3.10+.
