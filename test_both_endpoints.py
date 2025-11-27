#!/usr/bin/env python3
"""Test both drafting endpoints"""

import asyncio
import httpx
import io

async def test():
    base_url = 'http://localhost:8005'
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Login
        login_response = await client.post('/auth/login', json={
            'username': 'admin', 
            'password': 'admin123@Daewi1'
        })
        
        if login_response.status_code != 200:
            print(f'Login failed: {login_response.text}')
            return
        
        token = login_response.json()['data']['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print('✅ Login successful\n')
        
        # Test 1: File upload
        print("=" * 60)
        print("TEST 1: POST /api/v1/drafting/4/files")
        print("=" * 60)
        
        test_file = io.BytesIO(b'Test file content')
        files = {'files': ('test.jpg', test_file, 'image/jpeg')}
        
        r1 = await client.post('/api/v1/drafting/4/files', headers=headers, files=files)
        print(f'Status: {r1.status_code}')
        if r1.status_code == 200:
            print(f'✅ SUCCESS: {r1.json()}\n')
        else:
            print(f'❌ FAILED: {r1.text[:500]}\n')
        
        # Test 2: Update drafting
        print("=" * 60)
        print("TEST 2: PUT /api/v1/drafting/4")
        print("=" * 60)
        
        update_data = {
            "drafter_start_date": "2025-11-26T19:51:07.548Z",
            "drafter_end_date": "2025-11-26T19:51:41.037Z",
            "total_sqft_drafted": 14.0,
            "no_of_piece_drafted": 1,
            "draft_note": None,
            "is_completed": True,
            "status_id": 1
        }
        
        r2 = await client.put('/api/v1/drafting/4', headers=headers, json=update_data)
        print(f'Status: {r2.status_code}')
        if r2.status_code == 200:
            print(f'✅ SUCCESS: {r2.json()["message"]}\n')
        else:
            print(f'❌ FAILED: {r2.text[:500]}\n')
        
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f'Test 1 (File upload): {"✅ PASS" if r1.status_code == 200 else "❌ FAIL"}')
        print(f'Test 2 (Update): {"✅ PASS" if r2.status_code == 200 else "❌ FAIL"}')

if __name__ == "__main__":
    asyncio.run(test())
