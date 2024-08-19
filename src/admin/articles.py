import asyncio

from fastapi import APIRouter, Form, HTTPException, Query, Request, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from python_aid.aidx import genAidx

from prisma.models import Post, author

from .admin import get_current_user

app = APIRouter(prefix="/articles")
templates = Jinja2Templates(directory="templates/admin")


def min_filter(a, b):
    return min(a, b)


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
    Authorization: str | None = Cookie(default=None),
):
    verify = await get_current_user(Authorization)
    if not verify:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
    await Post.prisma().update(
        where={
            "id": articleId
        },
        data={
            "title": title,
            "content": content,
            "authorId": author_id,
        }
    )
    return RedirectResponse(url=f"/articles/{articleId}", status_code=303)


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


@app.post("/create", response_class=HTMLResponse, name="create_article")
async def create_article(
    title: str = Form(...),
    author_id: str = Form(...),
    content: str = Form(...),
    Authorization: str | None = Cookie(default=None),
):
    verify = await get_current_user(Authorization)
    if not verify:
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie(key="Authorization", httponly=True)
    article_id = genAidx()

    await Post.prisma().create(
        data={
            "id": article_id,
            "title": title,
            "content": content,
            "authorId": author_id,
        }
    )
    return RedirectResponse(url=f"/articles/{article_id}", status_code=303)
