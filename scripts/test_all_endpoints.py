#!/usr/bin/env python3
"""
Comprehensive API Endpoint Testing Script
Tests all endpoints in the Alpha Granit Backend API
"""

import requests
import json
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime
import os

# Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_USERNAME = os.getenv("TEST_USERNAME", "admin")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "your_password_here")

# Global token storage
AUTH_TOKEN = None
REFRESH_TOKEN = None

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "skipped": []
}


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 80}{Colors.RESET}\n")


def print_test(method: str, endpoint: str, status: str, message: str = ""):
    """Print test result"""
    color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
    status_symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "○"
    print(f"{color}{status_symbol} {method:6} {endpoint:50} [{status}]{Colors.RESET}")
    if message:
        print(f"  {Colors.MAGENTA}→ {message}{Colors.RESET}")


def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    files: Optional[Dict] = None,
    use_auth: bool = True,
    test_name: str = ""
) -> tuple[bool, Optional[Dict], str]:
    """
    Make HTTP request to API endpoint
    
    Returns: (success, response_data, message)
    """
    url = f"{BASE_URL}{endpoint}"
    headers = {}
    
    if use_auth and AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    
    if data and not files:
        headers["Content-Type"] = "application/json"
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, headers=headers, timeout=10)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, files=files, headers=headers, timeout=10)
            else:
                response = requests.post(url, json=data, params=params, headers=headers, timeout=10)
        elif method == "PUT":
            response = requests.put(url, json=data, params=params, headers=headers, timeout=10)
        elif method == "PATCH":
            response = requests.patch(url, json=data, params=params, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, params=params, headers=headers, timeout=10)
        else:
            return False, None, f"Unsupported method: {method}"
        
        # Check if successful
        success = 200 <= response.status_code < 300
        
        # Try to parse JSON response
        try:
            response_data = response.json()
        except:
            response_data = {"raw": response.text}
        
        message = f"Status: {response.status_code}"
        if not success and response_data:
            error_detail = response_data.get("detail", response_data.get("message", ""))
            if error_detail:
                message += f" - {error_detail}"
        
        return success, response_data, message
        
    except requests.exceptions.Timeout:
        return False, None, "Request timeout"
    except requests.exceptions.ConnectionError:
        return False, None, "Connection error - is the server running?"
    except Exception as e:
        return False, None, f"Error: {str(e)}"


def test_endpoint(
    method: str,
    endpoint: str,
    data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    files: Optional[Dict] = None,
    use_auth: bool = True,
    test_name: str = "",
    skip: bool = False,
    skip_reason: str = ""
) -> Optional[Dict]:
    """
    Test a single endpoint and record result
    
    Returns: response_data if successful, None otherwise
    """
    full_name = f"{method} {endpoint}" + (f" - {test_name}" if test_name else "")
    
    if skip:
        print_test(method, endpoint, "SKIP", skip_reason)
        test_results["skipped"].append(full_name)
        return None
    
    success, response_data, message = make_request(method, endpoint, data, params, files, use_auth, test_name)
    
    if success:
        print_test(method, endpoint, "PASS", message)
        test_results["passed"].append(full_name)
        return response_data
    else:
        print_test(method, endpoint, "FAIL", message)
        test_results["failed"].append(full_name)
        return None


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

