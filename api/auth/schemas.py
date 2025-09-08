from pydantic import BaseModel

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

class TokenResponse(BaseModel):
    access: str
    refresh: str

class TokenRefreshRequest(BaseModel):
    refresh: str

class LoginRequest(BaseModel):
    username: str
    password: str