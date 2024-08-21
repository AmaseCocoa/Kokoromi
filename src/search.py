from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from prisma.models import Post, cmsMeta
from . import meta as kokoromi
from .func import convert_to_jst

app = APIRouter()

templates = Jinja2Templates(directory="templates")
templates.env.filters['to_jst'] = convert_to_jst

ARTICLES_DIR = "articles"
AUTHORS_FILE = "authors.json"
ARTICLES_PER_PAGE = 5


async def load_settings() -> cmsMeta:
    setting = await cmsMeta.prisma().find_first(where={"id": 1})
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
    return setting

@app.get("/search", response_class=HTMLResponse)
async def search_articles(request: Request, text: str):
    page = int(request.query_params.get("page", 1))

    skip = (page - 1) * ARTICLES_PER_PAGE

    results = await Post.prisma().find_many(
        where={
            "OR": [
                {"title": {"contains": text}},
                {"content": {"contains": text}},
            ],
            "draft": False
        },
        order={"createdAt": "desc"},
        skip=skip,
        take=ARTICLES_PER_PAGE,
        include={"author": True},
    )

    total_results = await Post.prisma().count(
        where={
            "OR": [
                {"title": {"contains": text}},
                {"content": {"contains": text}},
            ]
        },
    )

    total_pages = (total_results + ARTICLES_PER_PAGE - 1) // ARTICLES_PER_PAGE
    page_range = range(1, total_pages + 1)

    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if page < total_pages else None

    return templates.TemplateResponse(
        "search.html",
        {
            "request": request,
            "results": results,
            "query": text,
            "current_page": page,
            "page_range": page_range,
            "prev_page": prev_page,
            "next_page": next_page,
            "settings": await load_settings(),
            "kokoromi": kokoromi,
        },
    )