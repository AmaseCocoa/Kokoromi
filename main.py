import os
import traceback
from contextlib import asynccontextmanager

import aiofiles
import nest_asyncio
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.templating import Jinja2Templates

from prisma import Prisma
from src import meta as kokoromi
from src import router
from src.custom.preconnect import PreconnectMiddleware
from src.custom.staticfiles import StaticFiles
from src.custom.cache import CacheControlMiddleware

prisma = Prisma(auto_register=True)
DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"


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
app.add_middleware(CacheControlMiddleware)
app.include_router(router)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "cdn.jsdelivr.net",
        "cdnjs.cloudflare.com",
        "giscus.app",
        "avatars3.githubusercontent.com",
        "api.github.com",
        "cloudflareinsights.com",
        "www.google-analytics.com ",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
nest_asyncio.apply()

templates = Jinja2Templates(directory="templates")

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


@app.get("/robots.txt")
@app.head("/robots.txt")
async def robots(request: Request):
    async with aiofiles.open("./static/robots.txt", "r") as f:
        return PlainTextResponse(await f.read(), status_code=200)

@app.get("/sitemap.xml", response_class=Response)
async def sitemap_xml():
    articles = await prisma.post.find_many()
    authors = await prisma.author.find_many()
    
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    
    static_urls = [
        {'loc': 'https://blog.amase.xyz/'},
        {'loc': 'https://blog.amase.xyz/articles'},
        {'loc': 'https://blog.amase.xyz/search'},
    ]
    
    dynamic_urls = [
        {'loc': f'https://blog.amase.xyz/articles/{article.id}', 'lastmod': article.updatedAt.strftime('%Y-%m-%dT%H:%M:%S%z')}
        for article in articles
    ] + [
        {'loc': f'https://blog.amase.xyz/authors/{author.id}', 'lastmod': author.updatedAt.strftime('%Y-%m-%dT%H:%M:%S%z')}
        for author in authors
    ]
    
    for url in static_urls + dynamic_urls:
        sitemap += '<url>'
        sitemap += f"<loc>{url['loc']}</loc>"
        if 'lastmod' in url:
            sitemap += f"<lastmod>{url['lastmod']}</lastmod>"
        sitemap += '</url>'
    
    sitemap += '</urlset>'
    
    return Response(content=sitemap, media_type="application/xml")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
