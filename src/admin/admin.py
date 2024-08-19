import datetime

from fastapi import HTTPException, status
from pydantic import BaseModel
from prisma.models import author, Token

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440
SECRET_KEY = "your_secret_key"

class User(BaseModel):
    username: str
    full_name: str | None = None
    disabled: bool | None = None

class TokenData(BaseModel):
    username: str | None = None

async def get_current_user(token: str) -> author:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials"
    )
    if token is None:
        raise credentials_exception
    token: Token = await Token.prisma().find_first(where={
        'token': token
    })
    now = datetime.datetime.now(datetime.UTC)
    if now > token.expiresAt:
        await Token.prisma().delete(
            where={
                "token": token
            }
        )
        raise credentials_exception
    user = await author.prisma().find_first(where={"id": token.authorId})
    if user is None:
        raise credentials_exception
    return user