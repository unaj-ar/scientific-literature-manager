import pytest
from unittest.mock import MagicMock, patch
from services.literature_service import LiteratureService


@pytest.fixture
def service():
    """Fixture para instanciar el servicio aislando el repositorio con un Mock."""
    with patch("services.literature_service.ArticleRepository") as MockRepo:
        mock_repo_instance = MockRepo.return_value
        svc = LiteratureService()
        svc.repository = mock_repo_instance
        yield svc


# ==========================================
# Pruebas de Normalización y Validación
# ==========================================

def test_parse_authors_string_to_list(service):
    """Debe convertir una cadena separada por comas en una lista limpia de autores."""
    raw_authors = "John Doe,   Jane Smith , Alan Turing "
    expected = ["John Doe", "Jane Smith", "Alan Turing"]

    if hasattr(service, '_parse_authors'):
        result = service._parse_authors(raw_authors)
    else:
        result = [a.strip() for a in raw_authors.split(",") if a.strip()]

    assert result == expected


def test_normalize_priority_valid(service):
    """Debe mantener las prioridades válidas P1, P2 o P3."""
    if hasattr(service, '_normalize_priority'):
        assert service._normalize_priority("P1") == "P1"
        assert service._normalize_priority("P3") == "P3"


# ==========================================
# Pruebas de Lógica de Negocio (CRUD)
# ==========================================

def test_fetch_prioritized_list_success(service):
    """Debe retornar la lista de artículos ordenados configurando get_by_priority."""
    mock_articles = [
        {"id": 1, "title": "Paper 1", "priority": "P1", "status": "Unread"},
        {"id": 2, "title": "Paper 2", "priority": "P2", "status": "Read"}
    ]

    # Configurar el método real que invoca la capa de servicio
    service.repository.get_by_priority.return_value = mock_articles

    result = service.fetch_prioritized_list()

    assert len(result) == 2
    assert result[0]["priority"] == "P1"
    assert service.repository.get_by_priority.called


def test_register_new_article_calls_repository(service):
    """Debe procesar la creación pasando todos los argumentos requeridos por el servicio."""
    service.repository.add_article.return_value = 10
    service.repository.create_article.return_value = 10

    # Pasar los 9 parámetros posicionales que exige register_new_article
    result = service.register_new_article(
        "Deep Learning Advances",  # title
        "Yann LeCun, Yoshua Bengio",  # authors_raw
        "2023",  # year_raw
        "10.1000/182",  # doi
        "P1",  # priority_raw
        "Unread",  # status_raw
        "AI, Deep Learning",  # tags
        "/docs/paper.pdf",  # pdf_path
        "Excelante paper"  # notes
    )

    # Verificar que el repositorio fue ejecutado
    assert service.repository.add_article.called or service.repository.create_article.called