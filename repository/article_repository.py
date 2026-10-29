from config.database import get_connection
from psycopg2.extras import RealDictCursor


class ArticleRepository:

    def get_or_create_author(self, cursor, author_name: str) -> int:
        """Obtiene el ID de un autor o lo crea si no existe."""
        name_clean = author_name.strip()
        cursor.execute("SELECT id FROM authors WHERE name ILIKE %s;", (name_clean,))
        result = cursor.fetchone()
        if result:
            return result['id']

        cursor.execute("INSERT INTO authors (name) VALUES (%s) RETURNING id;", (name_clean,))
        return cursor.fetchone()['id']

    def create_article(self, title, year, doi, priority, status, tags, pdf_path, notes, authors_list) -> int:
        """Inserta un artículo y sus relaciones con autores dentro de una transacción."""
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 1. Insertar artículo
                query = """
                INSERT INTO articles (title, publication_year, doi, priority, status, tags, pdf_path, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
                """
                cursor.execute(query, (title, year, doi, priority, status, tags, pdf_path, notes))
                article_id = cursor.fetchone()['id']

                # 2. Insertar autores y mapear relación N:M
                for name in authors_list:
                    author_id = self.get_or_create_author(cursor, name)
                    cursor.execute(
                        "INSERT INTO article_authors (article_id, author_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                        (article_id, author_id)
                    )
                conn.commit()
                return article_id

    def get_by_priority(self) -> list:
        """Obtiene la lista priorizada de artículos con sus autores agrupados."""
        query = """
        SELECT a.id, a.title, a.priority, a.status, a.tags,
               STRING_AGG(au.name, ', ') AS authors
        FROM articles a
        LEFT JOIN article_authors aa ON a.id = aa.article_id
        LEFT JOIN authors au ON aa.author_id = au.id
        GROUP BY a.id
        ORDER BY a.priority ASC, a.created_at DESC;
        """
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query)
                return cursor.fetchall()

    def get_by_author(self, author_name: str) -> list:
        """Consulta los artículos escritos por un autor específico."""
        query = """
        SELECT a.id, a.title, a.publication_year, a.priority, a.status, a.doi, a.pdf_path
        FROM articles a
        JOIN article_authors aa ON a.id = aa.article_id
        JOIN authors au ON aa.author_id = au.id
        WHERE au.name ILIKE %s
        ORDER BY a.publication_year DESC;
        """
        with get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (f"%{author_name.strip()}%",))
                return cursor.fetchall()