import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from prisma.models import Post, cmsMeta
from prisma.models import author as author_db
from . import meta as kokoromi
from .func import convert_to_jst

app = APIRouter(prefix="/authors")

templates = Jinja2Templates(directory="templates")
templates.env.filters['to_jst'] = convert_to_jst

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

@app.get("/{author_id}", response_class=HTMLResponse)
async def read_author(request: Request, author_id: str):
    page = int(request.query_params.get("page", 1))
    author = await author_db.prisma().find_first(where={"id": author_id})
    if not author:
        return templates.TemplateResponse(
            "404.html",
            {
                "request": request,
                "settings": await load_settings(),
                "kokoromi": kokoromi,
            },
            status_code=404,
        )

    recent_articles = await Post.prisma().find_many(order={"createdAt": "desc"}, take=5)

    total_articles = await Post.prisma().count(
        where={
            "id": author_id,
        }
    )
    num_pages = (total_articles + ARTICLES_PER_PAGE - 1) // ARTICLES_PER_PAGE
    start_index = (page - 1) * ARTICLES_PER_PAGE
    end_index = start_index + ARTICLES_PER_PAGE

    articles = await Post.prisma().find_many(
        where={"authorId": author_id, "draft": False},
        order={"createdAt": "desc"},
        skip=start_index,
        take=ARTICLES_PER_PAGE,
        include={"author": True},
    )

    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if end_index < total_articles else None

    return templates.TemplateResponse(
        request=request,
        name="author.html",
        context={
            "page_url": str(request.url),
            "year": datetime.date.today().year,
            "author": author,
            "author_icon": author.icon if author.icon else "",
            "num_pages": num_pages,
            "prev_page": prev_page,
            "next_page": next_page,
            "articles": articles,
            "recent_articles": recent_articles,
            "kokoromi": kokoromi,
            "settings": await load_settings(),
        },
    )