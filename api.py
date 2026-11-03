from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse  # <-- 1. Agregar esta importación
from pydantic import BaseModel
from typing import Optional
from services.auth_service import get_current_user

from starlette import status

from repository import user_repository
from services import user_service
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

# --- 2. AGREGAR ESTA RUTA ---
@app.get("/")
def read_root():
    """Servir la página index.html al entrar a la raíz"""
    return FileResponse("ui/login.html")

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
def get_articles():
    """Obtiene la lista priorizada de artículos."""
    return service.fetch_prioritized_list()

@app.get("/articles/author/{author_name}")
def get_articles_by_author(author_name: str):
    """Consulta artículos filtrados por autor."""
    return service.fetch_articles_by_author(author_name)

@app.post("/articles")
def create_article(article: ArticleSchema):
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


@app.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_user(
    user_id: int,
    current_user: str = Depends(get_current_user)
):
    """Endpoint para baja lógica de usuario."""
    return user_service.deactivate_user(user_id=user_id, current_user_id=current_user["id"])


@app.patch("/users/{user_id}/restore", status_code=status.HTTP_200_OK)
def restore_user(
    user_id: int,
    current_user: str = Depends(get_current_user)
):
    """Endpoint opcional para reactivar una entidad."""
    success = user_repository.restore(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o ya activo.")
    return {"message": f"Usuario {user_id} reactivado con éxito."}