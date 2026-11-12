# Despliegue en Render

## Qué falló
El servicio arrancaba con `gunicorn run:app` y fallaba con `gunicorn: command not found` (código 127). Había dos problemas:

1. `gunicorn` no está en `requirements.txt`.
2. El comando no corresponde a esta app: no existe `run.py` y la app es **FastAPI (ASGI)**, expuesta como `api:app`. `gunicorn run:app` es un patrón de Flask.

## Arranque correcto
```bash
uvicorn api:app --host 0.0.0.0 --port $PORT
```
`uvicorn` ya está en `requirements.txt`. Render inyecta `$PORT`. No se usa `--reload`.

## Opción A — Blueprint (`render.yaml`)
El repo incluye `render.yaml`. En Render: **New → Blueprint**, elegir el repo y completar las variables marcadas `sync: false`.

## Opción B — Servicio ya creado (panel de Render)
Ir al servicio → **Settings** y cambiar:

| Campo | Valor |
|---|---|
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn api:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/login.html` |

Luego **Manual Deploy → Deploy latest commit**.

## Variables de entorno
| Variable | Valor |
|---|---|
| `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` | Los de una PostgreSQL accesible desde Render |
| `SECRET_KEY` | Texto largo y aleatorio (el blueprint lo genera). Si se cambia, se invalidan las sesiones |
| `PYTHON_VERSION` | `3.12.7` (el CI prueba 3.10 a 3.12) |

La base local (Docker) **no** es alcanzable desde Render. Hace falta una PostgreSQL pública o la de Render (en el plan gratuito caduca a los 30 días).

## Base de datos (una sola vez)
Render no ejecuta las migraciones. Desde tu equipo, con la cadena de conexión **externa** de la base:

```bash
psql "<URL_EXTERNA>" -f scripts/V002.sql
psql "<URL_EXTERNA>" -f scripts/V003.sql
psql "<URL_EXTERNA>" -f scripts/V004.sql
```

(`V001.sql` es el esquema antiguo: no se aplica.) Después, crear el primer administrador apuntando `.env` local a esa base:

```bash
python -m scripts.create_admin --username <usuario> --email <email>
```

## Verificación
- Los logs deben mostrar `Uvicorn running on http://0.0.0.0:<puerto>`.
- `https://<servicio>.onrender.com/` muestra el login y `/docs` el Swagger.

## Pendientes de seguridad antes de exponerlo
- CORS está abierto a cualquier origen (`allow_origins=["*"]`).
- `SECRET_KEY` tiene un valor por defecto inseguro en el código si falta la variable.
- La CLI (`main.py`) no se despliega y no tiene autenticación.
