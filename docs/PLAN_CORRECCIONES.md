# Plan de correcciones — Scientific Literature Manager

Estado: propuesto (nada implementado). Fecha del relevamiento: 2026-11-05. Rama de origen: `login`.

Cada fase es un PR chico e independiente. El orden va de lo que rompe la app a lo cosmético.

---

## Fase 1 — Reparar lo que está roto (bloqueante)

### 1.1 Cableado de usuarios en `api.py`
- **Problema:** `user_service.deactivate_user(...)` se llama como función de módulo, pero es un método de `UserService`. `user_repository.restore(...)` se llama sin instanciar `UserRepository` (que requiere una conexión). Ambos endpoints fallan con `AttributeError`.
- **Cambio:**
  - Crear dependencias FastAPI `get_db()`, `get_user_repository()` y `get_user_service()` (una conexión por request, cerrada al terminar).
  - Mover la lógica de `restore` a `UserService.restore_user` (404 si no existe o ya está activo) y que `api.py` solo la invoque.
  - Tipar `current_user` como `dict` (hoy dice `str`).
- **Archivos:** `api.py`, `services/user_service.py`, `repository/user_repository.py`, `config/database.py`.
- **Hecho cuando:** `DELETE /users/{id}` y `PATCH /users/{id}/restore` responden 200/404/400 según el caso, con tests de API que lo prueban.

### 1.2 Login y registro
- **Problema:** `OAuth2PasswordBearer(tokenUrl="login")` apunta a una ruta inexistente; no hay forma de obtener un token ni de crear usuarios.
- **Cambio:**
  - `POST /register` (username, email, password → hash con `AuthService.hash_password`).
  - `POST /login` con `OAuth2PasswordRequestForm`; verifica hash, rechaza usuarios con `is_active = FALSE`, devuelve `access_token` (incluyendo `user_id` y `sub`).
  - Métodos `get_by_username` y `create` en `UserRepository`.
  - Mensaje de error genérico ante credenciales inválidas (no revelar si falló usuario o contraseña).
  - Conectar `ui/login.html` a `/login` y guardar el token para `index.html`.
- **Hecho cuando:** se puede registrar, loguear y usar el token en un endpoint protegido.

### 1.3 Regla de negocio de `deactivate_user`
- **Problema:** el comentario dice "no puede darse de baja si es el único admin", pero el código bloquea toda auto-baja y no existe el concepto de admin.
- **Cambio:** alinear comentario y código (dejar solo "no puede darse de baja a sí mismo") salvo que se decida agregar roles.

---

## Fase 2 — Seguridad

| # | Problema | Cambio |
|---|---|---|
| 2.1 | `SECRET_KEY` con valor por defecto fijo | Exigir la variable de entorno; si falta, fallar al arrancar. Agregarla a un `.env.example` (sin valores reales). |
| 2.2 | Endpoints de artículos sin autenticación | Agregar `Depends(get_current_user)` a `GET/POST /articles*`. |
| 2.3 | CORS `*` con `allow_credentials=True` | Lista de orígenes desde variable de entorno (`CORS_ORIGINS`). |
| 2.4 | `article_manager.py` con credenciales escritas en código | Eliminar el archivo (ver 3.1). Revisar el historial de git: si la contraseña fue real, rotarla. |
| 2.5 | `create_article` devuelve `str(e)` al cliente | Capturar `ValueError` → 400; errores de BD → 500 con mensaje genérico y log interno. |
| 2.6 | `datetime.utcnow()` deprecado (tokens y baja lógica) | Usar `datetime.now(timezone.utc)`. |
| 2.7 | Sin límite de intentos de login | Evaluar rate limiting (p. ej. `slowapi`) en `/login`. |
| 2.8 | `.env` presente en el árbol del proyecto | Está en `.gitignore`; verificar con `git log --all -- .env` que nunca se commiteó. |

**Hecho cuando:** Bandit (`bandit -r . -x ./venv --severity-level medium`) pasa sin hallazgos y no hay secretos en el repo.

---

## Fase 3 — Limpieza de código y base de datos

### 3.1 Código duplicado
- Eliminar `article_manager.py` (versión monolítica antigua; duplica repositorio, servicio y CLI).

### 3.2 Scripts SQL
- `V001.sql` queda obsoleto (columna `authors` en `articles`) y `schema.sql` duplica `V002.sql`.
- Definir una convención única de migraciones (`V001`, `V002`, `V003`… en orden) y decidir si `schema.sql` es el esquema final consolidado o se elimina.
- Hacer `V003.sql` idempotente: `ADD COLUMN IF NOT EXISTS`.
- Crear `V004.sql`: índices en `article_authors(author_id)`, `articles(priority)` y `users(is_active)`.
- Documentar el orden de ejecución en `install.md`.

### 3.3 `is_active` en artículos
- Decidir: o se aplica la baja lógica a artículos (filtrar `WHERE a.is_active` en todas las consultas) o se quita la columna de `V003`.

