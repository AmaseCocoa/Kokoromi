import datetime
import json
import traceback
from contextlib import asynccontextmanager

import nest_asyncio
import pymdownx.emoji
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Cookie
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from is_bot import Bots
from markdown import markdown

from prisma import Prisma
from prisma.models import Post, cmsMeta
from prisma.models import author as author_db
from src import meta as kokoromi
from src.admin import app as admin_app
from src.custom.preconnect import PreconnectMiddleware
from src.custom.staticfiles import StaticFiles
from src.extensions.autoref import LinkTargetBlankExtension
from src.extensions.luminous import LuminousHTMLProcessor
from src.admin import get_current_user

prisma = Prisma(auto_register=True)
# DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
DEBUG_MODE = True


@asynccontextmanager
async def lifespan(app: FastAPI):
    await prisma.connect()
    yield
    await prisma.disconnect()


app = FastAPI(
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    version=kokoromi.version,
)
app.add_middleware(PreconnectMiddleware)
app.include_router(admin_app)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "cdn.jsdelivr.net",
        "cdnjs.cloudflare.com",
        "giscus.app",
        "avatars3.githubusercontent.com",
        "api.github.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")
bots = Bots()

ARTICLES_DIR = "articles"
AUTHORS_FILE = "authors.json"
ARTICLES_PER_PAGE = 5


def load_authors() -> dict:
    with open(AUTHORS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


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


@app.exception_handler(HTTPException)
async def internal_server_error(request: Request, exc: Exception):
    error_message = str(exc)
    print(traceback.format_exc())
    return templates.TemplateResponse(
        "load_fail.html",
        {
            "request": request,
            "debug": DEBUG_MODE,
            "error_message": error_message if DEBUG_MODE else None,
        },
        status_code=500,
    )


if DEBUG_MODE == "true":

    @app.get("/err")
    async def err(request: Request):
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/articles/{articleId}", response_class=HTMLResponse)
async def read_article(request: Request, articleId: str):
    ua = request.headers.get("user-agent")
    article = await Post.prisma().find_first(where={"id": articleId})
    if article is None:
        return templates.TemplateResponse(
            "404.html",
            {
                "request": request,
                "settings": await load_settings(),
                "kokoromi": kokoromi,
            },
            status_code=404
        )
    author = await author_db.prisma().find_first(where={"id": article.authorId})
    if author is None:
        return templates.TemplateResponse(
            "404.html",
            {
                "request": request,
                "settings": await load_settings(),
                "kokoromi": kokoromi,
            },
            status_code=404
        )

    html_content = markdown(
        article.content,
        extensions=[
            "abbr",
            "attr_list",
            "def_list",
            "fenced_code",
            "footnotes",
            "md_in_html",
            "tables",
            "admonition",
            "toc",
            LinkTargetBlankExtension(allowed_domains=[]),
            "pymdownx.emoji",
        ],
        extension_configs={
            "pymdownx.emoji": {
                "emoji_index": pymdownx.emoji.twemoji,
            }
        },
    )
    processor = LuminousHTMLProcessor(html_content)
    html_content = processor.process()
    if ua and not bots.is_bot(ua):
        await Post.prisma().update(
            where={"id": articleId}, data={"viewCount": article.viewCount + 1}
        )
    return templates.TemplateResponse(
        request=request,
        name="article.html",
        context={
            "page_url": str(request.url),
            "year": datetime.date.today().year,
            "article": article,
            "author": author,
            "author_avatar": author.icon,
            "author_id": author.id,
            "author_name": author.displayName,
            "author_bio": author.description,
            "content": html_content,
            "excerpt": article.content[:150] + "...",
            "kokoromi": kokoromi,
            "settings": await load_settings(),
        },
    )


@app.get("/", response_class=HTMLResponse)
async def list_articles(request: Request):
    page = int(request.query_params.get("page", 1))

    total_articles = await Post.prisma().count()
    num_pages = (total_articles + ARTICLES_PER_PAGE - 1) // ARTICLES_PER_PAGE
    start_index = (page - 1) * ARTICLES_PER_PAGE
    end_index = start_index + ARTICLES_PER_PAGE

    num_pages = (total_articles + ARTICLES_PER_PAGE - 1) // ARTICLES_PER_PAGE
    start_index = (page - 1) * ARTICLES_PER_PAGE
    end_index = start_index + ARTICLES_PER_PAGE

    articles = await Post.prisma().find_many(
        order={"createdAt": "desc"},
        skip=start_index,
        take=ARTICLES_PER_PAGE,
        include={"author": True},
    )

    recent_articles = await Post.prisma().find_many(take=5)

    prev_page = page - 1 if page > 1 else None
    next_page = page + 1 if end_index < total_articles else None

    return templates.TemplateResponse(
        request=request,
        name="articles.html",
        context={
            "page_url": str(request.url),
            "year": datetime.date.today().year,
            "articles": articles,
            "current_page": page,
            "num_pages": num_pages,
            "prev_page": prev_page,
            "next_page": next_page,
            "recent_articles": recent_articles,
            "kokoromi": kokoromi,
            "settings": await load_settings(),
        },
    )


@app.get("/authors/{author_id}", response_class=HTMLResponse)
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
            status_code=404
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
        where={
            "authorId": author_id,
        },
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


if __name__ == "__main__":
    nest_asyncio.apply()
    uvicorn.run(app, host="0.0.0.0", port=8000)
