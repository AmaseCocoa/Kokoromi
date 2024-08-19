from fastapi import APIRouter, Cookie, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Depends
from prisma.models import author

from .admin import get_current_user


app = APIRouter()

templates = Jinja2Templates(directory="templates/admin")


@app.get("/profile", response_class=HTMLResponse, name="profile")
async def profile(request: Request, Authorization: str | None = Cookie(default=None)):
    verify = await get_current_user(Authorization)
    if verify is False:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
    return templates.TemplateResponse("authors.html", {"request": request, "author": verify, "changed": False})

@app.post("/profile", response_class=HTMLResponse, name="profile_update")
async def profile_update(
    request: Request, 
    Authorization: str | None = Cookie(default=None),
    authorName: str = Form(None),
    authorEmail: str = Form(None),
    authorDescription: str = Form(None),
    authorIcon: str = Form(None),
):
    verify = await get_current_user(Authorization)
    if verify is False:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
    upd = {}
    if authorName is not None:
        upd["displayName"] = authorName
    if authorEmail is not None:
        upd["mail"] = authorEmail
    if authorDescription is not None:
        upd["description"] = authorDescription
    if authorIcon is not None:
        upd["icon"] = authorIcon
    ath = await author.prisma().update(
        where={
            "id": verify.id
        },
        data=upd,
    )
    return templates.TemplateResponse("authors.html", {"request": request, "author": ath, "changed": True})