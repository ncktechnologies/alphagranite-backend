#!/usr/bin/env python3
"""
Simple Authentication Test Runner

This script provides a simplified way to test the authentication APIs
with different scenarios from the authentication flow diagram.

Usage:
    python run_auth_tests.py

Requirements:
    pip install httpx faker
"""

import sys
import json
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.test_authentication import AuthenticationTestSuite

def print_banner():
    """Print test banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════╗
║                   ALPHA GRANITE BACKEND                       ║
║               Authentication Test Suite                       ║
║                                                               ║
║  Testing authentication flows based on the diagram:          ║
║  • Login with username/email and password                    ║
║  • First-time login password change                          ║
║  • Profile updates                                            ║
║  • Account locking/unlocking                                 ║
║  • Password reset flow                                        ║
║  • Role assignment validation                                ║
╚═══════════════════════════════════════════════════════════════╝
"""
    print(banner)

async def check_server_health():
    """Check if the server is running"""
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # ensure we hit the canonical health endpoint (trailing slash)
            response = await client.get("http://localhost:8000/health/")
            if response.status_code == 200:
                print("✅ Server is running and healthy")
                return True
    except Exception as e:
        print(f"❌ Server health check failed: {e}")
        print("💡 Make sure the FastAPI server is running on http://localhost:8000")
        return False
    
    return False

async def run_specific_test(test_name: str):
    """Run a specific test"""
    test_suite = AuthenticationTestSuite()
    await test_suite.setup()
    
    test_methods = {
        "login": test_suite.test_successful_login,
        "failed_login": test_suite.test_failed_login_attempts,
        "first_time": test_suite.test_first_time_login_flow,
        "password_change": test_suite.test_password_change,
        "profile_update": test_suite.test_profile_update,
        "no_role": test_suite.test_no_role_user_flow,
        "password_reset": test_suite.test_password_reset_flow,
        "auth_headers": test_suite.test_authentication_headers,
        "concurrent": test_suite.test_concurrent_login_attempts,
    }
    
    if test_name in test_methods:
        print(f"🧪 Running specific test: {test_name}")
        await test_methods[test_name]()
        test_suite.print_test_summary()
    else:
        print(f"❌ Test '{test_name}' not found. Available tests:")
        for name in test_methods.keys():
            print(f"   - {name}")
    
    await test_suite.cleanup()

async def main():
    """Main function"""
    print_banner()
    
    # Check if server is running
    if not await check_server_health():
        return
    
    # Check command line arguments
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        await run_specific_test(test_name)
    else:
        # Run all tests
        test_suite = AuthenticationTestSuite()
        await test_suite.run_all_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error running tests: {e}")
        sys.exit(1)