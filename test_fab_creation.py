#!/usr/bin/env python3
"""Test FAB creation with float input_area"""

import asyncio
import httpx

async def test_fab_creation():
    base_url = 'https://live-star-goldfish.ngrok-free.app'
    
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        # Login
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
        
        # Get test data - handle different response formats
        jobs = (await client.get('/api/v1/jobs', headers=headers)).json()
        
        colors_resp = (await client.get('/api/v1/stone-colors', headers=headers)).json()
        colors = colors_resp['data'] if isinstance(colors_resp, dict) else colors_resp
        
        types_resp = (await client.get('/api/v1/stone-types', headers=headers)).json()
        types = types_resp['data'] if isinstance(types_resp, dict) else types_resp
        
        thickness_resp = (await client.get('/api/v1/stone-thickness', headers=headers)).json()
        thickness_list = thickness_resp['data'] if isinstance(thickness_resp, dict) else thickness_resp
        
        edges_resp = (await client.get('/api/v1/edges', headers=headers)).json()
        edges = edges_resp['data'] if isinstance(edges_resp, dict) else edges_resp
        
        sales_resp = (await client.get('/api/v1/users/sales-persons', headers=headers)).json()
        sales_persons = sales_resp['data'] if isinstance(sales_resp, dict) else sales_resp
        
        print(f'Retrieved test data:')
        print(f'  Jobs: {len(jobs)} available')
        print(f'  Colors: {len(colors)} available')
        print(f'  Types: {len(types)} available')
        print(f'  Thickness: {len(thickness_list)} available')
        print(f'  Edges: {len(edges)} available')
        print(f'  Sales Persons: {len(sales_persons)} available\n')
        
        # Create FAB with float input_area (this is the key fix)
        fab_data = {
            'job_id': jobs[0]['id'],
            'fab_type': 'Test Kitchen Countertop',
            'sales_person_id': sales_persons[0]['id'],
            'stone_type_id': types[0]['id'],
            'stone_color_id': colors[0]['id'],
            'stone_thickness_id': thickness_list[0]['id'],
            'edge_id': edges[0]['id'],
            'input_area': 45.5,  # FLOAT, not string
            'total_sqft': 50.0,
            'notes': 'Test FAB - verifying float input_area works',
            'template_needed': True,
            'drafting_needed': True,
            'slab_smith_cust_needed': False,
            'slab_smith_ag_needed': True,
            'sct_needed': True,
            'final_programming_needed': True
        }
        
        print('Creating FAB with float input_area=45.5...')
        response = await client.post('/api/v1/fabs', json=fab_data, headers=headers)
        print(f'Status: {response.status_code}\n')
        
        if response.status_code in [200, 201]:
            result = response.json()['data']
            print(f'✅ FAB CREATED SUCCESSFULLY!')
            print(f'='*50)
            print(f'FAB ID: {result["id"]}')
            print(f'Input Area: {result["input_area"]} (Python type: {type(result["input_area"]).__name__})')
            print(f'Total SqFt: {result["total_sqft"]}')
            print(f'Current Stage: {result["current_stage"]}')
            print(f'Next Stage: {result["next_stage"]}')
            print(f'FAB Type: {result["fab_type"]}')
            print(f'='*50)
            print('\n✅ TEST PASSED: input_area field now accepts floats!')
        else:
            print(f'❌ FAB CREATION FAILED!')
            print(f'Response: {response.text[:500]}')

if __name__ == "__main__":
    asyncio.run(test_fab_creation())