### 3.4 Orden por prioridad
- `ORDER BY a.priority ASC` funciona por coincidencia alfabética (P1 < P2 < P3). Aceptable por el `CHECK`, pero conviene un comentario o un `CASE` explícito.

### 3.5 Repositorios
- `user_repository.restore` ejecuta la consulta con un parámetro sobrante (`datetime`); quitarlo.
- Unificar el patrón de conexión entre `ArticleRepository` (abre su propia conexión) y `UserRepository` (la recibe).
- `with get_connection() as conn` de psycopg2 no cierra la conexión (solo gestiona la transacción): cerrarla explícitamente o usar un pool (`psycopg2.pool`).

---

## Fase 4 — Tests

| Área | Tests a agregar |
|---|---|
| `auth_service` | hash/verify, token válido, token expirado, token alterado |
| API de login | registro OK, usuario duplicado, login OK, contraseña incorrecta, usuario inactivo |
| API de usuarios | baja OK, auto-baja (400), usuario inexistente (404), restore OK/404, sin token (401) |
| API de artículos | requiere token, alta válida, título vacío (400), duplicado de DOI |
| Repositorios | contra una base de prueba (PostgreSQL en contenedor o `testcontainers`) |

Herramientas: `pytest`, `fastapi.testclient.TestClient`, `pytest-cov`. Meta: cobertura mínima del 80 % en `services/` y `repository/`.
Agregar `requirements-dev.txt` (pytest, pytest-cov, httpx, bandit, ruff) y separarlo de `requirements.txt`.

---

## Fase 5 — Documentación y CI

- **README.md:** resolver los marcadores de conflicto (`<<<<<<< HEAD`, `=======`), dejar una sola versión.
- **install.md:** corregir el formato Markdown; incluir variables de entorno nuevas (`SECRET_KEY`, `CORS_ORIGINS`), orden de migraciones y cómo correr los tests.
- **`.claude/proyect.md`:** renombrar a `project.md` y actualizar (hoy describe solo una CLI).
- **CI:** agregar al workflow un job de tests (`pytest`) y `ruff`. Hoy solo hay escaneo OWASP/Bandit. Fijar la versión de `Dependency-Check_Action` en lugar de `@main`.
- **Dependencias:** fijar versiones máximas o un `requirements.lock`.
- **`.idea/`:** está en `.gitignore`; confirmar que no esté trackeado (`git ls-files .idea`).

---

## Orden de PRs sugerido

1. `fix(api): wire user service and repository` (1.1, 1.3)
2. `feat(auth): add login and register endpoints` (1.2)
3. `fix(security): harden secrets, CORS and article endpoints` (2.x)
4. `chore: remove legacy article_manager and consolidate SQL` (3.x)
5. `test: add API, auth and repository tests` (4)
6. `docs: fix README, install guide and CI` (5)

## Decisiones pendientes (requieren definición tuya)
1. ¿Habrá roles (admin/usuario) o la regla de baja es solo "no a sí mismo"?
2. ¿Los artículos son globales o pertenecen a cada usuario? Hoy son globales; si son por usuario hace falta `user_id` en `articles`.
3. ¿Se usará baja lógica también para artículos?
4. ¿Se mantiene la CLI o se retira en favor de la web?
5. ¿Se adopta una herramienta de migraciones (Alembic/Flyway) o se siguen los scripts `V00x.sql` manuales?

---

## Skills recomendadas para este proyecto

Las de la columna "Ya disponible" están en tu entorno; no hace falta instalarlas.

| Skill | Estado | Para qué |
|---|---|---|
| `g-e-bug-fix` | Ya disponible | Fase 1: reproducir y corregir los endpoints rotos |
| `g-e-coding` | Ya disponible | Estándares de código (SOLID, DRY, manejo de errores) en las fases 1 y 3 |
| `g-e-testing-implementation` | Ya disponible | Fase 4: plan y escritura de tests |
| `secure-dev-globant` | Ya disponible | Fase 2: prácticas de desarrollo seguro |
| `g-e-identify-technical-debt` | Ya disponible | Auditar deuda técnica contra un ASD |
| `g-e-asd-extract` | Ya disponible | Generar el documento de arquitectura del sistema existente |
| `g-e-review-pr` | Ya disponible | Revisar cada PR de las fases |
| `g-e-performance-review` | Ya disponible | Revisar consultas y manejo de conexiones (3.5) |
| `daxia-git-workflow` | Ya disponible | Ramas, commits y PRs con el estándar DaXia |
| `secure-container-images` | Ya disponible | Solo si se agrega un `Dockerfile` |
| Skills de la comunidad para FastAPI/Python/pytest | A buscar | Se buscan con `find-skills` (no hay ninguna instalada que sea específica de Python); conviene revisar su origen antes de instalarlas |
