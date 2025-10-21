import uuid
import pytest
from fastapi import status
from httpx import AsyncClient

from tests.conftest import get_test_token_header
from src.app.database.department import Departmentest_token_header


@pytest.mark.asyncio
async def test_create_department(client: AsyncClient, test_db):
    # Get token header
    token_header = await get_test_token_header(client)
    
    # Create department
    department_data = {
        "name": f"Test Department {uuid.uuid4()}",
        "description": "Test department description"
    }
    
    response = await client.post(
        "/departments",
        json=department_data,
        headers=token_header
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == department_data["name"]
    assert data["description"] == department_data["description"]
    assert data["status"] == 1  # Active status
    assert "users" in data
    assert "total_members" in data
    
    # Test department ID was returned
    department_id = data["id"]
    assert department_id is not None


@pytest.mark.asyncio
async def test_update_department(client: AsyncClient, test_db, test_department):
    # Get token header
    token_header = await get_test_token_header(client)
    
    # Update department
    update_data = {
        "name": f"Updated Department {uuid.uuid4()}",
        "description": "Updated description"
    }
    
    response = await client.put(
        f"/departments/{test_department.id}",
        json=update_data,
        headers=token_header
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]


@pytest.mark.asyncio
async def test_change_department_status(client: AsyncClient, test_db, test_department):
    # Get token header
    token_header = await get_test_token_header(client)
    
    # Change status to inactive (assuming 2 is inactive)
    status_data = {
        "status": 2
    }
    
    response = await client.patch(
        f"/departments/{test_department.id}/status",
        json=status_data,
        headers=token_header
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == 2


@pytest.mark.asyncio
async def test_list_departments(client: AsyncClient, test_db):
    # Get token header
    token_header = await get_test_token_header(client)
    
    # List departments
    response = await client.get(
        "/departments",
        headers=token_header
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data


@pytest.mark.asyncio
async def test_get_department_details(client: AsyncClient, test_db, test_department):
    # Get token header
    token_header = await get_test_token_header(client)
    
    # Get department details
    response = await client.get(
        f"/departments/{test_department.id}",
        headers=token_header
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == test_department.id
    assert data["name"] == test_department.name
    assert "users" in data
    assert "total_members" in data


@pytest.mark.asyncio
async def test_list_department_users(client: AsyncClient, test_db, test_department):
    # Get token header
    token_header = await get_test_token_header(client)
    
    # List department users
    response = await client.get(
        f"/departments/{test_department.id}/users",
        headers=token_header
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "department_id" in data
    assert data["department_id"] == test_department.id
    assert "department_name" in data
    assert "department_description" in data
    assert "users" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data
    assert "pages" in data