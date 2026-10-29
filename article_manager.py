import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    try:
        connection = psycopg2.connect(
            host='localhost',
            port='5432',
            user='postgres',  # Tu usuario
            password='password',  # Tu contraseña
            database='database_revision'
        )
        return connection
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None


def get_or_create_author_id(cursor, author_name):
    """Obtiene el ID del autor si existe; si no, lo inserta y retorna el nuevo ID."""
    name_clean = author_name.strip()
    if not name_clean:
        return None

    # Buscar si ya existe
    cursor.execute("SELECT id FROM authors WHERE name ILIKE %s;", (name_clean,))
    result = cursor.fetchone()
    if result:
        return result['id']

    # Si no existe, crearlo
    cursor.execute("INSERT INTO authors (name) VALUES (%s) RETURNING id;", (name_clean,))
    return cursor.fetchone()['id']


def add_article():
    """Registra un nuevo artículo asociando múltiples autores en la tabla de relaciones."""
    print("\n--- ADD NEW ARTICLE ---")
    title = input("Title: ")
    authors_input = input("Authors (separated by comma, e.g., 'John Doe, Jane Smith'): ")
    year = input("Publication Year: ")
    doi = input("DOI: ")

    # Validación Priority
    VALID_PRIORITIES = {'P1': 'P1', 'P2': 'P2', 'P3': 'P3'}
    raw_priority = input("Priority (P1=High, P2=Medium, P3=Low) [P2]: ").strip().upper()
    priority = VALID_PRIORITIES.get(raw_priority, 'P2')

    # Validación Status
    STATUS_MAP = {
        'unread': 'Unread',
        'in progress': 'In Progress',
        'in progres': 'In Progress',
        'read': 'Read',
        'archived': 'Archived'
    }
    raw_status = input("Status (Unread, In Progress, Read, Archived) [Unread]: ").strip().lower()
    status = STATUS_MAP.get(raw_status, 'Unread')

    tags = input("Tags (comma-separated): ")
    pdf_path = input("PDF Path or Link: ")
    notes = input("Initial Notes / Summary: ")

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 1. Insertar el artículo y retornar el ID generado
            insert_article_query = """
            INSERT INTO articles (title, publication_year, doi, priority, status, tags, pdf_path, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;
            """
            values = (
                title,
                int(year) if year.isdigit() else None,
                doi if doi else None,
                priority,
                status,
                tags,
                pdf_path,
                notes
            )
            cursor.execute(insert_article_query, values)
            article_id = cursor.fetchone()['id']

            # 2. Procesar los autores y vincularlos en article_authors
            if authors_input:
                author_names = [a.strip() for a in authors_input.split(',') if a.strip()]
                for name in author_names:
                    author_id = get_or_create_author_id(cursor, name)
                    if author_id:
                        cursor.execute(
                            "INSERT INTO article_authors (article_id, author_id) VALUES (%s, %s) ON CONFLICT DO NOTHING;",
                            (article_id, author_id)
                        )

            conn.commit()
            print("✅ Article and author relations successfully saved.")
        except Exception as e:
            conn.rollback()
            print(f"⚠️ Error inserting article: {e}")
        finally:
            cursor.close()
            conn.close()


def get_articles_by_author():
    """Consulta y lista todos los artículos asociados a un autor específico."""
    print("\n--- GET ARTICLES BY AUTHOR ---")
    author_name = input("Enter author's name: ").strip()

    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            query = """
            SELECT a.id, a.title, a.publication_year, a.priority, a.status, a.doi, a.pdf_path
            FROM articles a
            JOIN article_authors aa ON a.id = aa.article_id
            JOIN authors au ON aa.author_id = au.id
            WHERE au.name ILIKE %s
            ORDER BY a.publication_year DESC;
            """
            cursor.execute(query, (f"%{author_name}%",))
            articles = cursor.fetchall()

            if not articles:
                print(f"No articles found for author matching: '{author_name}'")
            else:
                print(f"\nFound {len(articles)} article(s) for '{author_name}':")
                for art in articles:
                    print("-" * 50)
                    print(f"ID: {art['id']} | [{art['priority']}] {art['title']} ({art['publication_year'] or 'N/A'})")
                    print(f"Status: {art['status']} | DOI: {art['doi']}")
                    print(f"PDF Link: {art['pdf_path']}")

        except Exception as e:
            print(f"⚠️ Error querying articles: {e}")
        finally:
            cursor.close()
            conn.close()


def list_by_priority():
    """Prioritization: Fetches and displays articles ordered by priority with their authors."""
    print("\n--- PRIORITIZED READING LIST ---")
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            query = """
            SELECT a.id, a.title, a.priority, a.status, a.tags,
                   STRING_AGG(au.name, ', ') AS authors
            FROM articles a
            LEFT JOIN article_authors aa ON a.id = aa.article_id
            LEFT JOIN authors au ON aa.author_id = au.id
            GROUP BY a.id
            ORDER BY a.priority ASC, a.created_at DESC;
            """
            cursor.execute(query)
            articles = cursor.fetchall()

            if not articles:
                print("No articles registered yet.")
            else:
                for art in articles:
                    authors_str = art['authors'] if art['authors'] else 'No authors'
                    print(
                        f"[{art['priority']}] ID: {art['id']} | {art['title']} | Authors: {authors_str} | Status: {art['status']}")
        except Exception as e:
            print(f"⚠️ Error: {e}")
        finally:
            cursor.close()
            conn.close()


def main():
    while True:
        print("\n=== SCIENTIFIC LITERATURE MANAGER ===")
        print("1. Add Article (Discovery)")
        print("2. View Priority List (Prioritization)")
        print("3. Get Articles by Author")
        print("4. Exit")

        choice = input("Select an option (1-4): ")
        if choice == '1':
            add_article()
        elif choice == '2':
            list_by_priority()
        elif choice == '3':
            get_articles_by_author()
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Invalid option. Please try again.")


if __name__ == '__main__':
    main()