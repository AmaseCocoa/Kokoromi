from fastapi import APIRouter

from . import author
from . import admin
from . import articles
from . import search

router = APIRouter()
router.include_router(articles.app)
router.include_router(author.app)
router.include_router(search.app)
router.include_router(admin.app)