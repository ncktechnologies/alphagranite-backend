



from fastapi import FastAPI
from src.app.routers.auth import auth_router
from src.app.middleware.jwt_auth import JWTAuthMiddleware




app = FastAPI(title="Alpha Granite Backend API", version="1.0.0")
app.add_middleware(JWTAuthMiddleware)
app.include_router(auth_router)


