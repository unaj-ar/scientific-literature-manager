from typing import Optional


class AppError(Exception):
    """Business error with the HTTP status the API should answer with."""

    status_code = 400
    default_detail = "Solicitud inválida."

    def __init__(self, detail: Optional[str] = None):
        self.detail = detail or self.default_detail
        super().__init__(self.detail)


class InvalidDataError(AppError):
    status_code = 400


class NotFoundError(AppError):
    status_code = 404
    default_detail = "El recurso no existe."


class ConflictError(AppError):
    status_code = 409
    default_detail = "El recurso ya existe."
