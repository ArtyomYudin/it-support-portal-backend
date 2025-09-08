from datetime import timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Optional

from utils.security import create_access_token, create_refresh_token, fake_user_db, verify_password
from core.settings import settings
from api.auth.schemas import TokenResponse, TokenRefreshRequest
from db.models.core import CoreUser

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    async def _get_user_by_username(db: AsyncSession, username: str) ->Optional[CoreUser]:
        result = await db.execute(select(CoreUser).where(CoreUser.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def authenticate_user(db: AsyncSession, username: str, password: str) -> TokenResponse:
        user = await AuthService._get_user_by_username(db, username)
        # user = fake_user_db.get(username)
        if not user or not verify_password(password, user.password_hash):

        # if not user or not pwd_context.verify(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Неверное имя пользователя или пароль"
            )

        access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)

        access = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
        refresh = create_refresh_token(data={"sub": user.username}, expires_delta=refresh_token_expires)

        return TokenResponse(access=access, refresh=refresh)

    @staticmethod
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
