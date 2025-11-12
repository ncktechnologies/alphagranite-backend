# API Endpoints Summary

This document provides a comprehensive overview of all the API endpoints created for the Alpha Granite Backend system.

## Base URL
All endpoints are prefixed with `/api/v1`

## Authentication
All endpoints require JWT authentication. Include the Bearer token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## 1. Jobs API

### Create Job
- **Endpoint**: `POST /api/v1/jobs`
- **Description**: Create a new job
- **Request Body**:
```json
{
  "name": "Kitchen Remodel - Smith Residence",
  "job_number": "JOB-2025-001",
  "account_id": 1,
  "description": "Complete kitchen countertop replacement",
  "priority": "High",
  "start_date": "2025-01-15T08:00:00",
  "due_date": "2025-01-30T17:00:00"
}
```
- **Response**: `201 Created` with job details

### Get All Jobs
- **Endpoint**: `GET /api/v1/jobs`
- **Description**: Get list of all jobs with optional filtering
- **Query Parameters**:
  - `skip`: Number of records to skip (default: 0)
  - `limit`: Number of records to return (default: 100, max: 1000)
  - `account_id`: Filter by account ID
  - `status_id`: Filter by status ID
  - `priority`: Filter by priority (Low, Medium, High, Urgent)
- **Response**: `200 OK` with array of jobs

### Get Job by ID
- **Endpoint**: `GET /api/v1/jobs/{job_id}`
- **Description**: Get a specific job by ID
- **Response**: `200 OK` with job details

### Update Job
- **Endpoint**: `PUT /api/v1/jobs/{job_id}`
- **Description**: Update an existing job
- **Request Body**: Same as Create Job (all fields optional)
- **Response**: `200 OK` with updated job details

### Delete Job
- **Endpoint**: `DELETE /api/v1/jobs/{job_id}`
- **Description**: Soft delete a job (sets status to deleted)
- **Response**: `204 No Content`

---

## 2. Accounts API

### Create Account
- **Endpoint**: `POST /api/v1/accounts`
- **Description**: Create a new account
- **Request Body**:
```json
{
  "name": "Smith Construction",
  "account_number": "ACC-2025-001",
  "description": "General contractor for residential projects",
  "contact_person": "John Smith",
  "email": "john@smithconstruction.com",
  "phone": "555-1234",
  "address": "123 Main St, Anytown, USA"
}
```
- **Response**: `201 Created` with account details

### Get All Accounts
- **Endpoint**: `GET /api/v1/accounts`
- **Description**: Get list of all accounts
- **Query Parameters**:
  - `skip`: Number of records to skip (default: 0)
  - `limit`: Number of records to return (default: 100, max: 1000)
  - `status_id`: Filter by status ID
  - `search`: Search by name or account number
- **Response**: `200 OK` with array of accounts

### Get Account by ID
- **Endpoint**: `GET /api/v1/accounts/{account_id}`
- **Description**: Get a specific account by ID
- **Response**: `200 OK` with account details

### Update Account
- **Endpoint**: `PUT /api/v1/accounts/{account_id}`
- **Description**: Update an existing account
- **Request Body**: Same as Create Account (all fields optional)
- **Response**: `200 OK` with updated account details

### Delete Account
- **Endpoint**: `DELETE /api/v1/accounts/{account_id}`
- **Description**: Soft delete an account
- **Response**: `204 No Content`

---

## 3. Stone Thickness API

### Create Stone Thickness
- **Endpoint**: `POST /api/v1/stone-thickness`
- **Description**: Create a new stone thickness option
- **Request Body**:
```json
{
  "thickness": "3/4 inch",
  "thickness_mm": 19.05,
  "description": "Standard granite thickness"
}
```
- **Response**: `201 Created` with stone thickness details

### Get All Stone Thicknesses
- **Endpoint**: `GET /api/v1/stone-thickness`
- **Description**: Get list of all stone thickness options
- **Query Parameters**:
  - `skip`: Number of records to skip
  - `limit`: Number of records to return
  - `status_id`: Filter by status ID
- **Response**: `200 OK` with array of stone thicknesses

### Get Stone Thickness by ID
- **Endpoint**: `GET /api/v1/stone-thickness/{thickness_id}`
- **Description**: Get a specific stone thickness by ID
- **Response**: `200 OK` with stone thickness details

