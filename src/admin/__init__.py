from fastapi import APIRouter, Cookie, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from prisma.models import Token

from .admin import get_current_user

from . import articles, login, settings, author

app = APIRouter(prefix="/admin")
app.include_router(articles.app)
app.include_router(login.app)
app.include_router(settings.app)
app.include_router(author.app)

templates = Jinja2Templates(directory="templates/admin")

@app.get("/", response_class=HTMLResponse, name="admin_dashboard")
async def admin_dashboard(request: Request, Authorization: str | None = Cookie(default=None)):
    if Authorization is None:
        return RedirectResponse(url="/login", status_code=303)
    verify = await get_current_user(Authorization)
    if not verify:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/authors", response_class=HTMLResponse, name="authors")
async def list_authors(request: Request, Authorization: str | None = Cookie(default=None)):
    verify = await get_current_user(Authorization)
    if not verify:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
    return templates.TemplateResponse("authors.html", {"request": request})

@app.get("/about", response_class=HTMLResponse, name="about")
async def about(request: Request, Authorization: str | None = Cookie(default=None)):
    verify = await get_current_user(Authorization)
    if not verify:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
    return templates.TemplateResponse(
        "about.html", {"request": request}
    )
    
@app.get("/logout", response_class=HTMLResponse, name="logout")
async def logout(request: Request, Authorization: str | None = Cookie(default=None)):
    await get_current_user(Authorization)
    await Token.prisma().delete(
        where={
            "token": Authorization
        }
    )
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(key="Authorization", httponly=True)
    return response