def test_auth_endpoints():
    """Test authentication endpoints"""
    global AUTH_TOKEN, REFRESH_TOKEN
    
    print_section("AUTHENTICATION ENDPOINTS")
    
    # 1. Login (REQUIRED - get token for other tests)
    login_data = {
        "username": TEST_USERNAME,
        "password": TEST_PASSWORD
    }
    response = test_endpoint("POST", "/auth/login", data=login_data, use_auth=False)
    
    if response and "data" in response:
        token_data = response["data"]
        AUTH_TOKEN = token_data.get("access_token")
        REFRESH_TOKEN = token_data.get("refresh_token")
        print(f"\n{Colors.GREEN}✓ Authentication successful - token obtained{Colors.RESET}\n")
    else:
        print(f"\n{Colors.RED}✗ CRITICAL: Login failed - cannot test authenticated endpoints{Colors.RESET}")
        print(f"{Colors.YELLOW}Please update TEST_USERNAME and TEST_PASSWORD in the script{Colors.RESET}\n")
        return False
    
    # 2. Refresh Token
    if REFRESH_TOKEN:
        test_endpoint("POST", "/auth/refresh-token", data={"refresh_token": REFRESH_TOKEN}, use_auth=False)
    
    # 3. Get Current User Profile
    test_endpoint("GET", "/auth/me")
    
    # 4. Update Current User Profile
    test_endpoint("PUT", "/auth/me", data={
        "first_name": "Test",
        "last_name": "User"
    })
    
    # 5. Request Password Reset (skip to avoid sending emails)
    test_endpoint("POST", "/auth/request-password-reset", 
                 data={"email": "test@example.com"},
                 use_auth=False,
                 skip=True,
                 skip_reason="Skipped to avoid sending emails")
    
    # 6. Change Password (skip to avoid changing actual password)
    test_endpoint("POST", "/auth/change-password",
                 data={
                     "old_password": "old_pass",
                     "new_password": "new_pass"
                 },
                 skip=True,
                 skip_reason="Skipped to avoid changing password")
    
    return True


# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

def test_health_endpoints():
    """Test health check endpoints"""
    print_section("HEALTH CHECK ENDPOINTS")
    
    test_endpoint("GET", "/health/", use_auth=False)
    test_endpoint("GET", "/health/db", use_auth=False)


# ============================================================================
# FAB ENDPOINTS
# ============================================================================

def test_fab_endpoints():
    """Test FAB endpoints"""
    print_section("FAB ENDPOINTS")
    
    # 1. Get all FABs
    fabs_response = test_endpoint("GET", "/fabs")
    
    # 2. Get FAB by ID (if FABs exist)
    fab_id = None
    if fabs_response and isinstance(fabs_response, list) and len(fabs_response) > 0:
        fab_id = fabs_response[0].get("id")
    elif fabs_response and "data" in fabs_response and len(fabs_response["data"]) > 0:
        fab_id = fabs_response["data"][0].get("id")
    
    if fab_id:
        test_endpoint("GET", f"/fabs/{fab_id}")
        test_endpoint("GET", f"/fab/{fab_id}/details")
    else:
        test_endpoint("GET", "/fabs/1", skip=True, skip_reason="No FABs found")
        test_endpoint("GET", "/fab/1/details", skip=True, skip_reason="No FABs found")
    
    # 3. Create FAB (requires job_id - skip for now)
    test_endpoint("POST", "/fabs",
                 data={
                     "job_id": 1,
                     "fab_type_id": 1,
                     "stone_type_id": 1,
                     "stone_color_id": 1,
                     "stone_thickness_id": 1
                 },
                 skip=True,
                 skip_reason="Requires valid foreign key IDs")
    
    # 4. Update FAB (skip)
    test_endpoint("PUT", f"/fabs/{fab_id if fab_id else 1}",
                 data={"notes": "Updated notes"},
                 skip=True,
                 skip_reason="Skipped to avoid modifying data")
    
    # 5. Delete FAB (skip)
    test_endpoint("DELETE", f"/fabs/{fab_id if fab_id else 1}",
                 skip=True,
                 skip_reason="Skipped to avoid deleting data")
    
    # 6. Get FABs by Job ID (skip if no jobs)
    test_endpoint("GET", "/jobs/1/fabs", skip=True, skip_reason="Requires valid job_id")
    
    # 7. Get FAB Types
    test_endpoint("GET", "/fab-types")


# ============================================================================
# TEMPLATING ENDPOINTS
# ============================================================================

