from datetime import datetime

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
            cursor.execute(query, (datetime.utcnow(), user_id))
            self.conn.commit()
            return cursor.rowcount > 0

    def get_all_active(self) -> list:
        """Obtiene únicamente los usuarios que están activos."""
        query = "SELECT id, username, email, is_active FROM users WHERE is_active = TRUE;"
        with self.conn.cursor() as cursor:
            cursor.execute(query)
            return cursor.fetchall()