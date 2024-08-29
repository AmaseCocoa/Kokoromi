import datetime

import pymdownx.emoji
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from is_bot import Bots
from markdown import markdown

from prisma.models import Post, cmsMeta
from prisma.models import author as author_db
from . import meta as kokoromi
from .extensions.autoref import LinkTargetBlankExtension
from .extensions.luminous import LuminousHTMLProcessor
from .extensions.toc import autoToc
from .func import convert_to_jst

app = APIRouter()

templates = Jinja2Templates(directory="templates")
templates.env.filters['to_jst'] = convert_to_jst
bots = Bots()

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

@app.get("/articles/{articleId}", response_class=HTMLResponse)
@app.head("/articles/{articleId}")
async def read_article(request: Request, articleId: str):
    ua = request.headers.get("user-agent")
    article = await Post.prisma().find_first(where={"id": articleId, "draft": False})
    if article is None:
        return templates.TemplateResponse(
            "404.html",
            {
                "request": request,
                "settings": await load_settings(),
                "kokoromi": kokoromi,
            },
            status_code=404,
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
            status_code=404,
        )

    content = markdown(
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
            "pymdownx.tilde",
            "pymdownx.tabbed",
            "pymdownx.tasklist",
            "pymdownx.smartsymbols",
            "pymdownx.magiclink",
            LinkTargetBlankExtension(allowed_domains=[request.base_url.hostname]),
            "pymdownx.emoji", 
            "markdown_gfm_admonition"
        ],
        extension_configs={
            "pymdownx.emoji": {
                "emoji_index": pymdownx.emoji.twemoji,
            }
        },
    )
    processor = LuminousHTMLProcessor(content)
    content = await processor.process()
#    content = await autoToc(content)
    if ua and not bots.is_bot(ua):
        await Post.prisma().update(
            where={"id": articleId}, data={"viewCount": article.viewCount + 1}
        )
    settings = await load_settings()
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
            "content": content,
            "excerpt": article.content[:150] + "...",
            "kokoromi": kokoromi,
            "settings": settings,
            "comment_disabled": False
        },
    )

@app.get("/", response_class=HTMLResponse)
@app.get("/articles", response_class=HTMLResponse)
@app.head("/")
@app.head("/articles")
async def list_articles(request: Request):
    page = int(request.query_params.get("page", 1))

    total_articles = await Post.prisma().count()
    num_pages = (total_articles + ARTICLES_PER_PAGE - 1) // ARTICLES_PER_PAGE
    start_index = (page - 1) * ARTICLES_PER_PAGE
    end_index = start_index + ARTICLES_PER_PAGE

    articles = await Post.prisma().find_many(
        order={"createdAt": "desc"},
        skip=start_index,
        take=ARTICLES_PER_PAGE,
        where={"draft": False},
        include={"author": True},
    )

    recent_articles = await Post.prisma().find_many(order={"createdAt": "desc"}, take=5, where={"draft": False})

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