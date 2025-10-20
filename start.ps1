# Script to start FastAPI application using Uvicorn (Windows PowerShell)

Write-Host "Starting FastAPI application..."
uvicorn src.app.main:app --reload