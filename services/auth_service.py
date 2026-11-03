import os
from datetime import datetime, timedelta
import jwt
from pwdlib import PasswordHash
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

# Configuración de OAuth2 y variables de entorno
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

SECRET_KEY = os.getenv("SECRET_KEY", "super_secret_key_cambiar_en_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_hash = PasswordHash.recommended()


class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Genera el hash seguro de una contraseña."""
        return password_hash.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verifica una contraseña plana contra su hash."""
        return password_hash.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict) -> str:
        """Crea un token de acceso JWT con tiempo de expiración."""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> dict:
        """Decodifica y valida un token JWT."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    Dependencia de FastAPI para obtener y validar el usuario autenticado
    a partir del Token JWT enviado en el header Authorization.
    """
    payload = AuthService.decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Retorna la estructura que espera current_user en api.py
    return {
        "id": payload.get("user_id"),
        "username": payload.get("sub")
    }