def test_templating_endpoints():
    """Test templating workflow endpoints"""
    print_section("TEMPLATING ENDPOINTS")
    
    # 1. Schedule Templating (skip)
    test_endpoint("POST", "/templating/schedule",
                 data={
                     "fab_id": 1,
                     "technician_id": 1,
                     "date_scheduled": datetime.now().isoformat()
                 },
                 skip=True,
                 skip_reason="Requires valid FAB and technician IDs")
    
    # 2. Get Templating by ID (skip)
    test_endpoint("GET", "/templating/1", skip=True, skip_reason="Requires valid templating ID")
    
    # 3. Get Templating by FAB ID (skip)
    test_endpoint("GET", "/templating/fab/1", skip=True, skip_reason="Requires valid FAB ID")
    
    # 4. Update Templating (skip)
    test_endpoint("PUT", "/templating/1",
                 data={
                     "date_scheduled": datetime.now().isoformat()
                 },
                 skip=True,
                 skip_reason="Requires valid templating ID")
    
    # 5. Mark as Received (skip)
    test_endpoint("POST", "/templating/1/mark-received",
                 skip=True,
                 skip_reason="Requires valid templating ID")
    
    # 6. Unschedule Templating (skip)
    test_endpoint("PUT", "/templating/1/unschedule",
                 skip=True,
                 skip_reason="Requires valid templating ID")


# ============================================================================
# DRAFTING ENDPOINTS
# ============================================================================

def test_drafting_endpoints():
    """Test drafting workflow endpoints"""
    print_section("DRAFTING ENDPOINTS")
    
    # 1. Create Drafting (skip)
    test_endpoint("POST", "/drafting",
                 data={
                     "fab_id": 1,
                     "drafter_id": 1
                 },
                 skip=True,
                 skip_reason="Requires valid FAB and drafter IDs")
    
    # 2. Get Drafting by ID (skip)
    test_endpoint("GET", "/drafting/1", skip=True, skip_reason="Requires valid drafting ID")
    
    # 3. Get Drafting by FAB ID (skip)
    test_endpoint("GET", "/drafting/fab/1", skip=True, skip_reason="Requires valid FAB ID")
    
    # 4. Update Drafting (skip)
    test_endpoint("PUT", "/drafting/1",
                 data={"notes": "Updated"},
                 skip=True,
                 skip_reason="Requires valid drafting ID")
    
    # 5. Submit Drafting (skip)
    test_endpoint("POST", "/drafting/1/submit",
                 skip=True,
                 skip_reason="Requires valid drafting ID")
    
    # 6. Add File to Drafting (skip)
    test_endpoint("POST", "/drafting/1/add-file",
                 data={"file_id": 1},
                 skip=True,
                 skip_reason="Requires valid IDs")
    
    # 7. Delete File from Drafting (skip)
    test_endpoint("DELETE", "/drafting/1/file/1",
                 skip=True,
                 skip_reason="Requires valid IDs")
    
    # 8. Create Pre-Draft Review (skip)
    test_endpoint("POST", "/pre-draft-review",
                 data={"fab_id": 1},
                 skip=True,
                 skip_reason="Requires valid FAB ID")
    
    # 9. Complete Pre-Draft Review (skip)
    test_endpoint("POST", "/pre-draft-review/1/complete",
                 skip=True,
                 skip_reason="Requires valid review ID")
    
    # 10. Set Redraft (skip)
    test_endpoint("POST", "/pre-draft-review/1/set-redraft",
                 data={"reason": "Test"},
                 skip=True,
                 skip_reason="Requires valid review ID")
    
    # 11. Get Pre-Draft Review by FAB ID (skip)
    test_endpoint("GET", "/pre-draft-review/fab/1",
                 skip=True,
                 skip_reason="Requires valid FAB ID")


# ============================================================================
# SLAB SMITH & SALES CT ENDPOINTS
# ============================================================================

