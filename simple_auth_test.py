"""Simple authentication test to verify bcrypt fix"""
import httpx
import sys

BASE_URL = "http://localhost:8000"

def test_login():
    """Test login with admin credentials"""
    print("Testing login with admin credentials...")
    
    try:
        response = httpx.post(
            f"{BASE_URL}/auth/login",
            json={"username": "admin", "password": "admin123@Daewi"},
            headers={
                "X-Device-ID": "test-device",
                "User-Agent": "TestScript/1.0"
            },
            timeout=10.0
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                print("\n[PASS] Login successful!")
                return True
            else:
                print(f"\n[FAIL] Login failed: {data.get('message')}")
                return False
        else:
            print(f"\n[FAIL] HTTP {response.status_code}: {response.json()}")
            return False
            
    except httpx.ConnectError:
        print("\n[ERROR] Cannot connect to server. Make sure it's running:")
        print("  uvicorn src.app.main:app --reload")
        return False
    except Exception as e:
        print(f"\n[ERROR] Exception: {e}")
        return False

if __name__ == "__main__":
    success = test_login()
    sys.exit(0 if success else 1)
