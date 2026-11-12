from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse  # <-- 1. Agregar esta importación
from pydantic import BaseModel, Field
from typing import Literal, Optional
from services.auth_service import get_current_user

from starlette import status

from config.database import get_db
from repository.user_repository import UserRepository
from services.permissions import ARTICLES_CREATE, ARTICLES_READ, USERS_MANAGE, has_permission, permissions_for
from services.user_service import UserService
from services.literature_service import LiteratureService

app = FastAPI(title="Scientific Literature Manager API")

# Permitir CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service = LiteratureService()

def get_user_repository(conn=Depends(get_db)) -> UserRepository:
    return UserRepository(conn)


def get_user_service(repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(repo)


def require_permission(permission: str):
    """Dependencia que valida el token y que el rol vigente en la BD tenga el permiso.

    Se consulta la BD en cada request para que bajas y cambios de rol apliquen al instante.
    """
    def checker(
        current_user: dict = Depends(get_current_user),
        repo: UserRepository = Depends(get_user_repository),
    ) -> dict:
        user = repo.get_by_id(current_user["id"])
        if not user or not user["is_active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido o expirado",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if not has_permission(user["role"], permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tienes permiso para esta acción.")
        return user

    return checker


@app.get("/")
@app.get("/login.html")
def read_root():
    """Sirve la pantalla de login."""
    return FileResponse("ui/login.html")


@app.get("/admin.html")
def read_admin():
    """Sirve la consola de administración (la API valida los permisos en cada llamada)."""
    return FileResponse("ui/admin.html")


@app.get("/index.html")
def read_index():
    """Sirve la aplicación principal (la página valida el token en el cliente)."""
    return FileResponse("ui/index.html")


class RegisterSchema(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=5, max_length=100, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8, max_length=128)


class AdminCreateUserSchema(RegisterSchema):
    role: Literal["admin", "researcher"] = "researcher"


class RoleSchema(BaseModel):
    role: Literal["admin", "researcher"]


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: RegisterSchema, users: UserService = Depends(get_user_service)):
    """Auto-registro público: siempre crea un investigador."""
    return users.register(data.username, data.email, data.password)


@app.get("/me")
def me(user: dict = Depends(require_permission(ARTICLES_READ))):
    """Datos y permisos del usuario autenticado."""
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "permissions": permissions_for(user["role"]),
    }


@app.post("/login")
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    users: UserService = Depends(get_user_service)
):
    """Autentica con usuario y contraseña (form data) y devuelve un JWT."""
    return users.authenticate(form.username, form.password)

# Modelo de datos de entrada para la API
class ArticleSchema(BaseModel):
    title: str
    authors: str
    publication_year: Optional[str] = None
    doi: Optional[str] = None
    priority: Optional[str] = "P2"
    status: Optional[str] = "Unread"
    tags: Optional[str] = ""
    pdf_path: Optional[str] = ""
    notes: Optional[str] = ""

@app.get("/articles")
def get_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _user: dict = Depends(require_permission(ARTICLES_READ)),
):
    """Obtiene una página de la lista priorizada de artículos."""
    return service.fetch_prioritized_list(page, page_size)

@app.get("/articles/author/{author_name}")
def get_articles_by_author(
    author_name: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _user: dict = Depends(require_permission(ARTICLES_READ)),
):
    """Consulta una página de artículos filtrados por autor."""
    return service.fetch_articles_by_author(author_name, page, page_size)

@app.post("/articles")
def create_article(article: ArticleSchema, _user: dict = Depends(require_permission(ARTICLES_CREATE))):
    """Guarda un nuevo artículo en la base de datos PostgreSQL."""
    try:
        article_id = service.register_new_article(
            title=article.title,
            authors_raw=article.authors,
            year_raw=article.publication_year,
            doi=article.doi,
            priority_raw=article.priority,
            status_raw=article.status,
            tags=article.tags,
            pdf_path=article.pdf_path,
            notes=article.notes
        )
        return {"status": "success", "article_id": article_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users")
def list_users(
    _admin: dict = Depends(require_permission(USERS_MANAGE)),
    users: UserService = Depends(get_user_service)
):
    """Lista todos los usuarios (solo administradores)."""
    return users.list_users()


@app.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(
    data: AdminCreateUserSchema,
    _admin: dict = Depends(require_permission(USERS_MANAGE)),
    users: UserService = Depends(get_user_service)
):
    """Crea un usuario con el rol indicado (solo administradores)."""
    return users.register(data.username, data.email, data.password, data.role)


@app.patch("/users/{user_id}/role")
def change_user_role(
    user_id: int,
    data: RoleSchema,
    admin: dict = Depends(require_permission(USERS_MANAGE)),
    users: UserService = Depends(get_user_service)
):
    """Cambia el rol de un usuario (solo administradores)."""
    return users.change_role(user_id, data.role, admin["id"])


@app.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    admin: dict = Depends(require_permission(USERS_MANAGE)),
    users: UserService = Depends(get_user_service)
):
    """Baja lógica de usuario (solo administradores)."""
    return users.deactivate_user(user_id=user_id, current_user_id=admin["id"])


@app.patch("/users/{user_id}/restore", status_code=status.HTTP_200_OK)
def restore_user(
    user_id: int,
    _admin: dict = Depends(require_permission(USERS_MANAGE)),
    users: UserService = Depends(get_user_service)
):
    """Reactiva un usuario dado de baja (solo administradores)."""
    return users.restore_user(user_id)
