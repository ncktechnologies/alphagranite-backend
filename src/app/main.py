



import os
from fastapi import FastAPI
from src.app.routers.auth import auth_router
from src.app.utils.config import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from src.app.routers.employee import employee_router
from src.app.middleware.jwt_auth import JWTAuthMiddleware
from src.app.routers.health import router as health_router
from src.app.routers.department import router as department_router

# Load environment variables
load_dotenv()

# Get CORS settings from environment variables or use defaults
cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
cors_methods = os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS,PATCH").split(",")
cors_headers = os.getenv("CORS_ALLOW_HEADERS", "*").split(",")
cors_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

app = FastAPI(title="Alpha Granite Backend API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_credentials,
    allow_methods=cors_methods,
    allow_headers=cors_headers,
)

app.add_middleware(JWTAuthMiddleware)
app.include_router(auth_router)
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(employee_router)
app.include_router(department_router)


