from src.app.middleware.jwt_auth import JWTAuthMiddleware
from src.app.middleware.request_logger import RequestLoggerMiddleware




import os
from fastapi import FastAPI, Depends, Request
# New routers for business logic
from src.app.routers import dashboard, fab_details, job_extras
from src.app.routers import operators
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

# Import new business API routers
from src.app.routers import jobs
from src.app.routers import edges
from src.app.routers import fabs 
from src.app.routers import fab_notes
from src.app.routers import accounts
from src.app.routers import users
from src.app.routers import fab_types
from src.app.routers import stone_types
from src.app.routers import stone_colors
from src.app.routers import stone_thickness
from src.app.routers import templating
from src.app.routers import drafting  
from src.app.routers import slabsmith
from src.app.routers import slabsmith_sales_ct
from src.app.routers import sales_ct
from src.app.routers import cut_list
from src.app.routers import final_programming
from src.app.routers import wj_programming
from src.app.routers import wj_scheduling
from src.app.routers import resurface_scheduling
from src.app.routers import revisions
from src.app.routers import shop_revisions
from src.app.routers import cost_of_stone
from src.app.routers import install_scheduling
from src.app.routers import install_completion  
from src.app.routers import public_files
from src.app.routers import shop_cut_plan
from src.app.routers import job_timers
from src.app.routers import job_fab_listing
from src.app.routers import cnc
from src.app.routers import reports
from src.app.service.monthly_end_of_month_status_report import start_monthly_status_report_scheduler
from src.app.service.monthly_end_of_month_status_report import stop_monthly_status_report_scheduler

# Import logging configuration
from src.app.utils.logger import setup_logging
import logging

# Configure logging (add near the top of file)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Or if you have a specific logger setup:
logger = logging.getLogger("src.app.routers.drafting")
logger.setLevel(logging.INFO)

# Load environment variables
load_dotenv()

# Initialize logging system
log_level = os.getenv("LOG_LEVEL", "INFO")
setup_logging(log_level)


def _parse_csv_env(value: str) -> list[str]:
    """Parse comma-separated env values into a normalized list."""
    return [item.strip() for item in value.split(",") if item.strip()]


