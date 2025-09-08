from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from services.auth_service import AuthService
from api.auth.schemas import LoginRequest, TokenResponse, TokenRefreshRequest
router = APIRouter(prefix="/api", tags=["Auth"])

@router.post("/token", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await AuthService.authenticate_user(db, data.username, data.password)


@router.post("/token/refresh")
async def refresh_token(request: TokenRefreshRequest):
    return await AuthService.refresh_token(request)