def test_slabsmith_salesct_endpoints():
    """Test Slab Smith and Sales CT workflow endpoints"""
    print_section("SLAB SMITH & SALES CT ENDPOINTS")
    
    # Slab Smith endpoints
    test_endpoint("POST", "/slabsmith",
                 data={"fab_id": 1},
                 skip=True,
                 skip_reason="Requires valid FAB ID")
    
    test_endpoint("PUT", "/slabsmith/1",
                 data={"notes": "Updated"},
                 skip=True,
                 skip_reason="Requires valid ID")
    
    test_endpoint("POST", "/slabsmith/1/complete",
                 skip=True,
                 skip_reason="Requires valid ID")
    
    test_endpoint("POST", "/slabsmith/1/add-file",
                 data={"file_id": 1},
                 skip=True,
                 skip_reason="Requires valid IDs")
    
    test_endpoint("DELETE", "/slabsmith/1/file/1",
                 skip=True,
                 skip_reason="Requires valid IDs")
    
    test_endpoint("GET", "/slabsmith/fab/1",
                 skip=True,
                 skip_reason="Requires valid FAB ID")
    
    # Sales CT endpoints
    test_endpoint("POST", "/sales-ct",
                 data={"fab_id": 1},
                 skip=True,
                 skip_reason="Requires valid FAB ID")
    
    test_endpoint("PUT", "/sales-ct/1/review-no",
                 skip=True,
                 skip_reason="Requires valid ID")
    
    test_endpoint("PUT", "/sales-ct/1/review-yes",
                 skip=True,
                 skip_reason="Requires valid ID")
    
    test_endpoint("PUT", "/sales-ct/1/revision",
                 data={"reason": "Test"},
                 skip=True,
                 skip_reason="Requires valid ID")
    
    test_endpoint("GET", "/sales-ct/fab/1",
                 skip=True,
                 skip_reason="Requires valid FAB ID")


# ============================================================================
# JOBS ENDPOINTS
# ============================================================================

def test_jobs_endpoints():
    """Test job management endpoints"""
    print_section("JOBS ENDPOINTS")
    
    # 1. Get all jobs
    jobs_response = test_endpoint("GET", "/jobs")
    
    # 2. Get job by ID
    job_id = None
    if jobs_response and "data" in jobs_response and len(jobs_response["data"]) > 0:
        job_id = jobs_response["data"][0].get("id")
    
    if job_id:
        test_endpoint("GET", f"/jobs/{job_id}")
    else:
        test_endpoint("GET", "/jobs/1", skip=True, skip_reason="No jobs found")
    
    # 3. Create job (skip)
    test_endpoint("POST", "/jobs",
                 data={
                     "job_name": "Test Job",
                     "account_id": 1
                 },
                 skip=True,
                 skip_reason="Skipped to avoid creating data")
    
    # 4. Update job (skip)
    test_endpoint("PUT", f"/jobs/{job_id if job_id else 1}",
                 data={"notes": "Updated"},
                 skip=True,
                 skip_reason="Skipped to avoid modifying data")
    
    # 5. Delete job (skip)
    test_endpoint("DELETE", f"/jobs/{job_id if job_id else 1}",
                 skip=True,
                 skip_reason="Skipped to avoid deleting data")
    
    # 6. Get jobs with FABs
    test_endpoint("GET", "/jobs-with-fabs")
    
    # 7. Get table names
    test_endpoint("GET", "/table-names")


# ============================================================================
# SHOP PLANNING ENDPOINTS
# ============================================================================

