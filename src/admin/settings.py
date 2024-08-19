from fastapi import APIRouter, Cookie, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi import Depends
from prisma.models import author, cmsMeta

from .admin import get_current_user

app = APIRouter(prefix="/settings")
templates = Jinja2Templates(directory="templates/admin")


@app.get("/", response_class=HTMLResponse, name="settings")
async def settings(request: Request, Authorization: str | None = Cookie(default=None)):
    verify = await get_current_user(Authorization)
    if verify is False:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
    setting = await cmsMeta.prisma().find_first()
    if setting is None:
        setting = await cmsMeta.prisma().create(
            data={
                "id": 1,
                "title": "Sample Blog",
                "description": "Sample Blog. Built with Kokoromi CMS.",
                "hideKokoromiVersion": False,
                "noindex": False,
                "disallowAiLearning": False,
            }
        )
    return templates.TemplateResponse(
        "settings.html",
        {
            "request": request,
            "settings": setting,
            "changed": False,
        },
    )


@app.post("/")
async def update(
    request: Request,
    Authorization: str | None = Cookie(default=None),
    site_name: str = Form(...),
    site_description: str = Form(""),
    disable_ai_learning: bool = Form(False),
    hide_kokoromi_version: bool = Form(False),
    disable_search_indexing: bool = Form(False),
    enable_giscus: bool = Form(False),
    giscusRepo: str = Form(None),
    giscusRepoId: str = Form(None),
    giscusCategoryName: str = Form(None),
    giscusCategoryId: str = Form(None),
    giscusThemeType: str = Form(...),
    enable_activitypub: bool = Form(False),
    adsense: str = Form(None),
    ga4TrackingId: str = Form(None),
    showViewCounts: bool = Form(False),
):
    verify = await get_current_user(Authorization)
    if verify is False:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
    if await cmsMeta.prisma().find_first(where={"id": 1}) is None:
        setting: cmsMeta = await cmsMeta.prisma().create(
            data={
                "id": 1,
                "title": site_name,
                "description": site_description,
                "disallowAiLearning": disable_ai_learning,
                "hideKokoromiVersion": hide_kokoromi_version,
                "noindex": disable_search_indexing,
                "giscusEnabled": enable_giscus,
                "giscusRepo": giscusRepo,
                "giscusRepoId": giscusRepoId,
                "giscusCategoryName": giscusCategoryName,
                "giscusCategoryId": giscusCategoryId,
                "giscusThemeType": giscusThemeType,
                "enableActivityPub": enable_activitypub,
                "adsense": adsense,
                "ga4TrackingId": ga4TrackingId,
                "showViewCounts": showViewCounts
            }
        )
    else:
        setting: cmsMeta = await cmsMeta.prisma().update(
            where={"id": 1},
            data={
                "title": site_name,
                "description": site_description,
                "disallowAiLearning": disable_ai_learning,
                "hideKokoromiVersion": hide_kokoromi_version,
                "noindex": disable_search_indexing,
                "giscusEnabled": enable_giscus,
                "giscusRepo": giscusRepo,
                "giscusRepoId": giscusRepoId,
                "giscusCategoryName": giscusCategoryName,
                "giscusCategoryId": giscusCategoryId,
                "giscusThemeType": giscusThemeType,
                "enableActivityPub": enable_activitypub,
                "adsense": adsense,
                "ga4TrackingId": ga4TrackingId,
                "showViewCounts": showViewCounts
            },
        )

    return templates.TemplateResponse(
        name="settings.html",
        context={
            "request": request,
            "settings": setting,
            "changed": True
        },
    )