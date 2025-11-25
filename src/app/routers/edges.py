from datetime import datetime
from typing import List, Optional
from sqlalchemy.future import select
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.database import get_db
from src.app.database.edge import Edge
from src.app.database.user import User
from src.app.interface.business_schemas import (
    EdgeCreate, EdgeUpdate, EdgeResponse,
)
from src.app.utils.permissions import PermissionChecker
from src.app.middleware.jwt_auth import get_current_user
from src.app.interface.response_wrappers import SuccessResponse
from src.app.utils.helpers import error_response, success_response

router = APIRouter()


@router.post("/edges", response_model=SuccessResponse[EdgeResponse], status_code=201)
async def create_edge(
    edge_data: EdgeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("edges", "create"))
):
    """Create a new edge"""
    
    # Check if edge name already exists
    edge_check = await db.execute(select(Edge).where(Edge.name == edge_data.name))
    if edge_check.scalar_one_or_none():
        raise error_response("Edge already exists", 400)
    
    # Create edge
    edge = Edge(
        name=edge_data.name,
        edge_type=edge_data.edge_type,
        description=edge_data.description,
        status_id=1,  # Active status
        created_by=current_user.id,
        created_at=datetime.now()
    )
    
    db.add(edge)
    await db.commit()
    await db.refresh(edge)
    
    return success_response(edge, "Edge created successfully")


@router.get("/edges", response_model=SuccessResponse[List[EdgeResponse]])
async def get_edges(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    status_id: Optional[int] = Query(None, description="Filter by status ID"),
    edge_type: Optional[str] = Query(None, description="Filter by edge type"),
    search: Optional[str] = Query(None, description="Search by name"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of edges with optional filtering"""
    
    query = select(Edge)
    
    # Apply filters
    # Use explicit None check so a provided 0 (invalid) won't be treated as "no filter".
    if status_id is not None:
        query = query.where(Edge.status_id == status_id)
    
    if edge_type:
        query = query.where(Edge.edge_type == edge_type)
    
    if search:
        search_term = f"%{search}%"
        query = query.where(Edge.name.ilike(search_term))
    
    # Apply pagination
    query = query.offset(skip).limit(limit).order_by(Edge.name.asc())
    
    result = await db.execute(query)
    edges = result.scalars().all()
    
    return success_response(edges, "Edges fetched successfully")


@router.get("/edges/{edge_id}", response_model=SuccessResponse[EdgeResponse])
async def get_edge(
    edge_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific edge by ID"""
    
    result = await db.execute(select(Edge).where(Edge.id == edge_id))
    edge = result.scalar_one_or_none()
    
    if not edge:
        raise error_response("Edge not found", 404)

    return success_response(edge, "Edge fetched successfully")


@router.put("/edges/{edge_id}", response_model=SuccessResponse[EdgeResponse])
async def update_edge(
    edge_id: int,
    edge_data: EdgeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("edges", "update"))
):
    """Update an edge"""
    
    # Get existing edge
    result = await db.execute(select(Edge).where(Edge.id == edge_id))
    edge = result.scalar_one_or_none()
    
    if not edge:
        raise error_response("Edge not found", 404)

    # Check name uniqueness if being updated
    if edge_data.name and edge_data.name != edge.name:
        edge_check = await db.execute(select(Edge).where(Edge.name == edge_data.name))
        if edge_check.scalar_one_or_none():
            raise error_response("Edge already exists", 400)
    
    # Update fields
    update_data = edge_data.model_dump(exclude_unset=True)

    # Validate provided status_id to avoid DB foreign key violations
    if "status_id" in update_data:
        status_val = update_data.get("status_id")
        if status_val is None or status_val == 0:
            raise error_response("Missing or invalid 'status_id'", 400)

        # Lazily import Status to avoid circular imports
        from src.app.database.status import Status

        status_result = await db.execute(select(Status).where(Status.id == status_val))
        if not status_result.scalar_one_or_none():
            raise error_response("Provided 'status_id' does not exist", 400)

    for field, value in update_data.items():
        setattr(edge, field, value)
    
    edge.updated_at = datetime.now()
    edge.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(edge)

    return success_response(edge, "Edge updated successfully")


@router.delete("/edges/{edge_id}", response_model=SuccessResponse[None], status_code=200)
async def delete_edge(
    edge_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("edges", "delete"))
):
    """Delete an edge (soft delete by setting status to deleted)"""
    
    result = await db.execute(select(Edge).where(Edge.id == edge_id))
    edge = result.scalar_one_or_none()
    
    if not edge:
        raise error_response("Edge not found", 404)
    
    await db.delete(edge)
    await db.commit()
    
    return success_response(None, "Edge deleted successfully")