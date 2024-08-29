import asyncio
import datetime

from fastapi import APIRouter, Cookie, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from python_aid.aidx import genAidx
import pymdownx.emoji
from markdown import markdown

from prisma.models import Post, author, cmsMeta

from .admin import get_current_user
from ..extensions.autoref import LinkTargetBlankExtension
from ..extensions.luminous import LuminousHTMLProcessor
from .. import meta as kokoromi
from ..func import convert_to_jst

app = APIRouter(prefix="/articles")
templates = Jinja2Templates(directory="templates/admin")
templates.env.filters["to_jst"] = convert_to_jst


def min_filter(a, b):
    return min(a, b)


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


templates.env.filters["min"] = min_filter


class Article(BaseModel):
    title: str
    date: str
    author_id: str
    name: str
    excerpt: str
    content: str


async def fa(author_id: str):
    return await author.prisma().find_first(where={"id": author_id})


def find_author(author_id: str) -> author | None:
    return asyncio.run(fa(author_id=author_id))


@app.get("/", response_class=HTMLResponse, name="articles")
async def list_articles(
    request: Request,
    page: int = Query(1, alias="page"),
    Authorization: str | None = Cookie(default=None),
):
    verify = await get_current_user(Authorization)
    if not verify:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
        return response
    page_skip = 10 * (page - 1)
    articles = await Post.prisma().find_many(take=10, skip=page_skip)
    total_pages = await Post.prisma().count()

    return templates.TemplateResponse(
        "articles.html",
        {
            "request": request,
            "articles": articles,
            "page": page,
            "find_author": find_author,
            "total_pages": total_pages,
        },
    )


@app.get("/{articleId}/edit", response_class=HTMLResponse, name="edit_article_form")
async def edit_article_form(
    request: Request, articleId: str, Authorization: str | None = Cookie(default=None)
):
    verify = await get_current_user(Authorization)
    if not verify:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
        return response
    article = await Post.prisma().find_first(
        where={
            "id": articleId,
        }
    )
    authors = await author.prisma().find_first(
        where={
            "id": article.authorId,
        }
    )
    if article is None:
        return HTTPException(status_code=404, detail="Article not found")

    return templates.TemplateResponse(
        "editor.html",
        {"request": request, "author": authors, "article": article},
    )


@app.post("/{articleId}/edit", response_class=HTMLResponse, name="edit_article")
async def edit_article(
    request: Request,
    articleId: str,
    title: str = Form(...),
    author_id: str = Form(...),
    content: str = Form(...),
    draft: bool = Form(False),
    Authorization: str | None = Cookie(default=None),
):
    verify = await get_current_user(Authorization)
    if not verify:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
    source = markdown(
        content,
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
            "markdown_gfm_admonition",
        ],
        extension_configs={
            "pymdownx.emoji": {
                "emoji_index": pymdownx.emoji.twemoji,
            }
        },
    )
    processor = LuminousHTMLProcessor(source)
    source = await processor.process()
    await Post.prisma().update(
        where={"id": articleId},
        data={
            "title": title,
            "content": content,
            "source": source,
            "authorId": author_id,
            "draft": draft,
            "updatedAt": datetime.datetime.now(datetime.UTC),
        },
    )
    if not draft:
        return RedirectResponse(url=f"/articles/{articleId}", status_code=303)
    else:
        return RedirectResponse(
            url=f"/admin/articles/{articleId}/preview", status_code=303
        )


@app.get("/create", response_class=HTMLResponse, name="create_article_form")
async def create_article_form(
    request: Request, Authorization: str | None = Cookie(default=None)
):
    verify: author = await get_current_user(Authorization)
    if not verify:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
        return response
    return templates.TemplateResponse(
        "editor.html",
        {"request": request, "author": verify, "article": None},
    )


@app.get("/{articleId}/delete", response_class=HTMLResponse, name="delete_article")
async def delete_article(
    request: Request, articleId: str, Authorization: str | None = Cookie(default=None)
):
    verify = await get_current_user(Authorization)
    if not verify:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
    else:
        await Post.prisma().delete(where={"id": articleId})
        response = RedirectResponse(url="/admin/articles", status_code=303)
    return response


@app.post("/create", response_class=HTMLResponse, name="create_article")
async def create_article(
    request: Request,
    title: str = Form(...),
    author_id: str = Form(...),
    content: str = Form(...),
    draft: bool = Form(False),
    Authorization: str | None = Cookie(default=None),
):
    verify = await get_current_user(Authorization)
    if not verify:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
    article_id = genAidx()
    now = datetime.datetime.now(datetime.UTC)
    source = markdown(
        content,
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
            "markdown_gfm_admonition",
        ],
        extension_configs={
            "pymdownx.emoji": {
                "emoji_index": pymdownx.emoji.twemoji,
            }
        },
    )
    processor = LuminousHTMLProcessor(source)
    source = await processor.process()
    await Post.prisma().create(
        data={
            "id": article_id,
            "title": title,
            "content": content,
            "source": source,
            "authorId": author_id,
            "draft": draft,
            "createdAt": now,
            "updatedAt": now,
        }
    )
    if not draft:
        return RedirectResponse(url=f"/articles/{article_id}", status_code=303)
    else:
        return RedirectResponse(
            url=f"/admin/articles/{article_id}/preview", status_code=303
        )


@app.get("/{articleId}/preview", response_class=HTMLResponse)
async def preview(
    request: Request, articleId: str, Authorization: str | None = Cookie(default=None)
):
    verify = await get_current_user(Authorization)
    if not verify:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
    article = await Post.prisma().find_first(where={"id": articleId, "draft": True})
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
    _author = await author.prisma().find_first(where={"id": article.authorId})
    if _author is None:
        return templates.TemplateResponse(
            "404.html",
            {
                "request": request,
                "settings": await load_settings(),
                "kokoromi": kokoromi,
            },
            status_code=404,
        )

    if article.source is None:
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
        await Post.prisma().update(
            where={"id": article.id},
            data={
                "source": content
            }
        )
    else:
        content = article.source
    settings = await load_settings()
    return templates.TemplateResponse(
        request=request,
        name="article.html",
        context={
            "page_url": str(request.url),
            "year": datetime.date.today().year,
            "article": article,
            "author": _author,
            "author_avatar": _author.icon,
            "author_id": _author.id,
            "author_name": _author.displayName,
            "author_bio": _author.description,
            "content": content,
            "excerpt": article.content[:150] + "...",
            "kokoromi": kokoromi,
            "settings": settings,
            "comment_disabled": True,
        },
    )