### Update Stone Thickness
- **Endpoint**: `PUT /api/v1/stone-thickness/{thickness_id}`
- **Description**: Update an existing stone thickness
- **Request Body**: Same as Create (all fields optional)
- **Response**: `200 OK` with updated details

### Delete Stone Thickness
- **Endpoint**: `DELETE /api/v1/stone-thickness/{thickness_id}`
- **Description**: Soft delete a stone thickness
- **Response**: `204 No Content`

---

## 4. Stone Colors API

### Create Stone Color
- **Endpoint**: `POST /api/v1/stone-colors`
- **Description**: Create a new stone color
- **Request Body**:
```json
{
  "name": "Kashmir White",
  "color_code": "#F5F5DC",
  "description": "Light colored granite with subtle pattern"
}
```
- **Response**: `201 Created` with stone color details

### Get All Stone Colors
- **Endpoint**: `GET /api/v1/stone-colors`
- **Description**: Get list of all stone colors
- **Query Parameters**:
  - `skip`: Number of records to skip
  - `limit`: Number of records to return
  - `status_id`: Filter by status ID
  - `search`: Search by name
- **Response**: `200 OK` with array of stone colors

### Get Stone Color by ID
- **Endpoint**: `GET /api/v1/stone-colors/{color_id}`
- **Description**: Get a specific stone color by ID
- **Response**: `200 OK` with stone color details

### Update Stone Color
- **Endpoint**: `PUT /api/v1/stone-colors/{color_id}`
- **Description**: Update an existing stone color
- **Request Body**: Same as Create (all fields optional)
- **Response**: `200 OK` with updated details

### Delete Stone Color
- **Endpoint**: `DELETE /api/v1/stone-colors/{color_id}`
- **Description**: Soft delete a stone color
- **Response**: `204 No Content`

---

## 5. Stone Types API

### Create Stone Type
- **Endpoint**: `POST /api/v1/stone-types`
- **Description**: Create a new stone type
- **Request Body**:
```json
{
  "name": "Granite",
  "description": "Natural granite stone"
}
```
- **Response**: `201 Created` with stone type details

### Get All Stone Types
- **Endpoint**: `GET /api/v1/stone-types`
- **Description**: Get list of all stone types
- **Query Parameters**:
  - `skip`: Number of records to skip
  - `limit`: Number of records to return
  - `status_id`: Filter by status ID
  - `search`: Search by name
- **Response**: `200 OK` with array of stone types

### Get Stone Type by ID
- **Endpoint**: `GET /api/v1/stone-types/{type_id}`
- **Description**: Get a specific stone type by ID
- **Response**: `200 OK` with stone type details

### Update Stone Type
- **Endpoint**: `PUT /api/v1/stone-types/{type_id}`
- **Description**: Update an existing stone type
- **Request Body**: Same as Create (all fields optional)
- **Response**: `200 OK` with updated details

### Delete Stone Type
- **Endpoint**: `DELETE /api/v1/stone-types/{type_id}`
- **Description**: Soft delete a stone type
- **Response**: `204 No Content`

---

## 6. Edges API

### Create Edge
- **Endpoint**: `POST /api/v1/edges`
- **Description**: Create a new edge type
- **Request Body**:
```json
{
  "name": "Bullnose",
  "edge_type": "Rounded",
  "description": "Rounded edge finish"
}
```
- **Response**: `201 Created` with edge details

### Get All Edges
- **Endpoint**: `GET /api/v1/edges`
- **Description**: Get list of all edge types
- **Query Parameters**:
  - `skip`: Number of records to skip
  - `limit`: Number of records to return
  - `status_id`: Filter by status ID
  - `edge_type`: Filter by edge type
  - `search`: Search by name
- **Response**: `200 OK` with array of edges

### Get Edge by ID
- **Endpoint**: `GET /api/v1/edges/{edge_id}`
- **Description**: Get a specific edge by ID
- **Response**: `200 OK` with edge details

### Update Edge
- **Endpoint**: `PUT /api/v1/edges/{edge_id}`
- **Description**: Update an existing edge
- **Request Body**: Same as Create (all fields optional)
- **Response**: `200 OK` with updated details

