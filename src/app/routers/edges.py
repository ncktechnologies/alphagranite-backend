from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.database import get_db
from src.app.database.edge import Edge
from src.app.database.user import User
from src.app.interface.business_schemas import (
    EdgeCreate, EdgeUpdate, EdgeResponse
)
from src.app.middleware.jwt_auth import get_current_user

router = APIRouter()


@router.post("/edges", response_model=EdgeResponse, status_code=201)
async def create_edge(
    edge_data: EdgeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new edge"""
    
    # Check if edge name already exists
    edge_check = await db.execute(select(Edge).where(Edge.name == edge_data.name))
    if edge_check.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Edge already exists")
    
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
    
    return edge


@router.get("/edges", response_model=List[EdgeResponse])
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
    if status_id:
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
    
    return edges


@router.get("/edges/{edge_id}", response_model=EdgeResponse)
async def get_edge(
    edge_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific edge by ID"""
    
    result = await db.execute(select(Edge).where(Edge.id == edge_id))
    edge = result.scalar_one_or_none()
    
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    
    return edge


@router.put("/edges/{edge_id}", response_model=EdgeResponse)
async def update_edge(
    edge_id: int,
    edge_data: EdgeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an edge"""
    
    # Get existing edge
    result = await db.execute(select(Edge).where(Edge.id == edge_id))
    edge = result.scalar_one_or_none()
    
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    
    # Check name uniqueness if being updated
    if edge_data.name and edge_data.name != edge.name:
        edge_check = await db.execute(select(Edge).where(Edge.name == edge_data.name))
        if edge_check.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Edge already exists")
    
    # Update fields
    update_data = edge_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(edge, field, value)
    
    edge.updated_at = datetime.now()
    edge.updated_by = current_user.id
    
    await db.commit()
    await db.refresh(edge)
    
    return edge


@router.delete("/edges/{edge_id}", status_code=204)
async def delete_edge(
    edge_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an edge (soft delete by setting status to deleted)"""
    
    result = await db.execute(select(Edge).where(Edge.id == edge_id))
    edge = result.scalar_one_or_none()
    
    if not edge:
        raise HTTPException(status_code=404, detail="Edge not found")
    
    # Soft delete by setting status to deleted (assuming status_id 3 is deleted)
    edge.status_id = 3  # Deleted status
    edge.updated_at = datetime.now()
    edge.updated_by = current_user.id
    
    await db.commit()
    
    return None