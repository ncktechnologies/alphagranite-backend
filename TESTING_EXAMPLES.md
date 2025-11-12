# API Testing Examples - cURL Commands

This document provides example cURL commands to test all the implemented APIs.

## Prerequisites

1. Start the FastAPI server:
```powershell
uvicorn src.app.main:app --reload
```

2. Get a JWT token by logging in (replace with your credentials):
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_password"
  }'
```

3. Copy the returned token and use it in the `Authorization` header below (replace `YOUR_JWT_TOKEN`)

---

## 1. Jobs API

### Create a Job
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Kitchen Remodel - Smith Residence",
    "job_number": "JOB-2025-001",
    "account_id": 1,
    "description": "Complete kitchen countertop replacement",
    "priority": "High"
  }'
```

### Get All Jobs
```bash
curl -X GET "http://localhost:8000/api/v1/jobs?limit=10" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Job by ID
```bash
curl -X GET "http://localhost:8000/api/v1/jobs/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update a Job
```bash
curl -X PUT "http://localhost:8000/api/v1/jobs/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "priority": "Urgent",
    "description": "Rush order - customer needs it ASAP"
  }'
```

### Delete a Job
```bash
curl -X DELETE "http://localhost:8000/api/v1/jobs/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 2. Accounts API

### Create an Account
```bash
curl -X POST "http://localhost:8000/api/v1/accounts" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Smith Construction",
    "account_number": "ACC-2025-001",
    "contact_person": "John Smith",
    "email": "john@smithconstruction.com",
    "phone": "555-1234",
    "address": "123 Main St, Anytown, USA"
  }'
```

### Get All Accounts
```bash
curl -X GET "http://localhost:8000/api/v1/accounts" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Search Accounts
```bash
curl -X GET "http://localhost:8000/api/v1/accounts?search=Smith" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Account by ID
```bash
curl -X GET "http://localhost:8000/api/v1/accounts/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update an Account
```bash
curl -X PUT "http://localhost:8000/api/v1/accounts/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "555-9999",
    "email": "john.smith@smithconstruction.com"
  }'
```

---

## 3. Stone Thickness API

### Get All Stone Thicknesses
```bash
curl -X GET "http://localhost:8000/api/v1/stone-thickness" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Stone Thickness by ID
```bash
curl -X GET "http://localhost:8000/api/v1/stone-thickness/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update Stone Thickness
```bash
curl -X PUT "http://localhost:8000/api/v1/stone-thickness/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "thickness": "3/4 inch",
    "thickness_mm": 19.05,
    "description": "Standard thickness - most popular"
  }'
```

### Delete Stone Thickness
```bash
curl -X DELETE "http://localhost:8000/api/v1/stone-thickness/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 4. Stone Colors API

### Get All Stone Colors
```bash
curl -X GET "http://localhost:8000/api/v1/stone-colors" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Search Stone Colors
```bash
curl -X GET "http://localhost:8000/api/v1/stone-colors?search=Kashmir" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Stone Color by ID
```bash
curl -X GET "http://localhost:8000/api/v1/stone-colors/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update Stone Color
```bash
curl -X PUT "http://localhost:8000/api/v1/stone-colors/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Kashmir White Premium",
    "color_code": "#F5F5DC",
    "description": "Premium grade Kashmir White granite"
  }'
```

---

## 5. Stone Types API

### Get All Stone Types
```bash
curl -X GET "http://localhost:8000/api/v1/stone-types" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Stone Type by ID
```bash
curl -X GET "http://localhost:8000/api/v1/stone-types/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update Stone Type
```bash
curl -X PUT "http://localhost:8000/api/v1/stone-types/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Granite - Premium",
    "description": "Premium grade natural granite"
  }'
```

---

## 6. Edges API

### Get All Edges
```bash
curl -X GET "http://localhost:8000/api/v1/edges" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Edge by ID
```bash
curl -X GET "http://localhost:8000/api/v1/edges/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Filter by Edge Type
```bash
curl -X GET "http://localhost:8000/api/v1/edges?edge_type=Rounded" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update Edge
```bash
curl -X PUT "http://localhost:8000/api/v1/edges/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bullnose - Standard",
    "edge_type": "Rounded",
    "description": "Classic rounded edge - most popular choice"
  }'
```

---

## 7. Fab Types API

### Get Fab Types (Predefined List)
```bash
curl -X GET "http://localhost:8000/api/v1/fab-types" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 8. Fabs API

