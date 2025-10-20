
from fastapi.responses import JSONResponse
from src.app.service.auth import AuthService
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.auth_service = AuthService()

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/auth/"):
            # Skip auth endpoints
            return await call_next(request)
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": "Missing or invalid token"})
        token = auth_header.split(" ", 1)[1]
        try:
            payload = self.auth_service.decode_token(token)
            request.state.user = payload
        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        return await call_next(request)
