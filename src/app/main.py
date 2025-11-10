



import os
from fastapi import FastAPI
# New routers for business logic
from src.app.routers import job_extras
from src.app.routers import workstation
from src.app.routers import shop_planning
from fastapi.staticfiles import StaticFiles
from src.app.routers.auth import auth_router
from src.app.routers.role import role_router
from src.app.routers import planning_section
from fastapi.openapi.utils import get_openapi
from src.app.routers import operator_workflow
from src.app.routers import shop_planning_section
from fastapi.middleware.cors import CORSMiddleware
from src.app.routers.employee import employee_router
from src.app.routers.file import router as file_router
from src.app.utils.config import load_dotenv, STATIC_DIR
from src.app.routers.health import router as health_router
from src.app.routers.department import router as department_router 
from src.app.routers.action_menu import action_menu_router, permission_router 

# Load environment variables
load_dotenv()

# Get CORS settings from environment variables or use defaults
cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")
cors_methods = os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS,PATCH").split(",")
cors_headers = os.getenv("CORS_ALLOW_HEADERS", "*").split(",")
cors_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

app = FastAPI(title="Alpha Granite Backend API", version="1.0.0")


def custom_openapi():
    """Add HTTP Bearer auth schema to OpenAPI so the Swagger UI shows an
    Authorize button for bearer (JWT) tokens.
    """
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    # Add a reusable security scheme for Bearer tokens (JWT)
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Enter your JWT token. Paste only the token value (the UI will add the 'Bearer ' prefix).",
    }
    # Add the BearerAuth requirement to every operation so the Swagger UI
    # will include the Authorization header in Try-it-out requests. The
    # app may in reality allow unauthenticated access for some paths
    # (e.g. /auth/*, /health); adding the security requirement here only
    # affects the docs/UI behaviour.
    openapi_schema.setdefault("security", [{"BearerAuth": []}])

    # Ensure each operation explicitly lists the security requirement so
    # the Swagger UI sends the header when "Try it out" is used.
    paths = openapi_schema.get("paths", {})
    for path_item in paths.values():
        # path_item is a dict of methods (get/post/put/...) -> operation
        for operation in path_item.values():
            if isinstance(operation, dict):
                operation.setdefault("security", [{"BearerAuth": []}])
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_credentials,
    allow_methods=cors_methods,
    allow_headers=cors_headers,
)


# Existing routers
app.include_router(auth_router)
app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(employee_router)
app.include_router(department_router)
app.include_router(file_router)
app.include_router(role_router)
app.include_router(action_menu_router)
app.include_router(permission_router)



app.include_router(job_extras.router, prefix="/api/v1", tags=["Job Extras"])
app.include_router(planning_section.router, prefix="/api/v1", tags=["Planning Sections"])
app.include_router(workstation.router, prefix="/api/v1", tags=["Workstations"])
app.include_router(shop_planning.router, prefix="/api/v1", tags=["Shop Planning"])
app.include_router(shop_planning_section.router, prefix="/api/v1", tags=["Shop Planning Sections"])
app.include_router(operator_workflow.router, prefix="/api/v1", tags=["Operator Workflows"])

# Mount static files directory
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