def test_shop_planning_endpoints():
    """Test shop planning endpoints"""
    print_section("SHOP PLANNING ENDPOINTS")
    
    # 1. Get all shop plans
    plans_response = test_endpoint("GET", "/shop-planning")
    
    # 2. Get shop plan by ID (skip)
    test_endpoint("GET", "/shop-planning/1", skip=True, skip_reason="Requires valid ID")
    
    # 3. Create shop plan (skip)
    test_endpoint("POST", "/shop-planning",
                 data={"fab_id": 1, "plan_date": datetime.now().isoformat()},
                 skip=True,
                 skip_reason="Requires valid FAB ID")
    
    # 4. Update shop plan (skip)
    test_endpoint("PUT", "/shop-planning/1",
                 data={"notes": "Updated"},
                 skip=True,
                 skip_reason="Requires valid ID")
    
    # 5. Delete shop plan (skip)
    test_endpoint("DELETE", "/shop-planning/1",
                 skip=True,
                 skip_reason="Requires valid ID")
    
    # Shop Planning Section endpoints
    test_endpoint("GET", "/shop-planning-section")
    test_endpoint("GET", "/shop-planning-section/1", skip=True, skip_reason="Requires valid ID")
    test_endpoint("POST", "/shop-planning-section",
                 data={"name": "Test Section"},
                 skip=True,
                 skip_reason="Skipped to avoid creating data")
    test_endpoint("PUT", "/shop-planning-section/1",
                 data={"name": "Updated"},
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("DELETE", "/shop-planning-section/1",
                 skip=True,
                 skip_reason="Requires valid ID")
    
    # Planning Section endpoints
    test_endpoint("GET", "/planning-section/active")
    test_endpoint("GET", "/planning-section/by-name/test", skip=True, skip_reason="Requires valid name")
    test_endpoint("POST", "/planning-section",
                 data={"plan_name": "Test"},
                 skip=True,
                 skip_reason="Skipped to avoid creating data")


# ============================================================================
# CLOCKWORK & TECHNICIAN ENDPOINTS
# ============================================================================

def test_clockwork_endpoints():
    """Test clockwork and technician workflow endpoints"""
    print_section("CLOCKWORK & TECHNICIAN ENDPOINTS")
    
    # Clockwork endpoints
    test_endpoint("GET", "/clockwork")
    test_endpoint("GET", "/clockwork/1", skip=True, skip_reason="Requires valid ID")
    test_endpoint("POST", "/clockwork",
                 data={
                     "fab_id": 1,
                     "workflow_table": "templating",
                     "clock_in": datetime.now().isoformat()
                 },
                 skip=True,
                 skip_reason="Requires valid IDs")
    test_endpoint("PUT", "/clockwork/1",
                 data={"clock_out": datetime.now().isoformat()},
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("DELETE", "/clockwork/1",
                 skip=True,
                 skip_reason="Requires valid ID")
    
    # Technician clock endpoints
    test_endpoint("POST", "/technician/clock",
                 data={
                     "fab_id": 1,
                     "workflow_table": "templating"
                 },
                 skip=True,
                 skip_reason="Requires valid IDs")
    test_endpoint("PUT", "/technician/clock/1",
                 data={"clock_out": datetime.now().isoformat()},
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("DELETE", "/technician/clock/1",
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("GET", "/technician/clockwork")
    test_endpoint("GET", "/technician/clockwork-table-names")


# ============================================================================
# WORKSTATION ENDPOINTS
# ============================================================================

def test_workstation_endpoints():
    """Test workstation endpoints"""
    print_section("WORKSTATION ENDPOINTS")
    
    test_endpoint("GET", "/workstation/active")
    test_endpoint("GET", "/workstation/by-name/test", skip=True, skip_reason="Requires valid name")
    test_endpoint("POST", "/workstation",
                 data={"workstation_name": "Test Station", "status": 1},
                 skip=True,
                 skip_reason="Skipped to avoid creating data")
    test_endpoint("PUT", "/workstation/1",
                 data={"status": 0},
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("DELETE", "/workstation/1",
                 skip=True,
                 skip_reason="Requires valid ID")


# ============================================================================
# STONE RESOURCES ENDPOINTS
# ============================================================================

def test_stone_resources_endpoints():
    """Test stone types, colors, thickness, edges endpoints"""
    print_section("STONE RESOURCES ENDPOINTS")
    
    # Stone Types
    test_endpoint("GET", "/stone-types")
    test_endpoint("GET", "/stone-types/1", skip=True, skip_reason="Requires valid ID")
    test_endpoint("POST", "/stone-types",
                 data={"name": "Test Stone"},
                 skip=True,
                 skip_reason="Skipped to avoid creating data")
    test_endpoint("PUT", "/stone-types/1",
                 data={"name": "Updated"},
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("DELETE", "/stone-types/1",
                 skip=True,
                 skip_reason="Requires valid ID")
    
    # Stone Colors
    test_endpoint("GET", "/stone-colors")
    test_endpoint("GET", "/stone-colors/1", skip=True, skip_reason="Requires valid ID")
    test_endpoint("POST", "/stone-colors",
                 data={"name": "Test Color"},
                 skip=True,
                 skip_reason="Skipped to avoid creating data")
    test_endpoint("PUT", "/stone-colors/1",
                 data={"name": "Updated"},
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("DELETE", "/stone-colors/1",
                 skip=True,
                 skip_reason="Requires valid ID")
    
    # Stone Thickness
    test_endpoint("GET", "/stone-thickness")
    test_endpoint("GET", "/stone-thickness/1", skip=True, skip_reason="Requires valid ID")
    test_endpoint("POST", "/stone-thickness",
                 data={"value": "3cm"},
                 skip=True,
                 skip_reason="Skipped to avoid creating data")
    test_endpoint("PUT", "/stone-thickness/1",
                 data={"value": "Updated"},
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("DELETE", "/stone-thickness/1",
                 skip=True,
                 skip_reason="Requires valid ID")
    
    # Edges
    test_endpoint("GET", "/edges")
    test_endpoint("GET", "/edges/1", skip=True, skip_reason="Requires valid ID")
    test_endpoint("POST", "/edges",
                 data={"name": "Test Edge"},
                 skip=True,
                 skip_reason="Skipped to avoid creating data")
    test_endpoint("PUT", "/edges/1",
                 data={"name": "Updated"},
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("DELETE", "/edges/1",
                 skip=True,
                 skip_reason="Requires valid ID")


# ============================================================================
# ACCOUNTS ENDPOINTS
# ============================================================================

def test_accounts_endpoints():
    """Test account management endpoints"""
    print_section("ACCOUNTS ENDPOINTS")
    
    # 1. Get all accounts
    accounts_response = test_endpoint("GET", "/accounts")
    
    # 2. Get account by ID
    account_id = None
    if accounts_response and "data" in accounts_response and len(accounts_response["data"]) > 0:
        account_id = accounts_response["data"][0].get("id")
    
    if account_id:
        test_endpoint("GET", f"/accounts/{account_id}")
    else:
        test_endpoint("GET", "/accounts/1", skip=True, skip_reason="No accounts found")
    
    # 3. Create account (skip)
    test_endpoint("POST", "/accounts",
                 data={
                     "account_name": "Test Account",
                     "contact_email": "test@example.com"
                 },
                 skip=True,
                 skip_reason="Skipped to avoid creating data")
    
    # 4. Update account (skip)
    test_endpoint("PUT", f"/accounts/{account_id if account_id else 1}",
                 data={"notes": "Updated"},
                 skip=True,
                 skip_reason="Skipped to avoid modifying data")
    
    # 5. Delete account (skip)
    test_endpoint("DELETE", f"/accounts/{account_id if account_id else 1}",
                 skip=True,
                 skip_reason="Skipped to avoid deleting data")


# ============================================================================
# DEPARTMENTS ENDPOINTS
# ============================================================================

def test_departments_endpoints():
    """Test department management endpoints"""
    print_section("DEPARTMENTS ENDPOINTS")
    
    # Note: Department endpoints use multiline decorators
    test_endpoint("GET", "/departments")
    test_endpoint("GET", "/departments/1", skip=True, skip_reason="Requires valid ID")
    test_endpoint("GET", "/departments/1/users", skip=True, skip_reason="Requires valid ID")
    test_endpoint("GET", "/departments/name/test", skip=True, skip_reason="Requires valid name")
    test_endpoint("POST", "/departments",
                 data={"name": "Test Dept"},
                 skip=True,
                 skip_reason="Skipped to avoid creating data")
    test_endpoint("PUT", "/departments/1",
                 data={"name": "Updated"},
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("PATCH", "/departments/1",
                 data={"status": 0},
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("DELETE", "/departments/1",
                 skip=True,
                 skip_reason="Requires valid ID")


# ============================================================================
# USERS ENDPOINTS
# ============================================================================

def test_users_endpoints():
    """Test user management endpoints"""
    print_section("USERS ENDPOINTS")
    
    test_endpoint("GET", "/users/sales-persons")


# ============================================================================
# FILE ENDPOINTS
# ============================================================================

def test_file_endpoints():
    """Test file upload/download endpoints"""
    print_section("FILE ENDPOINTS")
    
    # File upload (skip)
    test_endpoint("POST", "/upload",
                 skip=True,
                 skip_reason="Requires file upload - skipped")
    
    # File download (skip)
    test_endpoint("GET", "/1",
                 skip=True,
                 skip_reason="Requires valid file ID")
    
    # File delete (skip)
    test_endpoint("DELETE", "/1",
                 skip=True,
                 skip_reason="Requires valid file ID")


# ============================================================================
# JOB EXTRAS ENDPOINTS
# ============================================================================

def test_job_extras_endpoints():
    """Test additional job workflow endpoints"""
    print_section("JOB EXTRAS ENDPOINTS")
    
    # Pre-draft endpoints
    test_endpoint("POST", "/predraft/complete",
                 data={"fab_id": 1},
                 skip=True,
                 skip_reason="Requires valid FAB ID")
    test_endpoint("POST", "/predraft/redraft",
                 data={"fab_id": 1, "reason": "Test"},
                 skip=True,
                 skip_reason="Requires valid FAB ID")
    
    # Final Programming endpoints
    test_endpoint("POST", "/finalprogramming/1/files",
                 data={"file_id": 1},
                 skip=True,
                 skip_reason="Requires valid IDs")
    test_endpoint("DELETE", "/finalprogramming/1/files/1",
                 skip=True,
                 skip_reason="Requires valid IDs")
    test_endpoint("POST", "/finalprogramming/1/update",
                 data={"notes": "Updated"},
                 skip=True,
                 skip_reason="Requires valid ID")
    
    # Cut List endpoints
    test_endpoint("POST", "/cutlist/1/update-details",
                 data={"notes": "Updated"},
                 skip=True,
                 skip_reason="Requires valid ID")
    
    # Sales CT endpoints (in job_extras)
    test_endpoint("POST", "/salesct/1/review-no",
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("POST", "/salesct/1/review-yes",
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("POST", "/salesct/1/revision-update",
                 data={"reason": "Test"},
                 skip=True,
                 skip_reason="Requires valid ID")
    
    # Slab Smith endpoints (in job_extras)
    test_endpoint("POST", "/slabsmith/1/complete",
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("POST", "/slabsmith/1/files",
                 data={"file_id": 1},
                 skip=True,
                 skip_reason="Requires valid IDs")
    test_endpoint("DELETE", "/slabsmith/1/files/1",
                 skip=True,
                 skip_reason="Requires valid IDs")
    
    # Drafting endpoints (in job_extras)
    test_endpoint("POST", "/drafting/1/files",
                 data={"file_id": 1},
                 skip=True,
                 skip_reason="Requires valid IDs")
    test_endpoint("DELETE", "/drafting/1/files/1",
                 skip=True,
                 skip_reason="Requires valid IDs")
    test_endpoint("POST", "/drafting/1/submit-review",
                 skip=True,
                 skip_reason="Requires valid ID")
    
    # Shop schedule endpoint
    test_endpoint("POST", "/fab/1/shop-schedule",
                 data={"schedule_date": datetime.now().isoformat()},
                 skip=True,
                 skip_reason="Requires valid FAB ID")


# ============================================================================
# OPERATOR WORKFLOW ENDPOINTS
# ============================================================================

def test_operator_workflow_endpoints():
    """Test operator workflow endpoints"""
    print_section("OPERATOR WORKFLOW ENDPOINTS")
    
    test_endpoint("GET", "/operator-workflow")
    test_endpoint("GET", "/operator-workflow/1", skip=True, skip_reason="Requires valid ID")
    test_endpoint("POST", "/operator-workflow",
                 data={"fab_id": 1, "operator_id": 1},
                 skip=True,
                 skip_reason="Requires valid IDs")
    test_endpoint("PUT", "/operator-workflow/1",
                 data={"notes": "Updated"},
                 skip=True,
                 skip_reason="Requires valid ID")
    test_endpoint("DELETE", "/operator-workflow/1",
                 skip=True,
                 skip_reason="Requires valid ID")


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

def print_summary():
    """Print test summary"""
    print_section("TEST SUMMARY")
    
    total = len(test_results["passed"]) + len(test_results["failed"]) + len(test_results["skipped"])
    passed = len(test_results["passed"])
    failed = len(test_results["failed"])
    skipped = len(test_results["skipped"])
    
    print(f"{Colors.BOLD}Total Tests:{Colors.RESET}   {total}")
    print(f"{Colors.GREEN}Passed:{Colors.RESET}       {passed} ({passed/total*100:.1f}%)" if total > 0 else f"{Colors.GREEN}Passed: 0{Colors.RESET}")
    print(f"{Colors.RED}Failed:{Colors.RESET}       {failed} ({failed/total*100:.1f}%)" if total > 0 else f"{Colors.RED}Failed: 0{Colors.RESET}")
    print(f"{Colors.YELLOW}Skipped:{Colors.RESET}      {skipped} ({skipped/total*100:.1f}%)" if total > 0 else f"{Colors.YELLOW}Skipped: 0{Colors.RESET}")
    
    if failed > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}Failed Tests:{Colors.RESET}")
        for test in test_results["failed"]:
            print(f"  {Colors.RED}✗ {test}{Colors.RESET}")
    
    print(f"\n{Colors.BOLD}Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}\n")
    
    # Return exit code
    return 0 if failed == 0 else 1


def main():
    """Main test runner"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'ALPHA GRANIT API COMPREHENSIVE TEST SUITE'.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
    print(f"\n{Colors.CYAN}Base URL:{Colors.RESET} {BASE_URL}")
    print(f"{Colors.CYAN}Test User:{Colors.RESET} {TEST_USERNAME}\n")
    
    # Test authentication first (required for other tests)
    if not test_auth_endpoints():
        print(f"\n{Colors.RED}Aborting tests due to authentication failure{Colors.RESET}\n")
        sys.exit(1)
    
    # Run all other tests
    test_health_endpoints()
    test_fab_endpoints()
    test_templating_endpoints()
    test_drafting_endpoints()
    test_slabsmith_salesct_endpoints()
    test_jobs_endpoints()
    test_shop_planning_endpoints()
    test_clockwork_endpoints()
    test_workstation_endpoints()
    test_stone_resources_endpoints()
    test_accounts_endpoints()
    test_departments_endpoints()
    test_users_endpoints()
    test_file_endpoints()
    test_job_extras_endpoints()
    test_operator_workflow_endpoints()
    
    # Print summary and exit
    exit_code = print_summary()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
