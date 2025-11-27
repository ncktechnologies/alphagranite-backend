#!/usr/bin/env python3
"""
Comprehensive verification and testing script.
This script will:
1. Check database connection
2. Verify column types in draftings table
3. Test both endpoints
"""

import asyncio
import httpx
import io
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://admin:Admin@Gr@n1+e!@93.114.128.181:5432/alpha_granite"

async def verify_database_schema():
    """Check if the database columns have been migrated"""
    print("\n" + "="*60)
    print("DATABASE SCHEMA VERIFICATION")
    print("="*60)
    
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            # Check column types
            result = conn.execute(text("""
                SELECT 
                    column_name, 
                    data_type, 
                    udt_name
                FROM information_schema.columns 
                WHERE table_name = 'draftings' 
                AND column_name IN ('total_sqft_drafted', 'no_of_piece_drafted')
                ORDER BY column_name;
            """))
            
            print("\nCurrent column types in 'draftings' table:")
            print("-" * 60)
            
            columns = result.fetchall()
            schema_ok = True
            
            for col in columns:
                col_name, data_type, udt_name = col
                print(f"  {col_name}: {data_type} ({udt_name})")
                
                # Verify types
                if col_name == 'total_sqft_drafted' and udt_name != 'numeric':
                    print(f"    ❌ Expected: numeric, Got: {udt_name}")
                    schema_ok = False
                elif col_name == 'no_of_piece_drafted' and udt_name not in ['int4', 'integer']:
                    print(f"    ❌ Expected: integer, Got: {udt_name}")
                    schema_ok = False
                else:
                    print(f"    ✅ Correct type")
            
            print()
            if schema_ok:
                print("✅ Database schema is correct!")
                return True
            else:
                print("❌ Database schema needs migration!")
                print("\nRun this command to apply the migration:")
                print("  alembic upgrade head")
                return False
                
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False


async def test_endpoints():
    """Test both problematic endpoints"""
    base_url = 'http://localhost:8005'
    
    print("\n" + "="*60)
    print("ENDPOINT TESTING")
    print("="*60)
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Login
        print("\n1. Authenticating...")
        login_response = await client.post('/auth/login', json={
            'username': 'admin', 
            'password': 'admin123@Daewi1'
        })
        
        if login_response.status_code != 200:
            print(f'❌ Login failed: {login_response.text}')
            return False, False
        
        token = login_response.json()['data']['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print('✅ Login successful')
        
        # Test 1: File upload
        print("\n2. Testing POST /api/v1/drafting/4/files (File Upload)")
        print("-" * 60)
        
        test_file = io.BytesIO(b'Test file content for drafting')
        files = {'files': ('test_draft.jpg', test_file, 'image/jpeg')}
        
        r1 = await client.post('/api/v1/drafting/4/files', headers=headers, files=files)
        
        test1_pass = r1.status_code == 200
        
        if test1_pass:
            print(f'✅ Status: {r1.status_code}')
            print(f'Response: {r1.json()["message"]}')
        else:
            print(f'❌ Status: {r1.status_code}')
            print(f'Error: {r1.text[:300]}')
        
        # Test 2: Update drafting
        print("\n3. Testing PUT /api/v1/drafting/4 (Update Drafting)")
        print("-" * 60)
        
        update_data = {
            "drafter_start_date": "2025-11-27T10:00:00.000Z",
            "drafter_end_date": "2025-11-27T15:30:00.000Z",
            "total_sqft_drafted": 25.5,
            "no_of_piece_drafted": 3,
            "draft_note": "Test update with numeric types and timezone handling",
            "is_completed": True,
            "status_id": 1
        }
        
        r2 = await client.put('/api/v1/drafting/4', headers=headers, json=update_data)
        
        test2_pass = r2.status_code == 200
        
        if test2_pass:
            print(f'✅ Status: {r2.status_code}')
            print(f'Response: {r2.json()["message"]}')
        else:
            print(f'❌ Status: {r2.status_code}')
            print(f'Error: {r2.text[:300]}')
        
        return test1_pass, test2_pass


async def main():
    print("\n" + "="*60)
    print("DRAFTING ENDPOINTS - COMPREHENSIVE VERIFICATION")
    print("="*60)
    
    # Step 1: Verify database schema
    schema_ok = await verify_database_schema()
    
    if not schema_ok:
        print("\n⚠️  Warning: Database schema not migrated yet.")
        print("The tests may fail due to incorrect column types.")
        print("\nDo you want to continue with tests anyway? (y/n): ", end='')
        
        # For automated runs, we'll continue
        # In interactive mode, you could add input() here
    
    # Step 2: Test endpoints
    test1_pass, test2_pass = await test_endpoints()
    
    # Summary
    print("\n" + "="*60)
    print("FINAL SUMMARY")
    print("="*60)
    print(f"Database Schema: {'✅ READY' if schema_ok else '❌ NEEDS MIGRATION'}")
    print(f"Test 1 (File Upload): {'✅ PASS' if test1_pass else '❌ FAIL'}")
    print(f"Test 2 (Update Drafting): {'✅ PASS' if test2_pass else '❌ FAIL'}")
    
    if schema_ok and test1_pass and test2_pass:
        print("\n🎉 All checks passed! Both endpoints are working correctly.")
        return 0
    else:
        print("\n⚠️  Some checks failed. See details above.")
        if not schema_ok:
            print("\nNext step: Run 'alembic upgrade head' to apply database migration")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
