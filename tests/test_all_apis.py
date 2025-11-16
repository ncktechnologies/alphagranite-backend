"""
Comprehensive API tests for all job, fab, templating, drafting, and related endpoints.
"""
import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta


class TestJobsAPI:
    """Test job creation and listing"""
    
    async def test_create_job(self, async_client: AsyncClient, auth_headers: dict, test_account):
        """Test creating a new job"""
        job_data = {
            "name": "Kitchen Renovation Project",
            "job_number": "JOB-2025-001",
            "account_id": test_account["id"],
            "description": "Complete kitchen countertop renovation",
            "priority": "High",
            "start_date": datetime.now().isoformat(),
            "due_date": (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        response = await async_client.post(
            "/api/v1/jobs",
            json=job_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == job_data["name"]
        assert data["job_number"] == job_data["job_number"]
        return data
    
    async def test_list_jobs(self, async_client: AsyncClient, auth_headers: dict):
        """Test listing jobs"""
        response = await async_client.get(
            "/api/v1/jobs",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "data" in data


class TestAccountsAPI:
    """Test account endpoints"""
    
    async def test_list_accounts(self, async_client: AsyncClient, auth_headers: dict):
        """Test listing accounts"""
        response = await async_client.get(
            "/api/v1/accounts",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or isinstance(data, list)


class TestStoneResourcesAPI:
    """Test stone thickness, colors, edges APIs"""
    
    async def test_get_stone_thickness(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting stone thickness list"""
        response = await async_client.get(
            "/api/v1/stone-thickness",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or isinstance(data, list)
    
    async def test_get_stone_colors(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting stone colors list"""
        response = await async_client.get(
            "/api/v1/stone-colors",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or isinstance(data, list)
    
    async def test_get_edges(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting edges list"""
        response = await async_client.get(
            "/api/v1/edges",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data or isinstance(data, list)
    
    async def test_get_stone_types(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting stone types list"""
        response = await async_client.get(
            "/api/v1/stone-types",
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestFabsAPI:
    """Test fab creation and management"""
    
    async def test_create_fab(self, async_client: AsyncClient, auth_headers: dict, test_job, test_user):
        """Test creating a new fab"""
        fab_data = {
            "job_id": test_job["id"],
            "fab_type": "Kitchen Countertop",
            "sales_person_id": test_user["id"],
            "stone_type_id": 1,
            "stone_color_id": 1,
            "stone_thickness_id": 1,
            "edge_id": 1,
            "input_area": "Kitchen",
            "total_sqft": 45.5,
            "notes": "Test fab",
            "template_needed": True,
            "drafting_needed": True,
            "slab_smith_cust_needed": True,
            "slab_smith_ag_needed": True,
            "sct_needed": True,
            "final_programming_needed": True
        }
        
        response = await async_client.post(
            "/api/v1/fabs",
            json=fab_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["job_id"] == fab_data["job_id"]
        return data
    
    async def test_list_fabs(self, async_client: AsyncClient, auth_headers: dict):
        """Test listing fabs"""
        response = await async_client.get(
            "/api/v1/fabs",
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestTemplatingAPI:
    """Test templating scheduling and workflow"""
    
    async def test_schedule_templating(self, async_client: AsyncClient, auth_headers: dict, test_fab, test_user):
        """Test scheduling templating for a fab"""
        templating_data = {
            "fab_id": test_fab["id"],
            "technician_id": test_user["id"],
            "schedule_start_date": datetime.now().isoformat(),
            "schedule_due_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "total_sqft": "45.5",
            "notes": "Test templating schedule"
        }
        
        response = await async_client.post(
            "/api/v1/templating/schedule",
            json=templating_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        return data["data"]
    
    async def test_mark_templating_received(self, async_client: AsyncClient, auth_headers: dict, test_templating):
        """Test marking templating as received"""
        response = await async_client.post(
            f"/api/v1/templating/{test_templating['id']}/mark-received",
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestClockworkAPI:
    """Test clockwork (technician/drafter work tracking)"""
    
    async def test_save_clockwork(self, async_client: AsyncClient, auth_headers: dict, test_fab, test_user):
        """Test saving clockwork entry"""
        clockwork_data = {
            "fab_id": test_fab["id"],
            "technician_id": test_user["id"],
            "table_name": "templatings",
            "table_id": 1,
            "started_at": datetime.now().isoformat(),
            "completed_at": (datetime.now() + timedelta(hours=4)).isoformat(),
            "total_sqft_done": "15.5",
            "notes": "Completed first section"
        }
        
        response = await async_client.post(
            "/api/v1/clockwork",
            json=clockwork_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        return data["data"]
    
    async def test_list_clockwork(self, async_client: AsyncClient, auth_headers: dict):
        """Test listing clockwork entries"""
        response = await async_client.get(
            "/api/v1/clockwork",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


class TestDraftingAPI:
    """Test drafting workflow"""
    
    async def test_create_drafting(self, async_client: AsyncClient, auth_headers: dict, test_fab, test_user):
        """Test creating a drafting entry"""
        drafting_data = {
            "fab_id": test_fab["id"],
            "drafter_id": test_user["id"],
            "scheduled_start_date": datetime.now().isoformat(),
            "scheduled_end_date": (datetime.now() + timedelta(days=5)).isoformat(),
            "total_sqft_required_to_draft": "45.5"
        }
        
        response = await async_client.post(
            "/api/v1/drafting",
            json=drafting_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        return data["data"]
    
    async def test_submit_draft_for_review(self, async_client: AsyncClient, auth_headers: dict, test_drafting):
        """Test submitting draft for review"""
        form_data = {
            "total_sqft_drafted": "45.5",
            "no_of_piece_drafted": "8",
            "is_drafting_completed": True,
            "draft_note": "All pieces completed",
            "mentions": "1,2,3"
        }
        
        response = await async_client.post(
            f"/api/v1/drafting/{test_drafting['id']}/submit",
            data=form_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestSlabSmithAPI:
    """Test slab smith workflow"""
    
    async def test_create_slabsmith(self, async_client: AsyncClient, auth_headers: dict, test_fab, test_user):
        """Test creating slab smith entry"""
        slabsmith_data = {
            "fab_id": test_fab["id"],
            "slab_smith_type": "Customer",
            "drafter_id": test_user["id"],
            "start_date": datetime.now().isoformat(),
            "total_sqft_completed": "45.5"
        }
        
        response = await async_client.post(
            "/api/v1/slabsmith",
            json=slabsmith_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        return data["data"]
    
    async def test_mark_slabsmith_completed(self, async_client: AsyncClient, auth_headers: dict, test_slabsmith):
        """Test marking slab smith as completed"""
        response = await async_client.post(
            f"/api/v1/slabsmith/{test_slabsmith['id']}/complete",
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestSalesCTAPI:
    """Test sales CT and review workflow"""
    
    async def test_create_sales_ct(self, async_client: AsyncClient, auth_headers: dict, test_fab):
        """Test creating sales CT entry"""
        sales_ct_data = {
            "fab_id": test_fab["id"],
            "is_revision_needed": False
        }
        
        response = await async_client.post(
            "/api/v1/sales-ct",
            json=sales_ct_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        return data["data"]
    
    async def test_set_review_no(self, async_client: AsyncClient, auth_headers: dict, test_sales_ct):
        """Test setting review needed as No"""
        response = await async_client.put(
            f"/api/v1/sales-ct/{test_sales_ct['id']}/review-no",
            params={"revenue": 5000.0, "status_id": 3},
            headers=auth_headers
        )
        
        assert response.status_code == 200


class TestJobFabListingAPI:
    """Test job listing with fabs"""
    
    async def test_list_jobs_with_fabs(self, async_client: AsyncClient, auth_headers: dict):
        """Test listing jobs with their fabs"""
        response = await async_client.get(
            "/api/v1/jobs-with-fabs",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    async def test_get_table_names(self, async_client: AsyncClient, auth_headers: dict):
        """Test getting table names for clockwork"""
        response = await async_client.get(
            "/api/v1/table-names",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "table_names" in data["data"]


class TestFabDetailsAPI:
    """Test fab details view"""
    
    async def test_get_fab_details(self, async_client: AsyncClient, auth_headers: dict, test_fab):
        """Test getting fab details by stage"""
        response = await async_client.get(
            f"/api/v1/fab/{test_fab['id']}/details",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "data" in data


# Fixtures
@pytest.fixture
async def test_account(async_client: AsyncClient, auth_headers: dict):
    """Create a test account"""
    # Assuming account creation is already available
    response = await async_client.get("/api/v1/accounts?limit=1", headers=auth_headers)
    if response.status_code == 200:
        data = response.json()
        accounts = data.get("data", data)
        if isinstance(accounts, list) and len(accounts) > 0:
            return accounts[0]
    return {"id": 1}  # Fallback


@pytest.fixture
async def test_user(async_client: AsyncClient, auth_headers: dict):
    """Get current user"""
    return {"id": 1}  # Simplified - in real test, get from auth


@pytest.fixture
async def test_job(async_client: AsyncClient, auth_headers: dict, test_account):
    """Create a test job"""
    job_test = TestJobsAPI()
    return await job_test.test_create_job(async_client, auth_headers, test_account)


@pytest.fixture
async def test_fab(async_client: AsyncClient, auth_headers: dict, test_job, test_user):
    """Create a test fab"""
    fab_test = TestFabsAPI()
    return await fab_test.test_create_fab(async_client, auth_headers, test_job, test_user)


@pytest.fixture
async def test_templating(async_client: AsyncClient, auth_headers: dict, test_fab, test_user):
    """Create a test templating"""
    templating_test = TestTemplatingAPI()
    return await templating_test.test_schedule_templating(async_client, auth_headers, test_fab, test_user)


@pytest.fixture
async def test_drafting(async_client: AsyncClient, auth_headers: dict, test_fab, test_user):
    """Create a test drafting"""
    drafting_test = TestDraftingAPI()
    return await drafting_test.test_create_drafting(async_client, auth_headers, test_fab, test_user)


@pytest.fixture
async def test_slabsmith(async_client: AsyncClient, auth_headers: dict, test_fab, test_user):
    """Create a test slabsmith"""
    slabsmith_test = TestSlabSmithAPI()
    return await slabsmith_test.test_create_slabsmith(async_client, auth_headers, test_fab, test_user)


@pytest.fixture
async def test_sales_ct(async_client: AsyncClient, auth_headers: dict, test_fab):
    """Create a test sales CT"""
    sales_ct_test = TestSalesCTAPI()
    return await sales_ct_test.test_create_sales_ct(async_client, auth_headers, test_fab)
