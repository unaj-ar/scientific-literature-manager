from datetime import datetime

from psycopg2.extras import RealDictCursor

class UserRepository:
    def __init__(self, db_connection):
        self.conn = db_connection

    def soft_delete(self, user_id: int) -> bool:
        """Realiza la baja lógica de un usuario cambiando su estado a inactivo."""
        query = """
            UPDATE users 
            SET is_active = FALSE, deleted_at = %s 
            WHERE id = %s AND is_active = TRUE;
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query, (datetime.utcnow(), user_id))
            self.conn.commit()
            return cursor.rowcount > 0

    def restore(self, user_id: int) -> bool:
        """Restaura un usuario previamente dado de baja."""
        query = """
            UPDATE users 
            SET is_active = TRUE, deleted_at = NULL 
            WHERE id = %s AND is_active = FALSE;
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query, (user_id,))
            self.conn.commit()
            return cursor.rowcount > 0

    def get_all_active(self) -> list:
        """Obtiene únicamente los usuarios que están activos."""
        query = "SELECT id, username, email, is_active FROM users WHERE is_active = TRUE;"
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def get_by_username(self, username: str):
        """Retorna el usuario (dict) por nombre de usuario, o None si no existe."""
        query = """
            SELECT id, username, email, hashed_password, is_active, role
            FROM users WHERE username = %s;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (username,))
            return cursor.fetchone()

    def exists(self, username: str, email: str) -> bool:
        """Indica si ya hay un usuario con ese username o email."""
        query = "SELECT 1 FROM users WHERE username = %s OR email = %s;"
        with self.conn.cursor() as cursor:
            cursor.execute(query, (username, email))
            return cursor.fetchone() is not None

    def get_by_id(self, user_id: int):
        """Retorna el usuario (dict) por id, o None si no existe."""
        query = "SELECT id, username, email, is_active, role FROM users WHERE id = %s;"
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, (user_id,))
            return cursor.fetchone()

    def list_all(self) -> list:
        """Lista todos los usuarios, activos e inactivos (uso del administrador)."""
        query = """
            SELECT id, username, email, role, is_active, created_at, deleted_at
            FROM users ORDER BY id;
        """
        with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            return cursor.fetchall()

    def set_role(self, user_id: int, role: str) -> bool:
        query = "UPDATE users SET role = %s WHERE id = %s;"
        with self.conn.cursor() as cursor:
            cursor.execute(query, (role, user_id))
            self.conn.commit()
            return cursor.rowcount > 0

    def count_active_admins(self) -> int:
        query = "SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = TRUE;"
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchone()[0]

    def create(self, username: str, email: str, hashed_password: str, role: str = "researcher") -> int:
        """Inserta un usuario nuevo y retorna su id."""
        query = """
            INSERT INTO users (username, email, hashed_password, role)
            VALUES (%s, %s, %s, %s) RETURNING id;
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query, (username, email, hashed_password, role))
            user_id = cursor.fetchone()[0]
            self.conn.commit()
            return user_id
