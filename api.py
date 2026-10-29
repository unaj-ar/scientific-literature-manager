from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse  # <-- 1. Agregar esta importación
from pydantic import BaseModel
from typing import Optional
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
    return FileResponse("index.html")

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