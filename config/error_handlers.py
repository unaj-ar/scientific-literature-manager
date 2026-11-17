import logging
import time
import uuid
from typing import Optional

import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from psycopg2 import errors as pg_errors

from config.logging_config import request_id_var
from services.exceptions import AppError

logger = logging.getLogger(__name__)
access_logger = logging.getLogger("access")

REQUEST_ID_HEADER = "X-Request-ID"


def _error(status_code: int, detail: str, request: Optional[Request] = None) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None) if request else None
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "request_id": request_id or request_id_var.get()},
    )


def register_middleware_and_handlers(app: FastAPI) -> None:
    """Request id + access log, and global handlers that never leak internal error text."""

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # Unhandled errors are answered by the handler below; log the access line first.
            access_logger.info("%s %s -> 500 (%.0f ms)", request.method, request.url.path,
                               (time.perf_counter() - started) * 1000)
            raise
        else:
            response.headers[REQUEST_ID_HEADER] = request_id
            access_logger.info("%s %s -> %s (%.0f ms)", request.method, request.url.path, response.status_code,
                               (time.perf_counter() - started) * 1000)
            return response
        finally:
            request_id_var.reset(token)

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        logger.info("Business error %s: %s", exc.status_code, exc.detail)
        return _error(exc.status_code, exc.detail, request)

    @app.exception_handler(pg_errors.UniqueViolation)
    async def unique_violation_handler(request: Request, exc: pg_errors.UniqueViolation):
        logger.warning("Unique violation: %s", exc)
        return _error(409, "El recurso ya existe.", request)

    @app.exception_handler(psycopg2.OperationalError)
    async def db_unavailable_handler(request: Request, exc: psycopg2.OperationalError):
        logger.error("Database unavailable: %s", exc)
        return _error(503, "Servicio no disponible. Intenta de nuevo en unos instantes.", request)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error: %s", exc)
        return _error(500, "Error interno del servidor.", request)
