from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from utils.security import create_access_token, create_refresh_token, verify_password, authenticate_user
from core.settings import settings

# Для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 схема
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/token/")

# Фейковая база пользователей
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"),
    }
}

# ==========================
# Pydantic схемы
# их задача валидировать входящие/исходящие данные API в FastAPI
# ==========================
"""
class Token(BaseModel)
Используется как ответ API после успешного логина.
FastAPI благодаря response_model=Token автоматически проверяет и документирует, что эндпоинт должен вернуть объект с полями:
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token"
}

class TokenRefreshRequest(BaseModel)
Используется для входящих данных в эндпоинте /api/token/refresh/.
То есть клиент должен отправить JSON вида:
{
  "refresh": "jwt_refresh_token"
}

class TokenRefreshRequest(BaseModel)
Используется для входящих данных в эндпоинте /api/token/refresh/.
То есть клиент должен отправить JSON вида:
{
  "refresh": "jwt_refresh_token"
}
"""

class Token(BaseModel):
    access: str
    refresh: str

class TokenRefreshRequest(BaseModel):
    refresh: str

class LoginRequest(BaseModel):
    username: str
    password: str


# Router
router = APIRouter()

@router.post("/api/token/", response_model=Token)
async def login(data: LoginRequest):
    user = authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные имя пользователя или пароль"
        )

    access_token = create_access_token({"sub": user["username"]})
    refresh_token = create_refresh_token({"sub": user["username"]})

    return {"access": access_token, "refresh": refresh_token}


@router.post("/api/token/refresh/")
async def refresh_token(request: TokenRefreshRequest):
    try:
        payload = jwt.decode(
            request.refresh,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        if payload.get("scope") != "refresh_token":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный refresh токен")

        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недействительный refresh токен")

        new_access_token = create_access_token({"sub": username})
        return {"access": new_access_token, "refresh": request.refresh}

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Невалидный refresh токен")