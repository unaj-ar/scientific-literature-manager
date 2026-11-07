from fastapi import HTTPException, status

from services.auth_service import AuthService
from services.permissions import ADMIN, RESEARCHER, ROLES


class UserService:
    def __init__(self, user_repository):
        self.user_repo = user_repository

    def register(self, username: str, email: str, password: str, role: str = RESEARCHER) -> dict:
        """Crea un usuario nuevo guardando solo el hash de la contraseña."""
        if role not in ROLES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rol inválido.")
        if self.user_repo.exists(username, email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El usuario o el email ya están registrados."
            )
        user_id = self.user_repo.create(username, email, AuthService.hash_password(password), role)
        return {"id": user_id, "username": username, "email": email, "role": role}

    def authenticate(self, username: str, password: str) -> dict:
        """Valida credenciales y retorna un token JWT. El error no revela qué dato falló."""
        user = self.user_repo.get_by_username(username)
        if (
            not user
            or not user["is_active"]
            or not AuthService.verify_password(password, user["hashed_password"])
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario o contraseña incorrectos.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        token = AuthService.create_access_token({"sub": user["username"], "user_id": user["id"]})
        return {"access_token": token, "token_type": "bearer", "role": user["role"]}

    def deactivate_user(self, user_id: int, current_user_id: int) -> dict:
        """Ejecuta la regla de negocio para dar de baja a un usuario."""
        # Regla de negocio: un usuario no puede darse de baja a sí mismo
        if user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes desactivar tu propia cuenta activa desde esta sesión."
            )

        target = self.user_repo.get_by_id(user_id)
        if (
            target
            and target["role"] == ADMIN
            and target["is_active"]
            and self.user_repo.count_active_admins() <= 1
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede dar de baja al último administrador activo."
            )

        success = self.user_repo.soft_delete(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no existe o ya ha sido dado de baja."
            )

        return {"message": f"Usuario {user_id} dado de baja exitosamente."}

    def restore_user(self, user_id: int) -> dict:
        """Reactiva un usuario dado de baja."""
        if not self.user_repo.restore(user_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado o ya activo."
            )
        return {"message": f"Usuario {user_id} reactivado con éxito."}

    def list_users(self) -> list:
        return self.user_repo.list_all()

    def change_role(self, user_id: int, role: str, current_user_id: int) -> dict:
        """Cambia el rol de un usuario, protegiendo la cuenta propia y al último admin."""
        if role not in ROLES:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Rol inválido.")
        if user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes cambiar tu propio rol."
            )
        target = self.user_repo.get_by_id(user_id)
        if not target:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El usuario no existe.")
        if (
            target["role"] == ADMIN
            and role != ADMIN
            and target["is_active"]
            and self.user_repo.count_active_admins() <= 1
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Debe quedar al menos un administrador activo."
            )
        self.user_repo.set_role(user_id, role)
        return {"message": f"Rol de usuario {user_id} actualizado a {role}."}
