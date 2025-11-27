#!/usr/bin/env python3
"""Test drafting endpoints that are throwing 500 errors"""

import asyncio
import httpx
import io

async def test_drafting_endpoints():
    base_url = 'http://api.ag.easybusiness.ng:8000'
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Login
        print("Logging in...")
        login_response = await client.post('/auth/login', json={
            'username': 'admin', 
            'password': 'admin123@Daewi1'
        })
        print(f'Login: {login_response.status_code}')
        
        if login_response.status_code != 200:
            print(f'Login failed: {login_response.text}')
            return
        
        token = login_response.json()['data']['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        print('✅ Login successful\n')
        
        # Test 1: POST /api/v1/drafting/4/files (file upload)
        print("=" * 60)
        print("TEST 1: POST /api/v1/drafting/4/files (file upload)")
        print("=" * 60)
        
        # Create a test file
        test_file = io.BytesIO(b'Test image content')
        files = {'files': ('test.jpg', test_file, 'image/jpeg')}
        
        response1 = await client.post(
            '/api/v1/drafting/4/files',
            headers=headers,
            files=files
        )
        
        print(f'Status: {response1.status_code}')
        print(f'Response: {response1.text[:500]}\n')
        
        # Test 2: PUT /api/v1/drafting/4 (update drafting)
        print("=" * 60)
        print("TEST 2: PUT /api/v1/drafting/4 (update)")
        print("=" * 60)
        
        update_data = {
            "drafter_start_date": "2025-11-26T19:51:07.548Z",
            "drafter_end_date": "2025-11-26T19:51:41.037Z",
            "total_sqft_drafted": "14",
            "no_of_piece_drafted": "1",
            "draft_note": None,
            "is_completed": True,
            "status_id": 1
        }
        
        response2 = await client.put(
            '/api/v1/drafting/4',
            headers=headers,
            json=update_data
        )
        
        print(f'Status: {response2.status_code}')
        print(f'Response: {response2.text[:500]}\n')
        
        # Summary
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f'Endpoint 1 (file upload): {response1.status_code}')
        print(f'Endpoint 2 (update): {response2.status_code}')

if __name__ == "__main__":
    asyncio.run(test_drafting_endpoints())
