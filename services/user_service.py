from fastapi import HTTPException, status

class UserService:
    def __init__(self, user_repository):
        self.user_repo = user_repository

    def deactivate_user(self, user_id: int, current_user_id: int) -> dict:
        """Ejecuta la regla de negocio para dar de baja a un usuario."""
        # Regla de negocio: Un usuario no puede darse de baja a sí mismo si es el único admin
        if user_id == current_user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes desactivar tu propia cuenta activa desde esta sesión."
            )

        success = self.user_repo.soft_delete(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no existe o ya ha sido dado de baja."
            )

        return {"message": f"Usuario {user_id} dado de baja exitosamente."}