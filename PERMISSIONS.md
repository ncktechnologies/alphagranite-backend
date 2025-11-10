# Permission System Documentation

## Overview

The Alpha Granite Backend implements a role-based access control (RBAC) system that checks user permissions before allowing access to protected resources.

## How It Works

### 1. Permission Checker Middleware

The `PermissionChecker` class is a FastAPI dependency that validates user permissions based on:
- **Resource**: The entity being accessed (e.g., "employees", "departments", "roles")
- **Action**: The operation being performed (e.g., "create", "read", "update", "delete")

### 2. Super Admin Bypass

Users with `is_super_admin=True` automatically bypass all permission checks and have full access to all resources.

### 3. Role-Based Permissions

For non-super-admin users, the system:
1. Checks if the user has a role assigned
2. Looks up the resource in the `action_menus` table using the resource code
3. Queries the `role_permissions` table to find permissions for the user's role and resource
4. Validates that the specific action (create/read/update/delete) is allowed

## Database Schema

### Tables Involved

1. **users**: Contains user information including `role_id` and `is_super_admin`
2. **roles**: Defines available roles
3. **action_menus**: Defines resources with unique codes (e.g., "employees", "departments")
4. **permissions**: Defines CRUD permissions (can_create, can_read, can_update, can_delete)
5. **role_permissions**: Junction table linking roles to permissions for specific resources

## Usage in Routers

### Basic Example

```python
from fastapi import APIRouter, Depends
from src.app.utils.permissions import PermissionChecker
from src.app.database.user import User

router = APIRouter()

@router.post("/employees")
async def create_employee(
    current_user: User = Depends(PermissionChecker("employees", "create")),
    db: AsyncSession = Depends(get_db)
):
    # Only users with "create" permission on "employees" resource can access this
    pass

@router.get("/employees/{id}")
async def get_employee(
    employee_id: int,
    current_user: User = Depends(PermissionChecker("employees", "read")),
    db: AsyncSession = Depends(get_db)
):
    # Only users with "read" permission on "employees" resource can access this
    pass

@router.put("/employees/{id}")
async def update_employee(
    employee_id: int,
    current_user: User = Depends(PermissionChecker("employees", "update")),
    db: AsyncSession = Depends(get_db)
):
    # Only users with "update" permission on "employees" resource can access this
    pass

@router.delete("/employees/{id}")
async def delete_employee(
    employee_id: int,
    current_user: User = Depends(PermissionChecker("employees", "delete")),
    db: AsyncSession = Depends(get_db)
):
    # Only users with "delete" permission on "employees" resource can access this
    pass
```

## Resource Codes

The following resource codes are currently implemented:

- `employees` - Employee management
- `departments` - Department management
- `roles` - Role management

## Actions

The system supports four standard CRUD actions:

- `create` - Create new records
- `read` - View/retrieve records
- `update` - Modify existing records
- `delete` - Remove records

## Exceptions

The following routes do NOT require permission checks:

1. **Authentication routes** (`/auth/*`)
   - Login, logout, password reset, etc.

2. **Health check** (`/health`)
   - System health monitoring

3. **Status fetching** (`/departments/statuses`)
   - Fetching lookup data like status values

4. **File retrieval** (`/files/*` GET endpoints)
   - Accessing uploaded files

## Error Responses

### 403 Forbidden - No Role Assigned
```json
{
  "detail": "User has no role assigned"
}
```

### 403 Forbidden - Resource Not Found
```json
{
  "detail": "Resource 'employees' not found"
}
```

### 403 Forbidden - No Access to Resource
```json
{
  "detail": "Access denied to resource 'employees'"
}
```

### 403 Forbidden - Action Not Permitted
```json
{
  "detail": "Permission denied: cannot create employees"
}
```

## Setting Up Permissions

### 1. Create Action Menu Entry

```sql
INSERT INTO action_menus (name, code, created_at, updated_at)
VALUES ('Employees', 'employees', NOW(), NOW());
```

### 2. Create Permission

```sql
INSERT INTO permissions (name, description, can_create, can_read, can_update, can_delete, created_at, updated_at)
VALUES ('Employee Management', 'Full CRUD access to employees', true, true, true, true, NOW(), NOW());
```

### 3. Link Role to Permission

```sql
INSERT INTO role_permissions (role_id, permission_id, action_menu_id, created_at, updated_at)
VALUES (1, 1, 1, NOW(), NOW());
```

## Best Practices

1. **Always use PermissionChecker** for protected routes instead of just `get_current_user`
2. **Use consistent resource codes** across your application
3. **Document resource codes** when adding new protected resources
4. **Test with non-super-admin users** to ensure permissions work correctly
5. **Keep action_menus.code values lowercase** and use underscores for multi-word resources

## Migration from get_current_user

If you have existing routes using `get_current_user`, update them to use `PermissionChecker`:

### Before
```python
@router.post("/employees")
async def create_employee(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    pass
```

### After
```python
@router.post("/employees")
async def create_employee(
    current_user: User = Depends(PermissionChecker("employees", "create")),
    db: AsyncSession = Depends(get_db)
):
    pass
```

The `current_user` object remains the same - it's still a `User` model instance with all the same attributes.
