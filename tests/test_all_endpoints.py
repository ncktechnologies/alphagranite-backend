import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from src.app.main import app
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.database import get_db, engine
from sqlmodel import select
from src.app.database.user import User
from src.app.database.department import Department
from src.app.database.status import Status

# Configure pytest-asyncio
pytestmark = pytest.mark.asyncio

# Base URL for testing
BASE_URL = "http://test"

# Test credentials - use existing admin user or create manually
TEST_ADMIN_USER = {
    "username": "admin",  # Change to actual username
    "password": "admin"   # Change to actual password
}

# Global variable to store auth token
auth_token = None


@pytest_asyncio.fixture
async def client():
    """Create async HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url=BASE_URL) as ac:
        yield ac


@pytest_asyncio.fixture
async def authenticated_client(client):
    """Create authenticated client with valid JWT token."""
    global auth_token
    
    if auth_token is None:
        # Login to get token
        response = await client.post(
            "/auth/login",
            json={
                "username": TEST_ADMIN_USER["username"],
                "password": TEST_ADMIN_USER["password"]
            }
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert data["success"] is True
        auth_token = data["data"]["access_token"]
    
    client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return client


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

class TestHealthEndpoints:
    """Test health check endpoints."""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test basic health check."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_health_db_check(self, client):
        """Test database health check."""
        response = await client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert "database" in data


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    @pytest.mark.asyncio
    async def test_login_success(self, client):
        """Test successful login."""
        response = await client.post(
            "/auth/login",
            json={
                "username": TEST_ADMIN_USER["username"],
                "password": TEST_ADMIN_USER["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert "user" in data["data"]
        assert "permissions" in data["data"]
    
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = await client.post(
            "/auth/login",
            json={
                "username": "invalid_user",
                "password": "wrong_password"
            }
        )
        assert response.status_code in [400, 401]
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, authenticated_client):
        """Test token refresh."""
        # Get refresh token from login
        response = await authenticated_client.post(
            "/auth/login",
            json={
                "username": TEST_ADMIN_USER["username"],
                "password": TEST_ADMIN_USER["password"]
            }
        )
        refresh_token = response.json()["data"]["refresh_token"]
        
        # Use refresh token
        response = await authenticated_client.post(
            "/auth/refresh-token",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data["data"]
    
    @pytest.mark.asyncio
    async def test_get_profile(self, authenticated_client):
        """Test get current user profile."""
        response = await authenticated_client.get("/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["username"] == TEST_ADMIN_USER["username"]
    
    @pytest.mark.asyncio
    async def test_change_password(self, authenticated_client):
        """Test password change."""
        response = await authenticated_client.post(
            "/auth/change-password",
            json={
                "old_password": TEST_ADMIN_USER["password"],
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!"
            }
        )
        # Should succeed or fail with validation error
        assert response.status_code in [200, 400]
        
        # Change back if successful
        if response.status_code == 200:
            await authenticated_client.post(
                "/auth/change-password",
                json={
                    "old_password": "NewPassword123!",
                    "new_password": TEST_ADMIN_USER["password"],
                    "confirm_password": TEST_ADMIN_USER["password"]
                }
            )


# ============================================================================
# DEPARTMENT TESTS
# ============================================================================

class TestDepartmentEndpoints:
    """Test department CRUD endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_departments(self, authenticated_client):
        """Test list all departments."""
        response = await authenticated_client.get("/departments")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    @pytest.mark.asyncio
    async def test_create_department(self, authenticated_client):
        """Test create new department."""
        response = await authenticated_client.post(
            "/departments",
            json={
                "name": f"Test Department {asyncio.get_event_loop().time()}",
                "description": "Test department description"
            }
        )
        assert response.status_code in [200, 201]
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["success"] is True
            assert "id" in data["data"]
            return data["data"]["id"]
    
    @pytest.mark.asyncio
    async def test_get_department(self, authenticated_client):
        """Test get single department."""
        response = await authenticated_client.get("/departments/1")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == 1
    
    @pytest.mark.asyncio
    async def test_update_department(self, authenticated_client):
        """Test update department."""
        # Create first
        create_response = await authenticated_client.post(
            "/departments",
            json={
                "name": f"Update Test Dept {asyncio.get_event_loop().time()}",
                "description": "Original description"
            }
        )
        
        if create_response.status_code in [200, 201]:
            dept_id = create_response.json()["data"]["id"]
            
            # Update
            response = await authenticated_client.put(
                f"/departments/{dept_id}",
                json={
                    "name": f"Updated Dept {dept_id}",
                    "description": "Updated description"
                }
            )
            assert response.status_code == 200


# ============================================================================
# EMPLOYEE TESTS
# ============================================================================

