"""Crea un usuario administrador (o promueve uno existente).

Uso, desde la raíz del proyecto:
    python -m scripts.create_admin --username ale --email ale@example.com

La contraseña se pide por consola sin mostrarla; nunca se pasa por argumento.
"""
import argparse
import getpass
import sys

from config.database import get_connection
from repository.user_repository import UserRepository
from services.auth_service import AuthService
from services.permissions import ADMIN


def main() -> int:
    parser = argparse.ArgumentParser(description="Crear o promover un administrador")
    parser.add_argument("--username", default="ale")
    parser.add_argument("--email", help="Requerido si el usuario no existe")
    args = parser.parse_args()

    conn = get_connection()
    try:
        repo = UserRepository(conn)
        existing = repo.get_by_username(args.username)

        if existing:
            repo.set_role(existing["id"], ADMIN)
            if not existing["is_active"]:
                repo.restore(existing["id"])
            print(f"Usuario '{args.username}' existente: ahora es administrador (contraseña sin cambios).")
            return 0

        email = args.email or input("Email: ").strip()
        password = getpass.getpass("Contraseña (mín. 8 caracteres): ")
        if len(password) < 8:
            print("La contraseña debe tener al menos 8 caracteres.", file=sys.stderr)
            return 1
        if password != getpass.getpass("Repetir contraseña: "):
            print("Las contraseñas no coinciden.", file=sys.stderr)
            return 1
        if repo.exists(args.username, email):
            print("Ya existe un usuario con ese email.", file=sys.stderr)
            return 1

        user_id = repo.create(args.username, email, AuthService.hash_password(password), ADMIN)
        print(f"Administrador '{args.username}' creado con id {user_id}.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
