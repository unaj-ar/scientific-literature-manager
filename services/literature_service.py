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

    def fetch_prioritized_list(self):
        return self.repository.get_by_priority()

    def fetch_articles_by_author(self, author_name):
        if not author_name.strip():
            return []
        return self.repository.get_by_author(author_name)