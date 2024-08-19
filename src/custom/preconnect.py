from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class PreconnectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers['Link'] = (
            '<https://cdn.jsdelivr.net>; rel=preconnect, '
            '<https://giscus.app>; rel=preconnect'
        )
        return response