### Delete Edge
- **Endpoint**: `DELETE /api/v1/edges/{edge_id}`
- **Description**: Soft delete an edge
- **Response**: `204 No Content`

---

## 7. Fab Types API

### Get Fab Types
- **Endpoint**: `GET /api/v1/fab-types`
- **Description**: Get list of predefined fabrication types
- **Response**: `200 OK` with array of fab types
```json
[
  {
    "name": "Kitchen Countertop",
    "description": "Standard kitchen counter fabrication"
  },
  {
    "name": "Bathroom Vanity",
    "description": "Bathroom vanity top fabrication"
  }
]
```

---

## 8. Fabs API

### Create Fab
- **Endpoint**: `POST /api/v1/fabs`
- **Description**: Create a new fabrication order
- **Request Body**:
```json
{
  "job_id": 1,
  "fab_type": "Kitchen Countertop",
  "sales_person_id": 5,
  "stone_type_id": 1,
  "stone_color_id": 3,
  "stone_thickness_id": 2,
  "edge_id": 4,
  "input_area": "Kitchen - Main Counter",
  "total_sqft": 45.5,
  "notes": "Customer wants undermount sink",
  "template_needed": true,
  "drafting_needed": true,
  "slab_smith_cust_needed": false,
  "slab_smith_ag_needed": true,
  "sct_needed": true,
  "final_programming_needed": true
}
```
- **Response**: `201 Created` with fab details

### Get All Fabs
- **Endpoint**: `GET /api/v1/fabs`
- **Description**: Get list of all fabs with optional filtering
- **Query Parameters**:
  - `skip`: Number of records to skip
  - `limit`: Number of records to return
  - `job_id`: Filter by job ID
  - `fab_type`: Filter by fab type
  - `sales_person_id`: Filter by sales person ID
  - `status_id`: Filter by status ID
  - `current_stage`: Filter by current stage
- **Response**: `200 OK` with array of fabs

### Get Fab by ID
- **Endpoint**: `GET /api/v1/fabs/{fab_id}`
- **Description**: Get a specific fab by ID
- **Response**: `200 OK` with fab details

### Get Fabs by Job
- **Endpoint**: `GET /api/v1/jobs/{job_id}/fabs`
- **Description**: Get all fabs for a specific job
- **Query Parameters**:
  - `skip`: Number of records to skip
  - `limit`: Number of records to return
- **Response**: `200 OK` with array of fabs

### Update Fab
- **Endpoint**: `PUT /api/v1/fabs/{fab_id}`
- **Description**: Update an existing fab
- **Request Body**: Same as Create (all fields optional)
- **Response**: `200 OK` with updated details

### Delete Fab
- **Endpoint**: `DELETE /api/v1/fabs/{fab_id}`
- **Description**: Soft delete a fab
- **Response**: `204 No Content`

---

## Common Response Fields

All entities include these tracking fields:
- `id`: Unique identifier
- `status_id`: Status identifier (1=Active, 3=Deleted)
- `created_at`: Creation timestamp
- `created_by`: User ID who created the record
- `updated_at`: Last update timestamp (nullable)
- `updated_by`: User ID who last updated the record (nullable)

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Workflow Integration

Based on the provided diagrams:

### Creating a Job Workflow
1. **POST** `/api/v1/jobs` - Create job with name, job_number, and account_id
2. Job is created and ready for fab creation

### Creating a Fab Workflow
1. **GET** `/api/v1/jobs` - Select job (or use job_id from job creation)
2. **GET** `/api/v1/fab-types` - Select fab type
3. **GET** `/api/v1/accounts` - Get account info (already linked via job)
4. **GET** `/api/v1/stone-types` - Select stone type
5. **GET** `/api/v1/stone-colors` - Select stone color
6. **GET** `/api/v1/stone-thickness` - Select stone thickness
7. **GET** `/api/v1/edges` - Select edge type
8. **POST** `/api/v1/fabs` - Create fab with all selected options and process step flags

### Updating Fab Workflow
1. **GET** `/api/v1/fabs/{fab_id}` - Get current fab details
2. **PUT** `/api/v1/fabs/{fab_id}` - Update fab details or process flags
3. Status changes can be tracked via `status_id` and `current_stage` fields

---

## Testing with Swagger UI

Access the interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

Use the "Authorize" button to add your JWT token for testing.
