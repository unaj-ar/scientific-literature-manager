# Plan — Docker, logs y manejo de errores

Rama: `fase2` (sale de `main`, que ya incluye la paginación de `fase1`).
Estado: **implementado en la rama**; Docker sin probar con el daemon (ver "Pendiente").

## 1. Docker

| Archivo | Qué hace |
|---|---|
| `Dockerfile` | `python:3.12-slim`, usuario sin privilegios, copia solo el código necesario, `HEALTHCHECK` sobre `/login.html`, arranca con `uvicorn api:app --port ${PORT:-8000}` (compatible con Render). |
| `.dockerignore` | Excluye `.git`, `venv`, `.env`, `tests`, `docs`. |
| `docker-compose.yml` | `db` (PostgreSQL 16 con volumen y `pg_isready`) y `api` (espera a que la BD esté sana). Aplica `V002`→`V003`→`V004` en el primer arranque del volumen. |
| `.env.example` | Variables necesarias, sin valores reales. |

Uso: `cp .env.example .env` (completar `DB_PASSWORD` y `SECRET_KEY`), `docker compose up --build`, luego crear el admin con
`docker compose exec api python -m scripts.create_admin --username <u> --email <e>`.

## 2. Logs

- `config/logging_config.py`: `LOG_LEVEL` (por defecto `INFO`) y `LOG_FORMAT` (`text` o `json`; compose usa `json`). Salida por stdout.
- Cada request recibe un `X-Request-ID` (se reutiliza el que mande el cliente) que aparece en todos los logs y en la respuesta.
- Log de acceso: método, ruta, estado y duración. **No** se registran cuerpos, contraseñas ni tokens.

## 3. Manejo de errores

- `services/exceptions.py`: `AppError` (`InvalidDataError` 400, `NotFoundError` 404, `ConflictError` 409).
- `config/error_handlers.py`: handlers globales con formato `{"detail", "request_id"}`:
  - `AppError` → su código.
  - `UniqueViolation` → 409.
  - `OperationalError` (BD caída) → 503.
  - Cualquier otra excepción → 500 genérico; el detalle va solo al log con traza.
- `POST /articles` ya no devuelve `str(e)` al cliente.

## 4. Tests

`tests/test_error_handling.py` (500 sin filtrar texto interno, 409, 503, eco de `X-Request-ID`) y un caso de título vacío en `tests/test_roles.py`. Suite: 38 tests.

## 5. Pendiente (no incluido)

- Probar `docker compose up --build` con el daemon activo.
- Migrar `UserService` de `HTTPException` a `AppError` (hoy funciona con ambos).
- `SECRET_KEY` obligatoria en el código y CORS restringido (Fase 2 del plan de correcciones).
- Reemplazar `datetime.utcnow()` en `auth_service.py`.
- Migraciones automáticas al desplegar en lugar de montar los scripts en `initdb`.
