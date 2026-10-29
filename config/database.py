import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    """Retorna una nueva conexión activa a PostgreSQL."""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "academic_management")
    )