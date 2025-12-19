from fastapi.responses import JSONResponse
from src.app.service.auth import AuthService
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
class JWTAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.auth_service = AuthService()

    async def dispatch(self, request: Request, call_next):
        # Skip auth endpoints, docs/openapi endpoints, and health check
        if (request.url.path.startswith("/auth/") or
            request.url.path.startswith("/api/v1/auth/") or
            request.url.path.startswith("/docs") or
            request.url.path.startswith("/redoc") or
            request.url.path.startswith("/openapi.json") or
            request.url.path.startswith("/health") or
            # Skip static files for documentation UI
            request.url.path.startswith("/favicon.ico") or
            request.url.path.startswith("/api/v1/test-public/") or
            request.url.path.startswith("/api/v1/files/download/") or
            request.url.path.startswith("/static")):
            return await call_next(request)
            
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            # Return standardized error shape used across the app
            content = {"success": False, "message": "Missing or invalid token", "details": None}
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content=content)

        # Accept either "Bearer <token>" or a raw token value to be more
        # forgiving with different client behaviours (e.g. Swagger UI sends
        # the token as "Bearer <token>" automatically; some clients may
        # send just the token).
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ", 1)[1]
        else:
            token = auth_header
        try:
            payload = self.auth_service.decode_token(token)
            request.state.user = payload
        except HTTPException as e:
            # If the exception detail already contains our standardized
            # error shape (dict), return it directly; otherwise wrap the
            # string/detail into the standardized shape so clients always
            # receive consistent error payloads.
            detail = e.detail
            if isinstance(detail, dict):
                content = detail
            else:
                content = {"success": False, "message": str(detail), "details": None}
            return JSONResponse(status_code=e.status_code, content=content)
        return await call_next(request)


# Additional JWT authentication for route-level protection
class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
        self.auth_service = AuthService()

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials = await super(JWTBearer, self).__call__(request)
        if credentials:
            if not credentials.scheme == "Bearer":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid authentication scheme")
            if not self.verify_jwt(credentials.credentials):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid token or expired token")
            return credentials.credentials
        else:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid authorization code")

    def verify_jwt(self, token: str) -> bool:
        try:
            self.auth_service.decode_token(token)
            return True
        except:
            return False


# Dependency to get the current user
from src.app.database import get_db
from sqlalchemy.future import select
from src.app.database.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Request

# Public routes that should NOT require authentication
PUBLIC_PATHS = [
    "/api/v1/files/download",
    "/docs",
    "/openapi.json",
    "/redoc"
]

def is_public_path(path: str) -> bool:
    """Check if the request path is public"""
    return any(path.startswith(public_path) for public_path in PUBLIC_PATHS)

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    """Dependency that returns the current User instance based on the token

    The previous implementation accidentally defined a nested function and
    returned None when used as a dependency. This version directly implements
    the dependency and raises HTTPException on any authentication problem.
    """
    # Skip authentication for public paths
    if is_public_path(request.url.path):
        return None
    
    if hasattr(request.state, "user"):
        payload = request.state.user
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
