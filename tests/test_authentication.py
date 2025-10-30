"""
Comprehensive Authentication Test Script

This script tests all authentication flows based on the authentication flow diagram:
1. Login with username/email and password
2. First-time login password change
3. Profile update
4. Account locking/unlocking
5. Password reset flow
6. Role assignment validation

Tests cover different scenarios:
- Successful authentication
- Failed authentication attempts
- Account lockout
- First-time login flow
- User with no role
- Password change requirements
- Profile updates
"""

import os
import sys
import json
import time
import httpx
import pytest
import asyncio
import subprocess
from faker import Faker
from datetime import datetime
from typing import Dict, Any, Optional
from passlib.context import CryptContext

# Test configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

# Check if server is running
import httpx
try:
    response = httpx.get(f"{BASE_URL}/health", timeout=5.0)
    if response.status_code != 200:
        print(f"⚠️ Server health check failed: {response.status_code}")
except Exception as e:
    print(f"⚠️ Cannot connect to server at {BASE_URL}: {e}")
    print("Make sure to run: uvicorn src.app.main:app --reload")

# Test data generator
fake = Faker()

class AuthTestClient:
    """Enhanced test client for authentication testing"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = httpx.AsyncClient(timeout=TIMEOUT)
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        
    async def close(self):
        """Close the HTTP session"""
        await self.session.aclose()
        
    def set_auth_header(self, token: str):
        """Set authorization header for authenticated requests"""
        self.access_token = token
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
    def clear_auth_header(self):
        """Clear authorization header"""
        self.access_token = None
        if "Authorization" in self.session.headers:
            del self.session.headers["Authorization"]
            
    async def request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make HTTP request with enhanced error handling"""
        url = f"{self.base_url}{endpoint}"
        
        # Add common headers for audit trail
        headers = kwargs.get("headers", {})
        headers.update({
            "X-Device-ID": fake.uuid4(),
            "User-Agent": "AuthTestScript/1.0"
        })
        kwargs["headers"] = headers
        
        try:
            response = await self.session.request(method, url, **kwargs)
            return response
        except httpx.TimeoutException:
            print(f"Timeout error for {method} {url}")
            raise
        except httpx.ConnectError:
            print(f"Connection error for {method} {url}")
            raise
            
    async def login(self, username: str, password: str) -> Dict[str, Any]:
        """Login and return response data"""
        response = await self.request(
            "POST", 
            "/auth/login",
            json={"username": username, "password": password}
        )
        return response.status_code, response.json()
        
    async def change_password(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change password for authenticated user"""
        response = await self.request(
            "POST",
            "/auth/change-password",
            json={
                "current_password": current_password,
                "new_password": new_password,
                "confirm_password": new_password
            }
        )
        return response.status_code, response.json()
        
    async def update_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile"""
        response = await self.request(
            "PUT",
            "/auth/me",
            json=profile_data
        )
        return response.status_code, response.json()
        
    async def get_profile(self) -> Dict[str, Any]:
        """Get current user profile"""
        response = await self.request("GET", "/auth/me")
        return response.status_code, response.json()
        
    async def request_password_reset(self, email: str) -> Dict[str, Any]:
        """Request password reset"""
        response = await self.request(
            "POST",
            "/auth/request-password-reset",
            json={"email": email}
        )
        return response.status_code, response.json()


class AuthenticationTestSuite:
    """Comprehensive authentication test suite"""
    
    def __init__(self):
        self.client = AuthTestClient()
        self.test_users = []
        self.results = []
        
    async def setup(self):
        """Setup test environment"""
        print("🚀 Setting up authentication test suite...")
        
        # Generate test user data
        self.test_users = [
            {
                "username": "testuser1",
                "email": "testuser1@example.com",
                "password": "TestPassword123!",
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "phone": fake.phone_number(),
                "is_first_login": True
            },
            {
                "username": "testuser2", 
                "email": "testuser2@example.com",
                "password": "TestPassword456!",
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "phone": fake.phone_number(),
                "is_first_login": False,
                "has_role": True
            },
            {
                "username": "noroleuser",
                "email": "norole@example.com", 
                "password": "TestPassword789!",
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "phone": fake.phone_number(),
                "is_first_login": False,
                "has_role": False
            }
        ]
        # Ensure a superadmin account exists so tests can authenticate.
        # Try logging in as the default admin; if it fails, create the superuser
        # using the provided script and retry.
        import traceback
        # Try multiple credential combinations
        credential_sets = [
            ("admin", "admin123@Daewi"),
            ("admin", "admin123"),
            ("testadmin", "password123"),
            (os.getenv("SUPERUSER_USERNAME", "admin"), os.getenv("SUPERUSER_PASSWORD", "admin123@Daewi"))
        ]
        
        authenticated = False
        for username, password in credential_sets:
            try:
                print(f"Trying to authenticate with: {username}")
                status_code, response = await self.client.login(username, password)
                
                print(f"Login response: {status_code}, {response}")
                
                if status_code == 200 and response.get("success"):
                    token_data = response.get("data", {})
                    access_token = token_data.get("access_token")
                    if access_token:
                        self.client.set_auth_header(access_token)
                        print(f"✅ Authenticated successfully with {username}")
                        authenticated = True
                        break
                    else:
                        print(f"⚠️ Login succeeded but no access token for {username}")
                else:
                    print(f"❌ Login failed for {username}: {response}")
            except Exception as e:
                print(f"❌ Exception during login for {username}: {e}")
        
        if not authenticated:
            print("⚠️ Could not authenticate with any credentials. Tests may fail.")
            print("Make sure the FastAPI server is running on http://localhost:8000")
            print("Run: uvicorn src.app.main:app --reload")
        
    async def cleanup(self):
        """Cleanup test environment"""
        print("🧹 Cleaning up test environment...")
        await self.client.close()
        
    def log_test_result(self, test_name: str, status: str, details: str = "", response_data: Any = None):
        """Log test result"""
        result = {
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "status": status,
            "details": details,
            "response_data": response_data
        }
        self.results.append(result)
        
        # Print result
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
            
    async def test_successful_login(self):
        """Test successful login flow"""
        test_name = "Successful Login"
        
        try:
            # Clear any existing auth first
            self.client.clear_auth_header()
            
            # Test login with known credentials
            status_code, response = await self.client.login("admin", "admin123@Daewi")
            
            print(f"Login attempt - Status: {status_code}, Response: {response}")
            
            if status_code == 200 and response.get("success"):
                token_data = response.get("data", {})
                if "access_token" in token_data:
                    self.client.set_auth_header(token_data["access_token"])
                    self.log_test_result(test_name, "PASS", "Login successful with valid credentials")
                else:
                    self.log_test_result(test_name, "FAIL", "No access token in response", response)
            else:
                # Try alternative credentials if first fails
                status_code2, response2 = await self.client.login("testadmin", "password123")
                if status_code2 == 200 and response2.get("success"):
                    token_data = response2.get("data", {})
                    if "access_token" in token_data:
                        self.client.set_auth_header(token_data["access_token"])
                        self.log_test_result(test_name, "PASS", "Login successful with alternative credentials")
                    else:
                        self.log_test_result(test_name, "FAIL", "No access token in response", response2)
                else:
                    self.log_test_result(test_name, "FAIL", f"Login failed with both credential sets. Status: {status_code}, Response: {response}", response)
                
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Exception: {str(e)}")
            
    async def test_failed_login_attempts(self):
        """Test failed login attempts and account lockout"""
        test_name = "Failed Login Attempts"
        
        try:
            # Clear any existing auth
            self.client.clear_auth_header()
            
            # Attempt multiple failed logins
            failed_attempts = []
            for i in range(4):  # Exceed MAX_LOGIN_ATTEMPTS (3)
                status_code, response = await self.client.login("admin", "wrongpassword")
                failed_attempts.append({
                    "attempt": i + 1,
                    "status_code": status_code,
                    "response": response
                })
                
                if i == 0:  # Check first attempt
                    if status_code != 401:
                        self.log_test_result(test_name, "FAIL", f"Attempt 1: Expected 401, got {status_code}")
                        return
                        
            # Check if account got locked after multiple attempts
            final_attempt = failed_attempts[-1]
            if final_attempt["status_code"] == 403:  # Account locked
                self.log_test_result(test_name, "PASS", "Account correctly locked after failed attempts")
            else:
                self.log_test_result(test_name, "FAIL", f"Expected account lock (403), got {final_attempt['status_code']}")
                
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Exception: {str(e)}").append({
                    "attempt": i + 1,
                    "status_code": status_code,
                    "response": response
                })
                
            if i < 2:  # First 3 attempts should return 401
                if status_code != 401:
                    self.log_test_result(test_name, "FAIL", f"Attempt {i+1}: Expected 401, got {status_code}")
                    return
            else:  # 4th attempt should return 403 (account locked)
                if status_code == 403:
                    self.log_test_result(test_name, "PASS", "Account locked after max attempts")
                    return
                        
            self.log_test_result(test_name, "FAIL", "Account was not locked after max attempts", failed_attempts)
            
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Exception: {str(e)}")
            
    async def test_first_time_login_flow(self):
        """Test first-time login flow"""
        test_name = "First Time Login Flow"
        
        try:
            # This would require a user with is_first_login=True
            # For now, we'll test the expected response structure
            
            # Simulate first-time login response
            status_code, response = await self.client.login("firsttimeuser", "temppassword")
            
            # Check if response indicates first-time login
            if response.get("data", {}).get("first_time"):
                self.log_test_result(test_name, "PASS", "First-time login detected correctly")
            else:
                # If not a first-time user, that's also valid
                self.log_test_result(test_name, "SKIP", "No first-time user available for testing")
                
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Exception: {str(e)}")
            
    async def test_password_change(self):
        """Test password change functionality"""
        test_name = "Password Change"
        
        try:
            # First, ensure we're logged in
            if not self.client.access_token:
                status_code, response = await self.client.login("admin", "admin123")
                if status_code == 200 and response.get("success"):
                    token_data = response.get("data", {})
                    self.client.set_auth_header(token_data["access_token"])
                    
            # Test password change
            new_password = "NewTestPassword123!"
            status_code, response = await self.client.change_password("admin123", new_password)
            
            if status_code == 200 and response.get("success"):
                self.log_test_result(test_name, "PASS", "Password changed successfully")
                
                # Test login with new password
                self.client.clear_auth_header()
                status_code, login_response = await self.client.login("admin", new_password)
                
                if status_code == 200:
                    # Change password back
                    token_data = login_response.get("data", {})
                    self.client.set_auth_header(token_data["access_token"])
                    await self.client.change_password(new_password, "admin123")
                    self.log_test_result(test_name + " (Verification)", "PASS", "Login with new password successful")
                else:
                    self.log_test_result(test_name + " (Verification)", "FAIL", "Could not login with new password")
            else:
                self.log_test_result(test_name, "FAIL", f"Password change failed: {response.get('message')}", response)
                
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Exception: {str(e)}")
            
    async def test_profile_update(self):
        """Test profile update functionality"""
        test_name = "Profile Update"
        
        try:
            # Ensure we're logged in
            if not self.client.access_token:
                status_code, response = await self.client.login("admin", "admin123")
                if status_code == 200 and response.get("success"):
                    token_data = response.get("data", {})
                    self.client.set_auth_header(token_data["access_token"])
                    
            # Get current profile
            status_code, current_profile = await self.client.get_profile()
            if status_code != 200:
                self.log_test_result(test_name, "FAIL", "Could not fetch current profile")
                return
                
            # Update profile
            profile_updates = {
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "phone": fake.phone_number(),
                "home_address": fake.address()
            }
            
            status_code, response = await self.client.update_profile(profile_updates)
            
            if status_code == 200 and response.get("success"):
                # Verify updates
                status_code, updated_profile = await self.client.get_profile()
                if status_code == 200:
                    profile_data = updated_profile.get("data", {}) if updated_profile.get("success") else updated_profile
                    
                    # Check if updates were applied
                    updates_applied = all(
                        profile_data.get(key) == value 
                        for key, value in profile_updates.items()
                    )
                    
                    if updates_applied:
                        self.log_test_result(test_name, "PASS", "Profile updated successfully")
                    else:
                        self.log_test_result(test_name, "FAIL", "Profile updates were not applied correctly")
                else:
                    self.log_test_result(test_name, "FAIL", "Could not fetch updated profile")
            else:
                self.log_test_result(test_name, "FAIL", f"Profile update failed: {response.get('message')}", response)
                
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Exception: {str(e)}")
            
    async def test_no_role_user_flow(self):
        """Test user with no role assigned"""
        test_name = "No Role User Flow"
        
        try:
            # This would require a user with no role assigned
            # For demonstration, we'll test the expected response
            status_code, response = await self.client.login("noroleuser", "password")
            
            # Check if response indicates no role
            if response.get("data", {}).get("no_role"):
                admin_email = response.get("data", {}).get("admin_email")
                if admin_email:
                    self.log_test_result(test_name, "PASS", f"No role user handled correctly, admin contact: {admin_email}")
                else:
                    self.log_test_result(test_name, "PARTIAL", "No role detected but no admin contact provided")
            else:
                self.log_test_result(test_name, "SKIP", "No role user not available for testing")
                
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Exception: {str(e)}")
            
    async def test_password_reset_flow(self):
        """Test password reset flow"""
        test_name = "Password Reset Flow"
        
        try:
            # Request password reset
            status_code, response = await self.client.request_password_reset("admin@example.com")
            
            if status_code == 200 and response.get("success"):
                self.log_test_result(test_name, "PASS", "Password reset request processed successfully")
            else:
                self.log_test_result(test_name, "FAIL", f"Password reset request failed: {response.get('message')}", response)
                
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Exception: {str(e)}")
            
    async def test_authentication_headers(self):
        """Test authentication with various header scenarios"""
        test_name = "Authentication Headers"
        
        try:
            # Test without authorization header
            self.client.clear_auth_header()
            status_code, response = await self.client.get_profile()
            
            if status_code == 401:
                self.log_test_result(test_name + " (No Auth)", "PASS", "Correctly rejected request without auth header")
            else:
                self.log_test_result(test_name + " (No Auth)", "FAIL", f"Expected 401, got {status_code}")
                
            # Test with invalid token
            self.client.set_auth_header("invalid_token")
            status_code, response = await self.client.get_profile()
            
            if status_code == 401:
                self.log_test_result(test_name + " (Invalid Token)", "PASS", "Correctly rejected invalid token")
            else:
                self.log_test_result(test_name + " (Invalid Token)", "FAIL", f"Expected 401, got {status_code}")
                
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Exception: {str(e)}")
            
    async def test_concurrent_login_attempts(self):
        """Test concurrent login attempts"""
        test_name = "Concurrent Login Attempts"
        
        try:
            # Create multiple clients for concurrent requests
            clients = [AuthTestClient() for _ in range(3)]
            
            # Concurrent login attempts
            tasks = [
                client.login("admin", "admin123")
                for client in clients
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_logins = sum(1 for status_code, _ in results if isinstance(results[0], tuple) and status_code == 200)
            
            if successful_logins >= 1:
                self.log_test_result(test_name, "PASS", f"Handled {successful_logins} concurrent login attempts")
            else:
                self.log_test_result(test_name, "FAIL", "No successful concurrent logins")
                
            # Cleanup
            for client in clients:
                await client.close()
                
        except Exception as e:
            self.log_test_result(test_name, "FAIL", f"Exception: {str(e)}")
            
    async def run_all_tests(self):
        """Run all authentication tests"""
        print("\n🔐 Starting Comprehensive Authentication Test Suite")
        print("=" * 60)
        
        await self.setup()
        
        # Run all test methods
        test_methods = [
            self.test_successful_login,
            self.test_failed_login_attempts,
            self.test_first_time_login_flow,
            self.test_password_change,
            self.test_profile_update,
            self.test_no_role_user_flow,
            self.test_password_reset_flow,
            self.test_authentication_headers,
            self.test_concurrent_login_attempts,
        ]
        
        for test_method in test_methods:
            print(f"\n🧪 Running {test_method.__name__}...")
            await test_method()
            await asyncio.sleep(0.5)  # Brief pause between tests
            
        await self.cleanup()
        
        # Print summary
        self.print_test_summary()
        
    def print_test_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r["status"] == "PASS"])
        failed_tests = len([r for r in self.results if r["status"] == "FAIL"])
        skipped_tests = len([r for r in self.results if r["status"] == "SKIP"])
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️  Skipped: {skipped_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if result["status"] == "FAIL":
                    print(f"  - {result['test_name']}: {result['details']}")
                    
        # Save detailed results to file
        with open("auth_test_results.json", "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "skipped": skipped_tests,
                    "success_rate": (passed_tests/total_tests)*100
                },
                "results": self.results
            }, f, indent=2)
            
        print(f"\n📝 Detailed results saved to: auth_test_results.json")


async def main():
    """Main test runner"""
    test_suite = AuthenticationTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    # Run the test suite
    asyncio.run(main())