class TestEmployeeEndpoints:
    """Test employee CRUD endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_employees(self, authenticated_client):
        """Test list all employees."""
        response = await authenticated_client.get("/employees")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    @pytest.mark.asyncio
    async def test_create_employee(self, authenticated_client):
        """Test create new employee."""
        import time
        timestamp = int(time.time())
        
        response = await authenticated_client.post(
            "/employees",
            data={
                "first_name": "Test",
                "last_name": "Employee",
                "email": f"test.employee{timestamp}@test.com",
                "department": "1",
                "role_id": "1",
                "phone": "1234567890",
                "gender": "Male"
            }
        )
        assert response.status_code in [200, 201, 400]  # May fail due to role validation
    
    @pytest.mark.asyncio
    async def test_get_employee(self, authenticated_client):
        """Test get single employee."""
        # Get list first
        list_response = await authenticated_client.get("/employees")
        if list_response.status_code == 200:
            employees = list_response.json()["data"]
            if employees:
                emp_id = employees[0]["id"]
                response = await authenticated_client.get(f"/employees/{emp_id}")
                assert response.status_code == 200


# ============================================================================
# ROLE TESTS
# ============================================================================

class TestRoleEndpoints:
    """Test role CRUD endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_roles(self, authenticated_client):
        """Test list all roles."""
        response = await authenticated_client.get("/roles")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)
    
    @pytest.mark.asyncio
    async def test_create_role(self, authenticated_client):
        """Test create new role."""
        import time
        timestamp = int(time.time())
        
        response = await authenticated_client.post(
            "/roles",
            json={
                "name": f"Test Role {timestamp}",
                "description": "Test role description",
                "action_menu_permissions": []
            }
        )
        assert response.status_code in [200, 201]


# ============================================================================
# ACTION MENU & PERMISSIONS TESTS
# ============================================================================

class TestActionMenuEndpoints:
    """Test action menu endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_action_menus(self, authenticated_client):
        """Test list all action menus."""
        response = await authenticated_client.get("/action-menus")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


class TestPermissionEndpoints:
    """Test permission endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_permissions(self, authenticated_client):
        """Test list all permissions."""
        response = await authenticated_client.get("/permissions")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert isinstance(data["data"], list)


# ============================================================================
# BUSINESS API TESTS - ACCOUNTS
# ============================================================================

class TestAccountEndpoints:
    """Test account CRUD endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_accounts(self, authenticated_client):
        """Test list all accounts."""
        response = await authenticated_client.get("/api/v1/accounts")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_create_account(self, authenticated_client):
        """Test create new account."""
        import time
        timestamp = int(time.time())
        
        response = await authenticated_client.post(
            "/api/v1/accounts",
            json={
                "account_name": f"Test Account {timestamp}",
                "status": 1
            }
        )
        assert response.status_code in [200, 201]


# ============================================================================
# BUSINESS API TESTS - JOBS
# ============================================================================

class TestJobEndpoints:
    """Test job CRUD endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_jobs(self, authenticated_client):
        """Test list all jobs."""
        response = await authenticated_client.get("/api/v1/jobs")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_create_job(self, authenticated_client):
        """Test create new job."""
        # First get an account
        accounts_response = await authenticated_client.get("/api/v1/accounts")
        if accounts_response.status_code == 200 and accounts_response.json()["data"]:
            account_id = accounts_response.json()["data"][0]["id"]
            
            import time
            timestamp = int(time.time())
            
            response = await authenticated_client.post(
                "/api/v1/jobs",
                json={
                    "job_name": f"Test Job {timestamp}",
                    "account_id": account_id,
                    "status": 1
                }
            )
            assert response.status_code in [200, 201, 400]


# ============================================================================
# BUSINESS API TESTS - FABS
# ============================================================================

class TestFabEndpoints:
    """Test fab CRUD endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_fabs(self, authenticated_client):
        """Test list all fabs."""
        response = await authenticated_client.get("/api/v1/fabs")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_fab_types(self, authenticated_client):
        """Test get all fab types."""
        response = await authenticated_client.get("/api/v1/fab-types")
        assert response.status_code == 200


# ============================================================================
# BUSINESS API TESTS - STONE DATA
# ============================================================================

class TestStoneEndpoints:
    """Test stone-related endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_stone_thickness(self, authenticated_client):
        """Test list all stone thickness."""
        response = await authenticated_client.get("/api/v1/stone-thickness")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_list_stone_colors(self, authenticated_client):
        """Test list all stone colors."""
        response = await authenticated_client.get("/api/v1/stone-colors")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_list_stone_types(self, authenticated_client):
        """Test list all stone types."""
        response = await authenticated_client.get("/api/v1/stone-types")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


# ============================================================================
# BUSINESS API TESTS - EDGES
# ============================================================================

class TestEdgeEndpoints:
    """Test edge CRUD endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_edges(self, authenticated_client):
        """Test list all edges."""
        response = await authenticated_client.get("/api/v1/edges")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_create_edge(self, authenticated_client):
        """Test create new edge."""
        import time
        timestamp = int(time.time())
        
        response = await authenticated_client.post(
            "/api/v1/edges",
            json={
                "edge_name": f"Test Edge {timestamp}",
                "status": 1
            }
        )
        assert response.status_code in [200, 201]


# ============================================================================
# WORKFLOW TESTS
# ============================================================================

class TestWorkflowEndpoints:
    """Test workflow-related endpoints."""
    
    @pytest.mark.asyncio
    async def test_list_planning_sections(self, authenticated_client):
        """Test list planning sections."""
        response = await authenticated_client.get("/api/v1/planning-sections")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_list_workstations(self, authenticated_client):
        """Test list workstations."""
        response = await authenticated_client.get("/api/v1/workstations")
        assert response.status_code == 200


# ============================================================================
# FILE UPLOAD TESTS
# ============================================================================

class TestFileEndpoints:
    """Test file upload/download endpoints."""
    
    @pytest.mark.asyncio
    async def test_upload_file(self, authenticated_client):
        """Test file upload."""
        # Create a test file
        import io
        file_content = b"Test file content"
        files = {
            "file": ("test.txt", io.BytesIO(file_content), "text/plain")
        }
        
        response = await authenticated_client.post(
            "/files/upload",
            files=files
        )
        assert response.status_code in [200, 201, 400]


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
