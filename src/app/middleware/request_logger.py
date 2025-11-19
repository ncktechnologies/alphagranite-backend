import json
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from src.app.utils.logger import get_logger

# Get logger instance
logger = get_logger(__name__)


class RequestLoggerMiddleware(BaseHTTPMiddleware):
    """Middleware to log all incoming requests with their data"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Log request details
        logger.info(f"\n{'='*80}")
        logger.info(f"📥 INCOMING REQUEST")
        logger.info(f"{'='*80}")
        logger.info(f"Method: {request.method}")
        logger.info(f"URL: {request.url}")
        logger.info(f"Path: {request.url.path}")
        
        # Log query parameters
        if request.query_params:
            logger.info(f"Query Params: {dict(request.query_params)}")
        
        # Log headers (excluding sensitive ones)
        headers_to_log = {
            k: v for k, v in request.headers.items() 
            if k.lower() not in ['authorization', 'cookie', 'x-api-key']
        }
        logger.info(f"Headers: {headers_to_log}")
        
        # Log request body for POST, PUT, PATCH requests
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            try:
                # Read the body
                body = await request.body()
                
                if body:
                    try:
                        # Try to parse as JSON
                        body_json = json.loads(body.decode('utf-8'))
                        logger.info(f"Request Body (JSON):")
                        logger.info(json.dumps(body_json, indent=2))
                    except json.JSONDecodeError:
                        # If not JSON, log as string
                        logger.info(f"Request Body (Raw): {body.decode('utf-8')}")
                    except Exception as e:
                        logger.info(f"Request Body: <binary data or error: {e}>")
                        
                # Important: Re-create the request with the body we just read
                # because body can only be read once
                async def receive():
                    return {"type": "http.request", "body": body}
                
                request._receive = receive
            except Exception as e:
                logger.error(f"Error reading request body: {e}")
        
        logger.info(f"{'='*80}\n")
        
        # Process the request
        response = await call_next(request)
        
        # Optionally log response status
        logger.info(f"📤 RESPONSE: {request.method} {request.url.path} - Status: {response.status_code}")
        
        return response
