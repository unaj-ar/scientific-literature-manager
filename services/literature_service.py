from repository.article_repository import ArticleRepository


class LiteratureService:
    def __init__(self):
        self.repository = ArticleRepository()
        self.VALID_PRIORITIES = {'P1': 'P1', 'P2': 'P2', 'P3': 'P3'}
        self.STATUS_MAP = {
            'unread': 'Unread',
            'in progress': 'In Progress',
            'in progres': 'In Progress',
            'read': 'Read',
            'archived': 'Archived'
        }

    def register_new_article(self, title, authors_raw, year_raw, doi, priority_raw, status_raw, tags, pdf_path, notes):
        """Valida entradas y registra un nuevo artículo en la BD."""
        if not title.strip():
            raise ValueError("El título no puede estar vacío.")

        # Limpieza de datos
        year = int(year_raw) if str(year_raw).isdigit() else None
        doi_clean = doi.strip() if doi and doi.strip() else None
        priority = self.VALID_PRIORITIES.get(priority_raw.strip().upper(), 'P2')
        status = self.STATUS_MAP.get(status_raw.strip().lower(), 'Unread')

        authors_list = [a.strip() for a in authors_raw.split(',') if a.strip()]

        return self.repository.create_article(
            title, year, doi_clean, priority, status, tags, pdf_path, notes, authors_list
        )

    @staticmethod
    def _page(rows: list, total: int, page: int, page_size: int) -> dict:
        return {"items": rows, "total": total, "page": page, "page_size": page_size}

    def fetch_prioritized_list(self, page: int = 1, page_size: int = 20) -> dict:
        rows, total = self.repository.get_by_priority(page_size, (page - 1) * page_size)
        return self._page(rows, total, page, page_size)

    def fetch_articles_by_author(self, author_name: str, page: int = 1, page_size: int = 20) -> dict:
        if not author_name.strip():
            return self._page([], 0, page, page_size)
        rows, total = self.repository.get_by_author(author_name, page_size, (page - 1) * page_size)
        return self._page(rows, total, page, page_size)
