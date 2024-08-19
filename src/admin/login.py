import datetime
from datetime import timedelta
import secrets

import bcrypt
from fastapi import APIRouter, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import jwt
from pydantic import BaseModel

from prisma.models import author
from prisma.models import Token as token

from .admin import ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, User

app = APIRouter()
templates = Jinja2Templates(directory="templates/admin")



class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None

class UserInDB(User):
    hashed_password: bytes


def verify_password(plain_password, hashed_password):
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password)

async def authenticate_user(username: str, password: str):
    user = await author.prisma().find_first(where={"name": username})
    if not user:
        return False
    if not verify_password(password, user.password.encode("utf-8")):
        return False
    return user


async def create_access_token(authorId: str, expires_delta: timedelta | None = None):
    if expires_delta:
        expire = datetime.datetime.now(datetime.UTC) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.UTC) + timedelta(minutes=1440)
    access_token = secrets.token_hex(16)
    await token.prisma().create(
        data={
            'token': access_token,
            'authorId': authorId,
            'expiresAt': expire
        }
    )
    return access_token


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": False, "username": None, "password": None})


@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    user = await authenticate_user(username, password)
    if not user:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": True, "username": username, "password": password}
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        authorId=user.id, expires_delta=access_token_expires
    )
    response = RedirectResponse(url="/admin", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="Authorization", value=f"{access_token}", httponly=True
    )
    return response
