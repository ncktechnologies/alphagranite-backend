#!/usr/bin/env python3
"""Test drafting endpoints with fixes"""

import asyncio
import httpx
import io

async def test():
    base_url = 'http://localhost:8005'
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Login
        print("Logging in...")
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
        
        # Test 1: POST /api/v1/drafting/4/files
        print("=" * 60)
        print("TEST 1: File upload to drafting")
        print("=" * 60)
        
        test_file = io.BytesIO(b'Test content')
        files = {'files': ('test.jpg', test_file, 'image/jpeg')}
        
        response1 = await client.post('/api/v1/drafting/4/files', headers=headers, files=files)
        print(f'Status: {response1.status_code}')
        if response1.status_code == 200:
            print(f'✅ Response: {response1.json()}')
        else:
            print(f'❌ Response: {response1.text[:300]}\n')
        
        # Test 2: PUT /api/v1/drafting/4 - with corrected types
        print("\n" + "=" * 60)
        print("TEST 2: Update drafting")
        print("=" * 60)
        
        update_data = {
            "drafter_start_date": "2025-11-26T19:51:07.548Z",
            "drafter_end_date": "2025-11-26T19:51:41.037Z",
            "total_sqft_drafted": 14.0,  # Changed to float
            "no_of_piece_drafted": 1,    # Changed to int
            "draft_note": None,
            "is_completed": True,
            "status_id": 1
        }
        
        response2 = await client.put('/api/v1/drafting/4', headers=headers, json=update_data)
        print(f'Status: {response2.status_code}')
        if response2.status_code == 200:
            print(f'✅ Response: {response2.json()["message"]}')
        else:
            print(f'❌ Response: {response2.text[:300]}')
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f'File upload: {"✅ PASS" if response1.status_code == 200 else "❌ FAIL"}')
        print(f'Update drafting: {"✅ PASS" if response2.status_code == 200 else "❌ FAIL"}')

if __name__ == "__main__":
    asyncio.run(test())
