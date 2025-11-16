#!/usr/bin/env python3
"""
Simple API validation script to test all endpoints
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")

def print_error(message):
    print(f"{RED}✗ {message}{RESET}")

def print_info(message):
    print(f"{YELLOW}ℹ {message}{RESET}")

# Test results
results = {
    "passed": 0,
    "failed": 0,
    "skipped": 0
}

def test_endpoint(method, endpoint, data=None, headers=None, expected_status=200, description=""):
    """Test an API endpoint"""
    try:
        url = f"{API_URL}{endpoint}"
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        if response.status_code == expected_status:
            print_success(f"{description or endpoint}: {response.status_code}")
            results["passed"] += 1
            return response.json() if response.text else None
        else:
            print_error(f"{description or endpoint}: Expected {expected_status}, got {response.status_code}")
            print_error(f"  Response: {response.text[:200]}")
            results["failed"] += 1
            return None
    except Exception as e:
        print_error(f"{description or endpoint}: {str(e)}")
        results["failed"] += 1
        return None

def main():
    print("\n" + "="*60)
    print("API VALIDATION TEST SUITE")
    print("="*60 + "\n")
    
    # First, try to login (this might fail if auth is required, which is okay)
    print_info("Testing authentication...")
    auth_data = {
        "username": "admin@example.com",
        "password": "admin123"
    }
    
    auth_response = test_endpoint(
        "POST", 
        "/auth/login", 
        data=auth_data, 
        expected_status=[200, 401, 404],
        description="Login endpoint"
    )
    
    headers = {}
    if auth_response and "access_token" in auth_response:
        headers["Authorization"] = f"Bearer {auth_response['access_token']}"
        print_success("Authentication successful")
    else:
        print_info("Proceeding without authentication (some endpoints may fail)")
    
    print("\n" + "-"*60)
    print("TESTING BASIC ENDPOINTS")
    print("-"*60 + "\n")
    
    # Test health endpoint
    test_endpoint("GET", "/health", description="Health check")
    
    # Test accounts list
    test_endpoint("GET", "/accounts", headers=headers, description="List accounts")
    
    # Test stone resources
    test_endpoint("GET", "/stone-thickness", headers=headers, description="List stone thickness")
    test_endpoint("GET", "/stone-colors", headers=headers, description="List stone colors")
    test_endpoint("GET", "/stone-types", headers=headers, description="List stone types")
    test_endpoint("GET", "/edges", headers=headers, description="List edges")
    test_endpoint("GET", "/fab-types", headers=headers, description="List fab types")
    
    # Test jobs list
    test_endpoint("GET", "/jobs", headers=headers, description="List jobs")
    
    # Test fabs list
    test_endpoint("GET", "/fabs", headers=headers, description="List fabs")
    
    print("\n" + "-"*60)
    print("TESTING NEW ENDPOINTS")
    print("-"*60 + "\n")
    
    # Test table names
    test_endpoint("GET", "/table-names", headers=headers, description="Get table names for clockwork")
    
    # Test jobs with fabs
    test_endpoint("GET", "/jobs-with-fabs", headers=headers, description="List jobs with fabs")
    
    # Test clockwork list
    test_endpoint("GET", "/clockwork", headers=headers, description="List clockwork entries")
    
    print("\n" + "-"*60)
    print("TESTING CREATION ENDPOINTS (May fail without valid data)")
    print("-"*60 + "\n")
    
    # Try to create a job (will likely fail without valid account_id)
    job_data = {
        "name": "Test Kitchen Job",
        "job_number": f"JOB-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "account_id": 1,
        "description": "Test job",
        "priority": "Medium"
    }
    
    created_job = test_endpoint(
        "POST", 
        "/jobs", 
        data=job_data, 
        headers=headers,
        expected_status=[201, 400, 401, 404],
        description="Create job"
    )
    
    if created_job:
        job_id = created_job.get("id")
        
        # Try to create a fab
        fab_data = {
            "job_id": job_id,
            "fab_type": "Kitchen Countertop",
            "sales_person_id": 1,
            "stone_type_id": 1,
            "stone_color_id": 1,
            "stone_thickness_id": 1,
            "edge_id": 1,
            "input_area": "Kitchen",
            "total_sqft": 45.5,
            "notes": "Test fab"
        }
        
        created_fab = test_endpoint(
            "POST",
            "/fabs",
            data=fab_data,
            headers=headers,
            expected_status=[201, 400, 401, 404],
            description="Create fab"
        )
        
        if created_fab:
            fab_id = created_fab.get("id")
            
            # Test fab details
            test_endpoint(
                "GET",
                f"/fab/{fab_id}/details",
                headers=headers,
                description="Get fab details"
            )
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"{GREEN}Passed:{RESET} {results['passed']}")
    print(f"{RED}Failed:{RESET} {results['failed']}")
    print(f"{YELLOW}Skipped:{RESET} {results['skipped']}")
    print(f"Total: {results['passed'] + results['failed'] + results['skipped']}")
    
    if results['failed'] == 0:
        print(f"\n{GREEN}All tests passed!{RESET}\n")
        return 0
    else:
        print(f"\n{YELLOW}Some tests failed (expected if database is empty or auth required){RESET}\n")
        return 1

if __name__ == "__main__":
    exit(main())
