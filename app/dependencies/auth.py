import datetime
from enum import StrEnum

from fastapi import Depends, HTTPException, Request
import jwt
from pydantic import BaseModel

from core.settings import get_settings
from core.settings.base import Settings


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class UserInfo(BaseModel):
    user_id: str
    admin: bool


class TokenPayload(UserInfo):
    exp: datetime.datetime
    type: TokenType


def get_current_user(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> UserInfo:
    token = request.headers.get("Authorization")

    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")

    parsed_token = token.removeprefix("Bearer ")

    try:
        decoded = jwt.decode(
            parsed_token,
            key=settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        payload = TokenPayload.model_validate(decoded)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    if payload.type != TokenType.ACCESS:
        raise HTTPException(status_code=401, detail="Invalid token type")

    return UserInfo(**payload.model_dump())
