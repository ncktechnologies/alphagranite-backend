"""
Comprehensive endpoint testing script for Alpha Granite Backend
Tests all endpoints and reports any errors
"""
import asyncio
import httpx
import json
from datetime import datetime, date

BASE_URL = "http://localhost:8005"
token = None
test_results = []

def log_test(endpoint, method, status, success, error=None):
    """Log test result"""
    result = {
        "endpoint": endpoint,
        "method": method,
        "status": status,
        "success": success,
        "error": error,
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    
    emoji = "✅" if success else "❌"
    print(f"{emoji} {method:6} {endpoint:50} -> {status}")
    if error:
        print(f"   Error: {error}")

async def test_endpoint(client, method, endpoint, data=None, auth=True, expected_status=200):
    """Test a single endpoint"""
    headers = {}
    if auth and token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = await client.get(endpoint, headers=headers)
        elif method == "POST":
            response = await client.post(endpoint, json=data, headers=headers)
        elif method == "PUT":
            response = await client.put(endpoint, json=data, headers=headers)
        elif method == "DELETE":
            response = await client.delete(endpoint, headers=headers)
        elif method == "PATCH":
            response = await client.patch(endpoint, json=data, headers=headers)
        
        success = response.status_code == expected_status or (200 <= response.status_code < 300)
        error = None if success else response.text[:200]
        
        log_test(endpoint, method, response.status_code, success, error)
        return response
    except Exception as e:
        log_test(endpoint, method, 0, False, str(e))
        return None

async def main():
    global token
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        print("\n" + "="*80)
        print("ALPHA GRANITE BACKEND - COMPREHENSIVE ENDPOINT TESTING")
        print("="*80 + "\n")
        
        # 1. AUTHENTICATION
        print("\n📋 AUTHENTICATION ENDPOINTS")
        print("-" * 80)
        
        # Try login with first password
        response = await test_endpoint(
            client, "POST", "/auth/login",
            data={"username": "admin", "password": "admin123@Daewi1"},
            auth=False
        )
        
        if not response or response.status_code != 200:
            # Try second password
            response = await test_endpoint(
                client, "POST", "/auth/login",
                data={"username": "admin", "password": "YourSecurePassword123!"},
                auth=False
            )
        
        if response and response.status_code == 200:
            data = response.json()
            # Handle nested data structure
            if "data" in data and isinstance(data["data"], dict):
                token = data["data"].get("access_token")
            else:
                token = data.get("access_token") or data.get("token")
            if token:
                print(f"✅ Authenticated successfully! Token obtained.")
        
        if not token:
            print("❌ Authentication failed with both passwords. Creating new user...")
            # Create new admin user
            await test_endpoint(
                client, "POST", "/auth/register",
                data={
                    "username": "testadmin",
                    "email": "testadmin@example.com",
                    "password": "TestPass123!",
                    "first_name": "Test",
                    "last_name": "Admin"
                },
                auth=False
            )
            response = await test_endpoint(
                client, "POST", "/auth/login",
                data={"username": "testadmin", "password": "TestPass123!"},
                auth=False
            )
            if response and response.status_code == 200:
                data = response.json()
                # Handle nested data structure
                if "data" in data and isinstance(data["data"], dict):
                    token = data["data"].get("access_token")
                else:
                    token = data.get("access_token") or data.get("token")
        
        if not token:
            print("\n❌ FATAL: Could not obtain authentication token. Stopping tests.")
            return
        
        # Test other auth endpoints
        # Note: /auth/refresh doesn't exist in this implementation
        await test_endpoint(client, "GET", "/auth/me", auth=True)
        
        # 2. HEALTH CHECK
        print("\n📋 HEALTH CHECK")
        print("-" * 80)
        await test_endpoint(client, "GET", "/health", auth=False, expected_status=307)  # Redirects to /health/
        
        # 3. USERS/EMPLOYEES
        print("\n📋 USERS/EMPLOYEES ENDPOINTS")
        print("-" * 80)
        await test_endpoint(client, "GET", "/employees")
        await test_endpoint(client, "GET", "/api/v1/users/sales-persons")
        
        # 4. DEPARTMENTS
        print("\n📋 DEPARTMENTS ENDPOINTS")
        print("-" * 80)
        await test_endpoint(client, "GET", "/departments")
        
        # 5. ROLES
        print("\n📋 ROLES ENDPOINTS")
        print("-" * 80)
        await test_endpoint(client, "GET", "/roles")
        
        # 6. ACCOUNTS
        print("\n📋 ACCOUNTS ENDPOINTS")
        print("-" * 80)
        await test_endpoint(client, "GET", "/api/v1/accounts")
        await test_endpoint(client, "GET", "/api/v1/accounts?skip=0&limit=20")
        account_response = await test_endpoint(client, "GET", "/api/v1/accounts")
        account_id = None
        if account_response and account_response.status_code == 200:
            accounts = account_response.json()
            # Handle different response formats
            if isinstance(accounts, dict) and "data" in accounts:
                accounts = accounts["data"]
            if isinstance(accounts, list) and len(accounts) > 0:
                account_id = accounts[0].get("id")
                await test_endpoint(client, "GET", f"/api/v1/accounts/{account_id}")
                await test_endpoint(client, "GET", f"/api/v1/accounts/{account_id}/jobs")
        
        # 7. JOBS
        print("\n📋 JOBS ENDPOINTS")
        print("-" * 80)
        await test_endpoint(client, "GET", "/api/v1/jobs")
        await test_endpoint(client, "GET", "/api/v1/jobs?skip=0&limit=20")
        job_response = await test_endpoint(client, "GET", "/api/v1/jobs")
        job_id = None
        if job_response and job_response.status_code == 200:
            jobs = job_response.json()
            if isinstance(jobs, dict) and "data" in jobs:
                jobs = jobs["data"]
            if isinstance(jobs, list) and len(jobs) > 0:
                job_id = jobs[0].get("id")
                await test_endpoint(client, "GET", f"/api/v1/jobs/{job_id}")
                await test_endpoint(client, "GET", f"/api/v1/jobs/{job_id}/fabs")
        
        # Create test job if we have account_id
        if account_id:
            create_job_response = await test_endpoint(
                client, "POST", "/api/v1/jobs",
                data={
                    "name": "Test Job " + datetime.now().strftime("%Y%m%d%H%M%S"),
                    "job_number": "TEST" + datetime.now().strftime("%H%M%S"),
                    "account_id": account_id,
                    "project_value": "10000"
                },
                expected_status=201
            )
            if create_job_response and create_job_response.status_code == 201:
                new_job_id = create_job_response.json()["id"]
                await test_endpoint(client, "GET", f"/api/v1/jobs/{new_job_id}")
        
        # 8. STONE COLORS
        print("\n📋 STONE COLORS ENDPOINTS")
        print("-" * 80)
        await test_endpoint(client, "GET", "/api/v1/stone-colors")
        await test_endpoint(client, "GET", "/api/v1/stone-colors?skip=0&limit=20")
        color_response = await test_endpoint(client, "GET", "/api/v1/stone-colors")
        color_id = None
        if color_response and color_response.status_code == 200:
            colors = color_response.json()
            if isinstance(colors, dict) and "data" in colors:
                colors = colors["data"]
            if isinstance(colors, list) and len(colors) > 0:
                color_id = colors[0].get("id")
                await test_endpoint(client, "GET", f"/api/v1/stone-colors/{color_id}")
        
        # 9. STONE TYPES
        print("\n📋 STONE TYPES ENDPOINTS")
        print("-" * 80)
        await test_endpoint(client, "GET", "/api/v1/stone-types")
        await test_endpoint(client, "GET", "/api/v1/stone-types?skip=0&limit=20")
        type_response = await test_endpoint(client, "GET", "/api/v1/stone-types")
        type_id = None
        if type_response and type_response.status_code == 200:
            types = type_response.json()
            if isinstance(types, dict) and "data" in types:
                types = types["data"]
            if isinstance(types, list) and len(types) > 0:
                type_id = types[0].get("id")
                await test_endpoint(client, "GET", f"/api/v1/stone-types/{type_id}")
        
        # 10. STONE THICKNESS
        print("\n📋 STONE THICKNESS ENDPOINTS")
        print("-" * 80)
        await test_endpoint(client, "GET", "/api/v1/stone-thickness")
        await test_endpoint(client, "GET", "/api/v1/stone-thickness?skip=0&limit=20")
        thickness_response = await test_endpoint(client, "GET", "/api/v1/stone-thickness")
        thickness_id = None
        if thickness_response and thickness_response.status_code == 200:
            thicknesses = thickness_response.json()
            if isinstance(thicknesses, dict) and "data" in thicknesses:
                thicknesses = thicknesses["data"]
            if isinstance(thicknesses, list) and len(thicknesses) > 0:
                thickness_id = thicknesses[0].get("id")
                await test_endpoint(client, "GET", f"/api/v1/stone-thickness/{thickness_id}")
        
        # 11. EDGES
        print("\n📋 EDGES ENDPOINTS")
        print("-" * 80)
        await test_endpoint(client, "GET", "/api/v1/edges")
        await test_endpoint(client, "GET", "/api/v1/edges?skip=0&limit=20")
        edge_response = await test_endpoint(client, "GET", "/api/v1/edges")
        edge_id = None
        if edge_response and edge_response.status_code == 200:
            edges = edge_response.json()
            if isinstance(edges, dict) and "data" in edges:
                edges = edges["data"]
            if isinstance(edges, list) and len(edges) > 0:
                edge_id = edges[0].get("id")
                await test_endpoint(client, "GET", f"/api/v1/edges/{edge_id}")
        
        # 12. FAB TYPES
        print("\n📋 FAB TYPES ENDPOINTS")
        print("-" * 80)
        await test_endpoint(client, "GET", "/api/v1/fab-types")
        
        # 13. FABS
        print("\n📋 FABS ENDPOINTS")
        print("-" * 80)
        await test_endpoint(client, "GET", "/api/v1/fabs")
        await test_endpoint(client, "GET", "/api/v1/fabs?skip=0&limit=100")
        fab_response = await test_endpoint(client, "GET", "/api/v1/fabs")
        fab_id = None
        if fab_response and fab_response.status_code == 200:
            fabs = fab_response.json()
            if isinstance(fabs, dict) and "data" in fabs:
                fabs = fabs["data"]
            if isinstance(fabs, list) and len(fabs) > 0:
                fab_id = fabs[0].get("id")
                await test_endpoint(client, "GET", f"/api/v1/fabs/{fab_id}")
        
        # 14. TEMPLATING (resource-specific, needs fab_id)
        print("\n📋 TEMPLATING ENDPOINTS")
        print("-" * 80)
        if fab_id:
            await test_endpoint(client, "GET", f"/api/v1/templating/fab/{fab_id}")
        
        # 15. DRAFTING (resource-specific, needs fab_id)
        print("\n📋 DRAFTING ENDPOINTS")
        print("-" * 80)
        if fab_id:
            await test_endpoint(client, "GET", f"/api/v1/drafting/fab/{fab_id}")
        
        # 16. SLABSMITH & SALES CT (resource-specific, needs fab_id)
        print("\n📋 SLABSMITH & SALES CT ENDPOINTS")
        print("-" * 80)
        if fab_id:
            await test_endpoint(client, "GET", f"/api/v1/slabsmith/fab/{fab_id}")
        
        # 17. CUT LIST (resource-specific, needs fab_id)
        print("\n📋 CUT LIST ENDPOINTS")
        print("-" * 80)
        if fab_id:
            await test_endpoint(client, "GET", f"/api/v1/cut-list/{fab_id}")
        
        # 18. FINAL PROGRAMMING (resource-specific, needs fab_id)
        print("\n📋 FINAL PROGRAMMING ENDPOINTS")
        print("-" * 80)
        if fab_id:
            await test_endpoint(client, "GET", f"/api/v1/final-programming/{fab_id}/session-status")
        
        # 19. WJ PROGRAMMING (check what endpoints exist)
        print("\n📋 WJ PROGRAMMING ENDPOINTS")
        print("-" * 80)
        # Skip for now - need to check actual endpoints
        
        # 20. ACTION MENU
        print("\n📋 ACTION MENU ENDPOINTS")
        print("-" * 80)
        await test_endpoint(client, "GET", "/action-menus")
        
        # 21. PERMISSIONS
        print("\n📋 PERMISSIONS ENDPOINTS")
        print("-" * 80)
        await test_endpoint(client, "GET", "/permissions")
        
        # Print Summary
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        total = len(test_results)
        passed = sum(1 for r in test_results if r["success"])
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")
        
        if failed > 0:
            print("\n" + "="*80)
            print("FAILED TESTS")
            print("="*80)
            for r in test_results:
                if not r["success"]:
                    print(f"\n❌ {r['method']} {r['endpoint']}")
                    print(f"   Status: {r['status']}")
                    if r["error"]:
                        print(f"   Error: {r['error'][:200]}")
        
        # Save detailed results
        with open("/Users/segun/Desktop/Protech/alpha_granit_backend/test_results.json", "w") as f:
            json.dump(test_results, f, indent=2)
        
        print(f"\n✅ Detailed results saved to test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
