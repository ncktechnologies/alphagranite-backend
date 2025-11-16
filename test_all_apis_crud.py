"""
Comprehensive API Test Suite - CRUD Order
Tests all APIs with focus on Jobs and related endpoints
"""
import httpx
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
AUTH_URL = "http://localhost:8000/auth"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

class APITester:
    def __init__(self):
        self.token = None
        self.headers = {}
        self.test_data = {}
        self.results = {"passed": 0, "failed": 0, "tests": []}
        
    def log(self, message, status="info"):
        colors = {"success": Colors.GREEN, "error": Colors.RED, "info": Colors.BLUE, "warning": Colors.YELLOW}
        color = colors.get(status, Colors.BLUE)
        print(f"{color}{message}{Colors.END}")
    
    def test(self, name, method, endpoint, data=None, expected_status=200, description=""):
        """Execute a test and record results"""
        url = f"{BASE_URL}{endpoint}" if not endpoint.startswith("http") else endpoint
        self.log(f"\n{'='*80}", "info")
        self.log(f"TEST: {name}", "info")
        if description:
            self.log(f"Description: {description}", "info")
        self.log(f"Method: {method} | Endpoint: {endpoint}", "info")
        
        try:
            with httpx.Client(timeout=30.0) as client:
                if method == "GET":
                    response = client.get(url, headers=self.headers)
                elif method == "POST":
                    response = client.post(url, json=data, headers=self.headers)
                elif method == "PUT":
                    response = client.put(url, json=data, headers=self.headers)
                elif method == "DELETE":
                    response = client.delete(url, headers=self.headers)
            
            self.log(f"Status Code: {response.status_code}", "info")
            
            # Try to parse JSON response
            try:
                response_data = response.json()
                self.log(f"Response: {json.dumps(response_data, indent=2)}", "info")
            except:
                self.log(f"Response (text): {response.text[:500]}", "info")
                response_data = None
            
            # Check status
            if response.status_code == expected_status:
                self.log(f"✅ PASSED: {name}", "success")
                self.results["passed"] += 1
                self.results["tests"].append({"name": name, "status": "PASSED", "code": response.status_code})
                return response_data
            else:
                self.log(f"❌ FAILED: {name} (Expected {expected_status}, got {response.status_code})", "error")
                self.results["failed"] += 1
                self.results["tests"].append({"name": name, "status": "FAILED", "code": response.status_code})
                return None
                
        except Exception as e:
            self.log(f"❌ EXCEPTION: {name} - {str(e)}", "error")
            self.results["failed"] += 1
            self.results["tests"].append({"name": name, "status": "EXCEPTION", "error": str(e)})
            return None
    
    def setup_auth(self):
        """Get or create user and obtain auth token"""
        self.log("\n" + "="*80, "info")
        self.log("PHASE 1: AUTHENTICATION SETUP", "info")
        self.log("="*80, "info")
        
        # AUTHENTICATION TEMPORARILY DISABLED ON SERVER
        self.log("\n⚠️  Authentication is temporarily disabled on the server for testing", "warning")
        self.log("✅ Proceeding without authentication token", "success")
        return True
    
    def test_accounts(self):
        """Test Accounts APIs"""
        self.log("\n" + "="*80, "info")
        self.log("PHASE 2: ACCOUNTS (Prerequisites for Jobs)", "info")
        self.log("="*80, "info")
        
        # CREATE
        account_data = {
            "account_name": f"Test Account {datetime.now().strftime('%H%M%S')}",
            "contact_person": "John Doe",
            "email": "john@testaccount.com",
            "phone": "1234567890",
            "address": "123 Test St"
        }
        
        result = self.test(
            "Create Account",
            "POST",
            "/accounts",
            account_data,
            201,
            "Create a new account for testing jobs"
        )
        
        if result and result.get("data"):
            self.test_data["account_id"] = result["data"].get("id")
            self.log(f"Created Account ID: {self.test_data['account_id']}", "success")
        
        # READ - List
        self.test(
            "List Accounts",
            "GET",
            "/accounts",
            None,
            200,
            "Get all accounts"
        )
        
        # READ - Get single
        if "account_id" in self.test_data:
            self.test(
                "Get Account by ID",
                "GET",
                f"/accounts/{self.test_data['account_id']}",
                None,
                200,
                f"Get account with ID {self.test_data['account_id']}"
            )
            
            # UPDATE
            update_data = {
                "contact_person": "Jane Doe Updated"
            }
            self.test(
                "Update Account",
                "PUT",
                f"/accounts/{self.test_data['account_id']}",
                update_data,
                200,
                "Update account contact person"
            )
    
    def test_stone_resources(self):
        """Test Stone Types, Colors, Thickness, Edges"""
        self.log("\n" + "="*80, "info")
        self.log("PHASE 3: STONE RESOURCES (Prerequisites for Jobs)", "info")
        self.log("="*80, "info")
        
        # Stone Types - CREATE
        stone_type_data = {"name": f"Test Granite {datetime.now().strftime('%H%M%S')}"}
        result = self.test("Create Stone Type", "POST", "/stone-types", stone_type_data, 201)
        if result and result.get("data"):
            self.test_data["stone_type_id"] = result["data"].get("id")
        
        # Stone Types - READ
        self.test("List Stone Types", "GET", "/stone-types", None, 200)
        if "stone_type_id" in self.test_data:
            self.test("Get Stone Type", "GET", f"/stone-types/{self.test_data['stone_type_id']}", None, 200)
            # UPDATE
            self.test("Update Stone Type", "PUT", f"/stone-types/{self.test_data['stone_type_id']}", 
                     {"name": "Updated Granite"}, 200)
        
        # Stone Colors - CREATE
        color_data = {"name": f"Test Black {datetime.now().strftime('%H%M%S')}"}
        result = self.test("Create Stone Color", "POST", "/stone-colors", color_data, 201)
        if result and result.get("data"):
            self.test_data["stone_color_id"] = result["data"].get("id")
        
        # Stone Colors - READ
        self.test("List Stone Colors", "GET", "/stone-colors", None, 200)
        if "stone_color_id" in self.test_data:
            self.test("Get Stone Color", "GET", f"/stone-colors/{self.test_data['stone_color_id']}", None, 200)
            # UPDATE
            self.test("Update Stone Color", "PUT", f"/stone-colors/{self.test_data['stone_color_id']}", 
                     {"name": "Updated Black"}, 200)
        
        # Stone Thickness - CREATE
        thickness_data = {"name": "3cm Test"}
        result = self.test("Create Stone Thickness", "POST", "/stone-thickness", thickness_data, 201)
        if result and result.get("data"):
            self.test_data["stone_thickness_id"] = result["data"].get("id")
        
        # Stone Thickness - READ
        self.test("List Stone Thickness", "GET", "/stone-thickness", None, 200)
        if "stone_thickness_id" in self.test_data:
            self.test("Get Stone Thickness", "GET", f"/stone-thickness/{self.test_data['stone_thickness_id']}", None, 200)
            # UPDATE
            self.test("Update Stone Thickness", "PUT", f"/stone-thickness/{self.test_data['stone_thickness_id']}", 
                     {"name": "2cm Updated"}, 200)
        
        # Edges - CREATE
        edge_data = {"name": f"Test Edge {datetime.now().strftime('%H%M%S')}"}
        result = self.test("Create Edge", "POST", "/edges", edge_data, 201)
        if result and result.get("data"):
            self.test_data["edge_id"] = result["data"].get("id")
        
        # Edges - READ
        self.test("List Edges", "GET", "/edges", None, 200)
        if "edge_id" in self.test_data:
            self.test("Get Edge", "GET", f"/edges/{self.test_data['edge_id']}", None, 200)
            # UPDATE
            self.test("Update Edge", "PUT", f"/edges/{self.test_data['edge_id']}", 
                     {"name": "Updated Edge"}, 200)
    
    def test_jobs_crud(self):
        """Test Jobs APIs in CRUD order"""
        self.log("\n" + "="*80, "info")
        self.log("PHASE 4: JOBS - COMPLETE CRUD TESTING", "info")
        self.log("="*80, "info")
        
        # Ensure we have required data
        if "account_id" not in self.test_data:
            self.log("⚠️  No account_id found, using default ID 1", "warning")
            self.test_data["account_id"] = 1
        
        # CREATE Job
        job_data = {
            "job_name": f"Test Job {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "job_number": f"JOB-{datetime.now().strftime('%H%M%S')}",
            "account_id": self.test_data["account_id"],
            "status_id": 1,
            "priority": "medium",
            "notes": "Test job created by automated test suite"
        }
        
        result = self.test(
            "CREATE Job",
            "POST",
            "/jobs",
            job_data,
            201,
            "Create a new job with all required fields"
        )
        
        if result and result.get("data"):
            self.test_data["job_id"] = result["data"].get("id")
            self.log(f"✅ Created Job ID: {self.test_data['job_id']}", "success")
        else:
            self.log("❌ Failed to create job, cannot continue with job tests", "error")
            return
        
        # READ - List all jobs
        self.test(
            "READ - List All Jobs",
            "GET",
            "/jobs",
            None,
            200,
            "Get all jobs without filters"
        )
        
        # READ - List with filters
        self.test(
            "READ - List Jobs by Account",
            "GET",
            f"/jobs?account_id={self.test_data['account_id']}",
            None,
            200,
            f"Get jobs filtered by account_id={self.test_data['account_id']}"
        )
        
        self.test(
            "READ - List Jobs by Status",
            "GET",
            "/jobs?status_id=1",
            None,
            200,
            "Get jobs filtered by status_id=1"
        )
        
        self.test(
            "READ - List Jobs by Priority",
            "GET",
            "/jobs?priority=medium",
            None,
            200,
            "Get jobs filtered by priority=medium"
        )
        
        # READ - Get single job
        self.test(
            "READ - Get Job by ID",
            "GET",
            f"/jobs/{self.test_data['job_id']}",
            None,
            200,
            f"Get specific job with ID {self.test_data['job_id']}"
        )
        
        # UPDATE Job
        update_data = {
            "job_name": f"Updated Job {datetime.now().strftime('%H%M%S')}",
            "priority": "high",
            "notes": "Job updated by automated test suite"
        }
        
        self.test(
            "UPDATE Job",
            "PUT",
            f"/jobs/{self.test_data['job_id']}",
            update_data,
            200,
            f"Update job name, priority and notes for job {self.test_data['job_id']}"
        )
        
        # Verify update by reading again
        result = self.test(
            "READ - Verify Job Update",
            "GET",
            f"/jobs/{self.test_data['job_id']}",
            None,
            200,
            "Verify that the job was updated correctly"
        )
        
        if result and result.get("data"):
            job = result["data"]
            if job.get("priority") == "high":
                self.log("✅ Job priority correctly updated to 'high'", "success")
            else:
                self.log(f"⚠️  Job priority is '{job.get('priority')}', expected 'high'", "warning")
    
    def test_fabs_crud(self):
        """Test Fabs APIs in CRUD order"""
        self.log("\n" + "="*80, "info")
        self.log("PHASE 5: FABS - COMPLETE CRUD TESTING", "info")
        self.log("="*80, "info")
        
        if "job_id" not in self.test_data:
            self.log("⚠️  No job_id found, skipping fab tests", "warning")
            return
        
        # Get default IDs if not created
        if "stone_type_id" not in self.test_data:
            self.test_data["stone_type_id"] = 1
        if "stone_color_id" not in self.test_data:
            self.test_data["stone_color_id"] = 1
        if "stone_thickness_id" not in self.test_data:
            self.test_data["stone_thickness_id"] = 1
        if "edge_id" not in self.test_data:
            self.test_data["edge_id"] = 1
        
        # CREATE Fab
        fab_data = {
            "job_id": self.test_data["job_id"],
            "fab_type": "kitchen",
            "stone_type_id": self.test_data["stone_type_id"],
            "stone_color_id": self.test_data["stone_color_id"],
            "stone_thickness_id": self.test_data["stone_thickness_id"],
            "edge_id": self.test_data["edge_id"],
            "current_stage": "templating",
            "notes": "Test fab for kitchen countertop"
        }
        
        result = self.test(
            "CREATE Fab",
            "POST",
            "/fabs",
            fab_data,
            201,
            "Create a new fab for the job"
        )
        
        if result and result.get("data"):
            self.test_data["fab_id"] = result["data"].get("id")
            self.log(f"✅ Created Fab ID: {self.test_data['fab_id']}", "success")
        else:
            self.log("❌ Failed to create fab", "error")
            return
        
        # READ - List all fabs
        self.test(
            "READ - List All Fabs",
            "GET",
            "/fabs",
            None,
            200,
            "Get all fabs"
        )
        
        # READ - List fabs by job
        self.test(
            "READ - List Fabs by Job",
            "GET",
            f"/fabs?job_id={self.test_data['job_id']}",
            None,
            200,
            f"Get fabs for job {self.test_data['job_id']}"
        )
        
        # READ - Get single fab
        self.test(
            "READ - Get Fab by ID",
            "GET",
            f"/fabs/{self.test_data['fab_id']}",
            None,
            200,
            f"Get specific fab with ID {self.test_data['fab_id']}"
        )
        
        # UPDATE Fab
        update_data = {
            "current_stage": "pre_draft_review",
            "notes": "Fab updated - moved to pre-draft review"
        }
        
        self.test(
            "UPDATE Fab",
            "PUT",
            f"/fabs/{self.test_data['fab_id']}",
            update_data,
            200,
            f"Update fab stage to pre_draft_review"
        )
    
    def test_workflow_apis(self):
        """Test workflow APIs (Templating, Clockwork, Drafting, etc.)"""
        self.log("\n" + "="*80, "info")
        self.log("PHASE 6: WORKFLOW APIs", "info")
        self.log("="*80, "info")
        
        if "fab_id" not in self.test_data:
            self.log("⚠️  No fab_id found, skipping workflow tests", "warning")
            return
        
        # TEMPLATING
        self.log("\n--- TEMPLATING ---", "info")
        templating_data = {
            "fab_id": self.test_data["fab_id"],
            "scheduled_date": datetime.now().strftime("%Y-%m-%d"),
            "notes": "Test templating schedule"
        }
        
        result = self.test(
            "Schedule Templating",
            "POST",
            "/templating/schedule",
            templating_data,
            201,
            "Schedule templating for the fab"
        )
        
        if result and result.get("data"):
            templating_id = result["data"].get("id")
            self.test_data["templating_id"] = templating_id
            
            # Mark as received
            self.test(
                "Mark Templating Received",
                "POST",
                f"/templating/{templating_id}/mark-received",
                {},
                200,
                "Mark templating as received (should auto-transition fab)"
            )
        
        # CLOCKWORK
        self.log("\n--- CLOCKWORK ---", "info")
        clockwork_data = {
            "fab_id": self.test_data["fab_id"],
            "technician_id": 1,
            "table_name": "drafting",
            "start_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sqft_completed": 50.5
        }
        
        result = self.test(
            "CREATE Clockwork Entry",
            "POST",
            "/clockwork",
            clockwork_data,
            201,
            "Track work time for technician"
        )
        
        if result and result.get("data"):
            clockwork_id = result["data"].get("id")
            
            # List clockwork entries
            self.test(
                "READ Clockwork Entries",
                "GET",
                f"/clockwork?fab_id={self.test_data['fab_id']}",
                None,
                200,
                "Get all clockwork entries for the fab"
            )
            
            # Update clockwork
            self.test(
                "UPDATE Clockwork Entry",
                "PUT",
                f"/clockwork/{clockwork_id}",
                {"sqft_completed": 75.0},
                200,
                "Update sqft completed"
            )
        
        # DRAFTING
        self.log("\n--- DRAFTING ---", "info")
        drafting_data = {
            "fab_id": self.test_data["fab_id"],
            "drafter_id": 1,
            "notes": "Test drafting entry"
        }
        
        result = self.test(
            "CREATE Drafting Entry",
            "POST",
            "/drafting",
            drafting_data,
            201,
            "Create drafting entry"
        )
        
        if result and result.get("data"):
            drafting_id = result["data"].get("id")
            
            # Submit drafting form
            submit_data = {
                "total_sqft_drafted": 100.5,
                "no_of_piece_drafted": 3,
                "mentions": "Test mentions"
            }
            
            self.test(
                "Submit Drafting Form",
                "POST",
                f"/drafting/{drafting_id}/submit",
                submit_data,
                200,
                "Submit drafting with form data"
            )
    
    def test_job_listings(self):
        """Test job listing and fab detail views"""
        self.log("\n" + "="*80, "info")
        self.log("PHASE 7: JOB LISTINGS & FAB DETAILS", "info")
        self.log("="*80, "info")
        
        # Jobs with Fabs listing
        self.test(
            "List Jobs with Fabs",
            "GET",
            "/jobs-with-fabs",
            None,
            200,
            "Get comprehensive job and fab listing"
        )
        
        if "account_id" in self.test_data:
            self.test(
                "List Jobs with Fabs (Filtered by Account)",
                "GET",
                f"/jobs-with-fabs?account_id={self.test_data['account_id']}",
                None,
                200,
                "Get jobs with fabs filtered by account"
            )
        
        # Fab details
        if "fab_id" in self.test_data:
            self.test(
                "Get Fab Details",
                "GET",
                f"/fab/{self.test_data['fab_id']}/details",
                None,
                200,
                f"Get detailed view of fab {self.test_data['fab_id']} with stage-specific data"
            )
    
    def test_delete_operations(self):
        """Test DELETE operations at the end"""
        self.log("\n" + "="*80, "info")
        self.log("PHASE 8: DELETE OPERATIONS (Cleanup)", "info")
        self.log("="*80, "info")
        
        # Delete fab first (since it depends on job)
        if "fab_id" in self.test_data:
            self.test(
                "DELETE Fab",
                "DELETE",
                f"/fabs/{self.test_data['fab_id']}",
                None,
                200,
                f"Delete fab {self.test_data['fab_id']}"
            )
        
        # Delete job
        if "job_id" in self.test_data:
            self.test(
                "DELETE Job",
                "DELETE",
                f"/jobs/{self.test_data['job_id']}",
                None,
                200,
                f"Soft delete job {self.test_data['job_id']}"
            )
        
        # Delete account
        if "account_id" in self.test_data:
            self.test(
                "DELETE Account",
                "DELETE",
                f"/accounts/{self.test_data['account_id']}",
                None,
                200,
                f"Delete account {self.test_data['account_id']}"
            )
    
    def print_summary(self):
        """Print test summary"""
        self.log("\n" + "="*80, "info")
        self.log("TEST SUMMARY", "info")
        self.log("="*80, "info")
        
        total = self.results["passed"] + self.results["failed"]
        pass_rate = (self.results["passed"] / total * 100) if total > 0 else 0
        
        self.log(f"\nTotal Tests: {total}", "info")
        self.log(f"Passed: {self.results['passed']}", "success")
        self.log(f"Failed: {self.results['failed']}", "error")
        self.log(f"Pass Rate: {pass_rate:.1f}%", "success" if pass_rate >= 80 else "warning")
        
        if self.results["failed"] > 0:
            self.log("\n❌ Failed Tests:", "error")
            for test in self.results["tests"]:
                if test["status"] != "PASSED":
                    self.log(f"  - {test['name']}: {test.get('error', test.get('code', 'Unknown'))}", "error")
        
        self.log("\n" + "="*80, "info")

def main():
    tester = APITester()
    
    print(f"\n{Colors.BLUE}{'='*80}")
    print("ALPHA GRANITE BACKEND - COMPREHENSIVE API TEST SUITE")
    print("Testing all APIs in CRUD order with focus on Jobs")
    print(f"{'='*80}{Colors.END}\n")
    
    # Phase 1: Authentication
    if not tester.setup_auth():
        print(f"\n{Colors.RED}Cannot proceed without authentication. Exiting.{Colors.END}")
        return
    
    # Phase 2: Test Accounts (prerequisite for jobs)
    tester.test_accounts()
    
    # Phase 3: Test Stone Resources (prerequisite for fabs)
    tester.test_stone_resources()
    
    # Phase 4: Test Jobs (CRUD order)
    tester.test_jobs_crud()
    
    # Phase 5: Test Fabs (CRUD order)
    tester.test_fabs_crud()
    
    # Phase 6: Test Workflow APIs
    tester.test_workflow_apis()
    
    # Phase 7: Test Job Listings
    tester.test_job_listings()
    
    # Phase 8: Delete operations (cleanup)
    tester.test_delete_operations()
    
    # Print summary
    tester.print_summary()

if __name__ == "__main__":
    main()