### Create a Fab
```bash
curl -X POST "http://localhost:8000/api/v1/fabs" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "fab_type": "Kitchen Countertop",
    "sales_person_id": 5,
    "stone_type_id": 1,
    "stone_color_id": 3,
    "stone_thickness_id": 2,
    "edge_id": 4,
    "input_area": "Kitchen - Main Counter",
    "total_sqft": 45.5,
    "notes": "Customer wants undermount sink cutout",
    "template_needed": true,
    "drafting_needed": true,
    "slab_smith_cust_needed": false,
    "slab_smith_ag_needed": true,
    "sct_needed": true,
    "final_programming_needed": false
  }'
```

### Get All Fabs
```bash
curl -X GET "http://localhost:8000/api/v1/fabs" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Fabs by Job ID
```bash
curl -X GET "http://localhost:8000/api/v1/jobs/1/fabs" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Filter Fabs by Sales Person
```bash
curl -X GET "http://localhost:8000/api/v1/fabs?sales_person_id=5" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Fab by ID
```bash
curl -X GET "http://localhost:8000/api/v1/fabs/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Update Fab
```bash
curl -X PUT "http://localhost:8000/api/v1/fabs/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "total_sqft": 48.0,
    "notes": "Updated measurements - added extra counter space",
    "current_stage": "templating",
    "template_needed": false
  }'
```

### Delete Fab
```bash
curl -X DELETE "http://localhost:8000/api/v1/fabs/1" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## Complete Workflow Example

### Step 1: Create an Account
```bash
curl -X POST "http://localhost:8000/api/v1/accounts" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ABC Builders",
    "account_number": "ACC-2025-100",
    "contact_person": "Jane Doe",
    "email": "jane@abcbuilders.com",
    "phone": "555-5555"
  }'
```

### Step 2: Create a Job
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Downtown Condo - Unit 401",
    "job_number": "JOB-2025-100",
    "account_id": 1,
    "priority": "Medium"
  }'
```

### Step 3: Get Available Options
```bash
# Get stone types
curl -X GET "http://localhost:8000/api/v1/stone-types" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get stone colors
curl -X GET "http://localhost:8000/api/v1/stone-colors" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get stone thicknesses
curl -X GET "http://localhost:8000/api/v1/stone-thickness" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get edges
curl -X GET "http://localhost:8000/api/v1/edges" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Get fab types
curl -X GET "http://localhost:8000/api/v1/fab-types" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Step 4: Create Fab with Selected Options
```bash
curl -X POST "http://localhost:8000/api/v1/fabs" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": 1,
    "fab_type": "Kitchen Countertop",
    "sales_person_id": 5,
    "stone_type_id": 1,
    "stone_color_id": 2,
    "stone_thickness_id": 1,
    "edge_id": 3,
    "input_area": "Main Kitchen",
    "total_sqft": 52.0,
    "notes": "Modern kitchen with waterfall edge on island",
    "template_needed": false,
    "drafting_needed": false,
    "slab_smith_cust_needed": false,
    "slab_smith_ag_needed": false,
    "sct_needed": false,
    "final_programming_needed": false
  }'
```

### Step 5: Verify Fab Creation
```bash
curl -X GET "http://localhost:8000/api/v1/jobs/1/fabs" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## PowerShell Examples

For Windows PowerShell users, use `Invoke-RestMethod`:

### Login Example
```powershell
$loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"username":"admin","password":"your_password"}'

$token = $loginResponse.access_token
```

### Create Job Example
```powershell
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}

$body = @{
    name = "Test Job"
    job_number = "JOB-001"
    account_id = 1
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/jobs" `
  -Method Post `
  -Headers $headers `
  -Body $body
```

### Get Jobs Example
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/jobs" `
  -Method Get `
  -Headers @{"Authorization" = "Bearer $token"}
```

---

## Notes

- Replace `YOUR_JWT_TOKEN` with the actual token from login
- Replace IDs (1, 2, etc.) with actual IDs from your database
- All timestamps should be in ISO 8601 format: `2025-01-15T08:00:00`
- Use `-v` flag with curl for verbose output and debugging
- Status codes:
  - 200: Success (GET, PUT)
  - 201: Created (POST)
  - 204: No Content (DELETE)
  - 400: Bad Request (validation errors)
  - 401: Unauthorized (missing/invalid token)
  - 404: Not Found
  - 422: Unprocessable Entity (schema validation errors)