# Get CORS settings from environment variables or use defaults
cors_origins_str = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://localhost:5173,https://agdemo.easybusiness.ng")
cors_origins = ["*"] if cors_origins_str.strip() == "*" else _parse_csv_env(cors_origins_str)
cors_methods = _parse_csv_env(os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,DELETE,OPTIONS,PATCH"))
cors_headers = _parse_csv_env(os.getenv("CORS_ALLOW_HEADERS", "*"))
cors_expose_headers = _parse_csv_env(os.getenv("CORS_EXPOSE_HEADERS", "Content-Disposition"))
cors_credentials = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

# If using wildcard origins, credentials must be False
if cors_origins == ["*"]:
    cors_credentials = False

app = FastAPI(title="Alpha Granite Backend API", version="1.0.0")


@app.on_event("startup")
async def startup_event() -> None:
    start_monthly_status_report_scheduler()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    await stop_monthly_status_report_scheduler()

# Add request logging middleware (logs all incoming requests)
app.add_middleware(RequestLoggerMiddleware)

# Add JWT authentication middleware
app.add_middleware(JWTAuthMiddleware)


@app.middleware("http")
async def authentication_middleware(request: Request, call_next):
    # Skip authentication for public paths
    if request.url.path.startswith("/api/v1/files/download"):
        return await call_next(request)
    
    # Skip authentication for job media view
    if request.url.path.startswith("/api/v1/jobs/") and "/media/" in request.url.path and request.url.path.endswith("/view"):
        return await call_next(request)
    
    # Apply authentication for other routes
    return await call_next(request)


@app.middleware("http")
async def some_auth_middleware(request: Request, call_next):
    # Skip specific public routes from authentication
    if request.url.path in ["/api/v1/test-public", "/api/v1/files/download"]:
        return await call_next(request)
    
    # For other routes, apply the JWT authentication middleware
    return await call_next(request)


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

    # --- Postman vendor extensions (reference only) ---
    openapi_schema["x-postman-variables"] = [
        {"key": "baseUrl", "value": "https://api.ag.easybusiness.ng"},
        {"key": "bearerToken", "value": ""},
        {"key": "currentTimestamp", "value": ""},
        {"key": "timestamp", "value": ""},
        {"key": "username", "value": ""},
        {"key": "password", "value": ""}
    ]

    openapi_schema["x-postman-prerequest"] = r"""
pm.sendRequest({
    url: '{{baseUrl}}/auth/login',
    method: 'POST',
    header: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    },
    body: {
        mode: 'raw',
        raw: JSON.stringify({
            username: '{{username}}',
            password: '{{password}}'
        })
    }
}, function (err, res) {
    if (err) {
        console.log("Request Error:", err);
        return;
    }

    console.log("Full Response:", res);

    try {
        const jsonResponse = res.json();
        console.log("Parsed Response:", jsonResponse);

        if (jsonResponse.success === true && jsonResponse.data && jsonResponse.data.access_token) {
            const token = jsonResponse.data.access_token;
            pm.environment.set('bearerToken', token);
            console.log("Auth Token Set:", token);
        } else {
            console.log("Unexpected Response Structure:", jsonResponse);
        }

    } catch (parseError) {
        console.log("JSON Parse Error:", parseError);
        console.log("Raw Response Body:", res.text());
    }
});


// Generate current ISO timestamp
const now = new Date().toISOString();
pm.collectionVariables.set("currentTimestamp", now);

// Generate timestamp without timezone (for your API)
const nowNoTz = new Date().toISOString().slice(0, -1);
pm.collectionVariables.set("timestamp", nowNoTz);
"""
    # --- end vendor extensions ---

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
    expose_headers=cors_expose_headers,
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

# New Business API routers
app.include_router(jobs.router, prefix="/api/v1", tags=["Jobs"])
app.include_router(accounts.router, prefix="/api/v1", tags=["Accounts"])
app.include_router(users.router, prefix="/api/v1", tags=["Users"])
app.include_router(stone_thickness.router, prefix="/api/v1", tags=["Stone Thickness"])
app.include_router(stone_colors.router, prefix="/api/v1", tags=["Stone Colors"])
app.include_router(stone_types.router, prefix="/api/v1", tags=["Stone Types"])
app.include_router(edges.router, prefix="/api/v1", tags=["Edges"])
app.include_router(fab_types.router, prefix="/api/v1", tags=["Fab Types"])
app.include_router(fabs.router, prefix="/api/v1", tags=["Fabs"])
app.include_router(fab_notes.router, prefix="/api/v1", tags=["FAB Notes"])
app.include_router(fab_details.router, prefix="/api/v1", tags=["FAB Details"])

# Workflow routers (templating, drafting, etc.)
app.include_router(templating.router, prefix="/api/v1", tags=["Templating"])
app.include_router(drafting.router, prefix="/api/v1", tags=["Drafting"])
app.include_router(slabsmith.router, prefix="/api/v1")
app.include_router(slabsmith_sales_ct.router, prefix="/api/v1", tags=["SlabSmith & Sales CT"])
app.include_router(sales_ct.router, prefix="/api/v1", tags=["SalesCT"])
app.include_router(cut_list.router, prefix="/api/v1", tags=["Cut List"])
app.include_router(final_programming.router, prefix="/api/v1", tags=["Final Programming"])
app.include_router(wj_programming.router, prefix="/api/v1", tags=["WJ Programming"])
app.include_router(wj_scheduling.router, prefix="/api/v1", tags=["WJ Scheduling"])
app.include_router(resurface_scheduling.router, prefix="/api/v1", tags=["Resurface Scheduling"])
app.include_router(revisions.router, prefix="/api/v1", tags=["Revisions"])
app.include_router(shop_revisions.router, prefix="/api/v1", tags=["Shop Revisions"])
app.include_router(cost_of_stone.router, prefix="/api/v1", tags=["Cost of Stone"])
app.include_router(install_scheduling.router, prefix="/api/v1", tags=["Install Scheduling"])
app.include_router(install_completion.router, prefix="/api/v1", tags=["Install Completion"])
app.include_router(job_timers.router, prefix="/api/v1", tags=["Job Timers"])
app.include_router(job_fab_listing.router, prefix="/api/v1", tags=["Job Fab Listing"])
app.include_router(cnc.router, prefix="/api/v1", tags=["CNC Drafting"])
app.include_router(reports.router, prefix="/api/v1", tags=["Reports"])



# Existing business workflow routers
app.include_router(job_extras.router, prefix="/api/v1", tags=["Job Extras"])
app.include_router(operators.router, prefix="/api/v1", tags=["Operators"])
app.include_router(planning_section.router, prefix="/api/v1", tags=["Planning Sections"])
app.include_router(workstation.router, prefix="/api/v1", tags=["Workstations"])
app.include_router(shop_planning.router, prefix="/api/v1", tags=["Shop Planning"])
app.include_router(shop_planning_section.router, prefix="/api/v1", tags=["Shop Planning Sections"])
app.include_router(operator_workflow.router, prefix="/api/v1", tags=["Operator Workflows"])
app.include_router(dashboard.router, prefix="/api/v1", tags=["Dashboard"])

# Register public routes WITHOUT authentication
app.include_router(
    public_files.router, 
    prefix="/api/v1", 
    tags=["public"]
)
app.include_router(shop_cut_plan.router, prefix="/api/v1")


