import os
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from src.app.utils.helpers import error_response

router = APIRouter()

# Define multiple possible upload directories
UPLOAD_DIRS = [
    Path("uploads/drafting"),
    Path("uploads/slabsmith"),
    Path("uploads/finalprogramming"),
    Path("uploads"),  # Generic uploads folder
]

@router.get("/test-public")
async def test_public_route():
    """Test endpoint to verify public access without authentication"""
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "message": "Public route is working! No authentication required.",
            "data": {
                "authenticated": False,
                "timestamp": str(os.times()),
                "upload_dirs": [str(d) for d in UPLOAD_DIRS]
            }
        }
    )

# @router.get("/files/download/{filename}")
# async def download_file(filename: str):
#     """Public endpoint to download files without authentication"""
    
#     # Search for file in all possible directories
#     for upload_dir in UPLOAD_DIRS:
#         file_path = upload_dir / filename
#         if os.path.exists(file_path):
#             return FileResponse(
#                 path=file_path,
#                 filename=filename,
#                 media_type="application/octet-stream"
#             )
    
#     # File not found in any directory
#     raise error_response("File not found on disk", 404)


# @router.get("/files/download/{filename}")
# async def download_file(
#     filename: str,
#     db: AsyncSession = Depends(get_db)
# ):
#     """Download a file by filename"""
#     from fastapi.responses import FileResponse
    
#     file_path = UPLOAD_DIR / filename
    
#     if not os.path.exists(file_path):
#         raise error_response("File not found on disk", 404)
    
#     return FileResponse(
#         path=file_path,
#         filename=filename,
#         media_type="application/octet-stream"
#     )
