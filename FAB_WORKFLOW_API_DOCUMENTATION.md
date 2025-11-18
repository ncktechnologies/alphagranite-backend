# FAB Workflow API Documentation

**Version**: 1.0  
**Date**: November 18, 2025  
**Backend Base URL**: `https://your-api-domain.com/api/v1`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Workflow Stages](#workflow-stages)
4. [Data Types & Notes](#data-types--notes)
5. [FAB Management APIs](#fab-management-apis)
6. [Templating Workflow APIs](#templating-workflow-apis)
7. [Drafting Workflow APIs](#drafting-workflow-apis)
8. [Pre-Draft Review APIs](#pre-draft-review-apis)
9. [Slab Smith Workflow APIs](#slab-smith-workflow-apis)
10. [Sales Check (Sales CT) APIs](#sales-check-sales-ct-apis)
11. [Cut List APIs](#cut-list-apis)
12. [Final Programming APIs](#final-programming-apis)
13. [Shop Planning APIs](#shop-planning-apis)
14. [Supporting Resources APIs](#supporting-resources-apis)
15. [Error Handling](#error-handling)
16. [Complete Workflow Example](#complete-workflow-example)

---

## Overview

The FAB (Fabrication) Workflow system manages the complete lifecycle of fabrication jobs from creation through production. Each FAB progresses through multiple stages, with specific APIs for each stage.

### Key Concepts

- **FAB ID**: Unique identifier for each fabrication request
- **Job**: Container for one or more FABs (from Moreware system)
- **Workflow Stages**: Sequential stages a FAB moves through
- **current_stage**: Where the FAB currently is in the workflow
- **next_stage**: Where the FAB will move to next
- **Notes**: Array of strings capturing history at each stage
- **Status**: State of work at each stage (Active, Completed, Pending, etc.)

---

## Authentication

All API requests (except health checks) require JWT authentication.

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  }
}
```

### Using the Token

Include the access token in all subsequent requests:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Workflow Stages

FABs progress through the following stages in order:

| Stage               | Description                                  | Who Works on It      |
| ------------------- | -------------------------------------------- | -------------------- |
| `fab_created`       | Initial creation, ready for templating       | Coordinator          |
| `templating`        | Templating scheduled/in progress             | Templater Technician |
| `pre_draft_review`  | Post-templating review                       | Coordinator          |
| `drafting`          | CAD drafting in progress                     | Drafter              |
| `sales_check`       | Sales department review                      | Salesperson          |
| `revision`          | Revisions needed (loops back to sales_check) | Drafter              |
| `cut_list`          | Scheduling for shop cut date                 | Coordinator          |
| `final_programming` | Final CNC programming                        | Programmer           |
| `shop_planning`     | Final stage before fabrication               | Production Team      |

**Stage Progression:**

```
fab_created → templating → pre_draft_review → drafting → sales_check
                                                              ↓
                                                           revision (loops back)
                                                              ↓
cut_list → final_programming → shop_planning
```

---

## Data Types & Notes

### Important Field Types

#### Notes Field (⚠️ BREAKING CHANGE)

**Notes are now ARRAYS, not strings!**

```javascript
// ❌ OLD (No longer works)
{
  "notes": "This is a note"
}

// ✅ NEW (Required format)
{
  "notes": ["This is a note"]
}

// Multiple notes
{
  "notes": ["First note", "Second note", "Third note"]
}
```

**Notes Behavior:**

- When creating/updating: Send array of strings
- When appending (completion endpoints): New notes are added to existing array
- Empty array `[]` is valid
- `null` is valid (no notes)

#### Date/Time Fields

All dates use ISO 8601 format:

```json
{
  "schedule_start_date": "2025-11-20T08:00:00",
  "schedule_due_date": "2025-11-22T17:00:00"
}
```

---

## FAB Management APIs

### 1. Create FAB

**Endpoint:** `POST /fabs`

**Description:** Create a new fabrication request

**Request Body:**

```json
{
  "job_id": 5,
  "fab_type": "standard",
  "sales_person_id": 10,
  "stone_type_id": 3,
  "stone_color_id": 7,
  "stone_thickness_id": 2,
  "edge_id": 4,
  "input_area": "Kitchen countertop and island",
  "total_sqft": 120.5,
  "notes": [
    "Customer prefers dark granite",
    "Rush job - requested completion by end of month"
  ],
  "template_needed": true,
  "drafting_needed": true,
  "slab_smith_cust_needed": false,
  "slab_smith_ag_needed": true,
  "sct_needed": true,
  "final_programming_needed": true
}
```

**Response:** `201 Created`

```json
{
  "success": true,
  "message": "FAB 25 submitted successfully for review!",
  "data": {
    "id": 25,
    "job_id": 5,
    "fab_type": "standard",
    "sales_person_id": 10,
    "sales_person_name": "John Doe",
    "stone_type_id": 3,
    "stone_type_name": "Granite",
    "stone_color_id": 7,
    "stone_color_name": "Absolute Black",
    "stone_thickness_id": 2,
    "stone_thickness_value": "3cm",
    "edge_id": 4,
    "edge_name": "Bullnose",
    "input_area": "Kitchen countertop and island",
    "total_sqft": 120.5,
    "notes": [
      "Customer prefers dark granite",
      "Rush job - requested completion by end of month"
    ],
    "template_needed": true,
    "drafting_needed": true,
    "slab_smith_cust_needed": false,
    "slab_smith_ag_needed": true,
    "sct_needed": true,
    "final_programming_needed": true,
    "current_stage": "fab_created",
    "next_stage": "templating",
    "status_id": 1,
    "created_at": "2025-11-18T10:30:00",
    "created_by": 2,
    "updated_at": null,
    "updated_by": null,
    "templating_schedule_start_date": null,
    "templating_schedule_due_date": null,
    "templating_notes": null,
    "technician_name": null
  }
}
```

### 2. Get All FABs (List with Filtering)

**Endpoint:** `GET /fabs`

**Description:** Get list of FABs with optional filters. Returns templating data for each FAB.

**Query Parameters:**

- `skip` (optional): Number of records to skip (default: 0)
- `limit` (optional): Number of records to return (default: 100, max: 1000)
- `job_id` (optional): Filter by job ID
- `fab_type` (optional): Filter by fab type
- `sales_person_id` (optional): Filter by salesperson
- `status_id` (optional): Filter by status
- `current_stage` (optional): Filter by workflow stage ⭐ **USE THIS TO GET FABS AT SPECIFIC STAGES**

**Examples:**

```http
# Get all FABs in templating stage
GET /fabs?current_stage=templating

# Get all FABs for a specific job
GET /fabs?job_id=5

# Get FABs in drafting stage, paginated
GET /fabs?current_stage=drafting&skip=0&limit=20

# Get all FABs awaiting sales check
GET /fabs?current_stage=sales_check
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Fabs fetched successfully",
  "data": [
    {
      "id": 25,
      "job_id": 5,
      "fab_type": "standard",
      "current_stage": "templating",
      "next_stage": "pre_draft_review",
      "sales_person_name": "John Doe",
      "stone_type_name": "Granite",
      "stone_color_name": "Absolute Black",
      "stone_thickness_value": "3cm",
      "edge_name": "Bullnose",
      "total_sqft": 120.5,
      "notes": ["Customer prefers dark granite"],
      "templating_schedule_start_date": "2025-11-20T08:00:00",
      "templating_schedule_due_date": "2025-11-22T17:00:00",
      "templating_notes": ["Customer prefers morning appointment", "Special access code: 1234"],
      "technician_name": "Mike Johnson",
      "created_at": "2025-11-18T10:30:00",
      ...
    }
  ]
}
```

### 3. Get Single FAB

**Endpoint:** `GET /fabs/{fab_id}`

**Description:** Get detailed information about a specific FAB, including templating data

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Fab fetched successfully",
  "data": {
    "id": 25,
    "job_id": 5,
    "fab_type": "standard",
    "sales_person_id": 10,
    "sales_person_name": "John Doe",
    "stone_type_id": 3,
    "stone_type_name": "Granite",
    "stone_color_id": 7,
    "stone_color_name": "Absolute Black",
    "stone_thickness_id": 2,
    "stone_thickness_value": "3cm",
    "edge_id": 4,
    "edge_name": "Bullnose",
    "input_area": "Kitchen countertop and island",
    "total_sqft": 120.5,
    "notes": ["Customer prefers dark granite"],
    "template_needed": true,
    "drafting_needed": true,
    "current_stage": "templating",
    "next_stage": "pre_draft_review",
    "status_id": 1,
    "templating_schedule_start_date": "2025-11-20T08:00:00",
    "templating_schedule_due_date": "2025-11-22T17:00:00",
    "templating_notes": ["Customer prefers morning", "Access code: 1234"],
    "technician_name": "Mike Johnson",
    "created_at": "2025-11-18T10:30:00",
    "updated_at": "2025-11-18T14:20:00"
  }
}
```

### 4. Update FAB

**Endpoint:** `PUT /fabs/{fab_id}`

**Description:** Update FAB details

**Request Body:** (All fields optional)

```json
{
  "stone_color_id": 8,
  "total_sqft": 125.0,
  "notes": [
    "Updated square footage after site visit",
    "Customer changed stone color"
  ]
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Fab updated successfully",
  "data": {
    "id": 25,
    "stone_color_id": 8,
    "stone_color_name": "Kashmir White",
    "total_sqft": 125.0,
    "notes": ["Updated square footage after site visit", "Customer changed stone color"],
    ...
  }
}
```

### 5. Delete FAB

**Endpoint:** `DELETE /fabs/{fab_id}`

**Response:** `204 No Content`

### 6. Get FABs by Job

**Endpoint:** `GET /jobs/{job_id}/fabs`

**Description:** Get all FABs for a specific job

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Fabs fetched successfully",
  "data": [
    {
      "id": 25,
      "job_id": 5,
      "fab_type": "standard",
      ...
    },
    {
      "id": 26,
      "job_id": 5,
      "fab_type": "fast_track",
      ...
    }
  ]
}
```

### 7. Get FAB Details (Extended)

**Endpoint:** `GET /fab/{fab_id}/details`

**Description:** Get comprehensive FAB details with all related data

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "FAB details fetched successfully",
  "data": {
    "fab": {...},
    "templating": {...},
    "drafting": {...},
    "sales_ct": {...},
    ...
  }
}
```

---

## Templating Workflow APIs

### 1. Schedule Templating

**Endpoint:** `POST /templating/schedule`

**Description:** Coordinator schedules templating for a FAB and assigns a technician

**Request Body:**

```json
{
  "fab_id": 25,
  "technician_id": 15,
  "schedule_start_date": "2025-11-20T08:00:00",
  "schedule_due_date": "2025-11-22T17:00:00",
  "total_sqft": "120",
  "notes": ["Customer available mornings only", "Gate code: 1234"]
}
```

**Response:** `201 Created`

```json
{
  "success": true,
  "message": "Templating scheduled successfully",
  "data": {
    "id": 42,
    "fab_id": 25,
    "technician_id": 15,
    "technician_name": "Mike Johnson",
    "schedule_start_date": "2025-11-20T08:00:00",
    "schedule_due_date": "2025-11-22T17:00:00",
    "total_sqft": "120",
    "notes": ["Customer available mornings only", "Gate code: 1234"],
    "is_templating_schedule": true,
    "status_id": 1,
    "status_name": "Active",
    "created_at": "2025-11-18T14:30:00",
    "updated_at": null,
    "updated_by": null
  }
}
```

**Side Effects:**

- FAB `current_stage` → `"templating"`
- FAB `next_stage` → `"pre_draft_review"`

### 2. Complete Templating (Technician) ⭐ NEW

**Endpoint:** `POST /templating/{templating_id}/complete`

**Description:** Technician marks templating work as complete after finishing in Moreware

**Request Body:**

```json
{
  "actual_sqft": "125.5",
  "notes": [
    "Template completed successfully",
    "Customer requested changes to island layout"
  ]
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Templating marked as complete",
  "data": {
    "id": 42,
    "fab_id": 25,
    "technician_id": 15,
    "technician_name": "Mike Johnson",
    "schedule_start_date": "2025-11-20T08:00:00",
    "schedule_due_date": "2025-11-22T17:00:00",
    "total_sqft": "125.5",
    "notes": [
      "Customer available mornings only",
      "Gate code: 1234",
      "Template completed successfully",
      "Customer requested changes to island layout"
    ],
    "is_templating_schedule": true,
    "status_id": 2,
    "status_name": "Completed",
    "created_at": "2025-11-18T14:30:00",
    "updated_at": "2025-11-20T16:45:00",
    "updated_by": 15
  }
}
```

**Behavior:**

- Updates `total_sqft` with actual measured value
- **Appends** new notes to existing notes array (preserves full history)
- Sets `status_id` to 2 (Completed)
- Records timestamp and user who completed

### 3. Update Templating Schedule

**Endpoint:** `PUT /templating/{templating_id}`

**Description:** Update templating details (reschedule, reassign technician, etc.)

**Request Body:** (All fields optional)

```json
{
  "technician_id": 16,
  "schedule_start_date": "2025-11-21T09:00:00",
  "schedule_due_date": "2025-11-23T17:00:00",
  "notes": ["Rescheduled due to customer request"]
}
```

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Templating updated successfully",
  "data": {
    "id": 42,
    "technician_id": 16,
    "technician_name": "Sarah Williams",
    "schedule_start_date": "2025-11-21T09:00:00",
    "schedule_due_date": "2025-11-23T17:00:00",
    "notes": ["Rescheduled due to customer request"],
    "status_id": 1,
    "status_name": "Active",
    ...
  }
}
```

### 4. Mark Templating Received (Coordinator)

**Endpoint:** `POST /templating/{templating_id}/mark-received`

**Description:** Coordinator marks templating results as received and moves FAB to pre-draft review

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Templating marked as received, moved to pre-draft review",
  "data": null
}
```

**Side Effects:**

- FAB `current_stage` → `"pre_draft_review"`
- FAB `next_stage` → `"drafting"`

### 5. Unschedule Templating

**Endpoint:** `PUT /templating/{templating_id}/unschedule`

**Description:** Cancel templating schedule and revert FAB to created state

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Templating unscheduled successfully",
  "data": null
}
```

**Side Effects:**

- FAB `current_stage` → `"fab_created"`
- FAB `next_stage` → `"templating"`
- Templating record is soft-deleted or marked inactive

### 6. Get Templating by ID

**Endpoint:** `GET /templating/{templating_id}`

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Templating fetched successfully",
  "data": {
    "id": 42,
    "fab_id": 25,
    "technician_id": 15,
    "technician_name": "Mike Johnson",
    "schedule_start_date": "2025-11-20T08:00:00",
    "schedule_due_date": "2025-11-22T17:00:00",
    "total_sqft": "125.5",
    "notes": ["Customer available mornings only", "Template completed"],
    "status_id": 2,
    "status_name": "Completed",
    ...
  }
}
```

### 7. Get Templating by FAB ID

**Endpoint:** `GET /templating/fab/{fab_id}`

**Description:** Get templating details for a specific FAB

**Response:** `200 OK` (same structure as Get Templating by ID)

---

## Drafting Workflow APIs

### 1. Create Drafting Assignment

**Endpoint:** `POST /drafting`

**Description:** Assign drafter to a FAB (usually after pre-draft review)

**Request Body:**

```json
{
  "fab_id": 25,
  "drafter_id": 12
}
```

**Response:** `201 Created`

```json
{
  "success": true,
  "message": "Drafting assignment created successfully",
  "data": {
    "id": 55,
    "fab_id": 25,
    "drafter_id": 12,
    "drafter_name": "Alex Thompson",
    "scheduled_start_date": "2025-11-23T09:00:00",
    "scheduled_end_date": "2025-11-25T17:00:00",
    "status_id": 1,
    "status_name": "In Progress",
    "created_at": "2025-11-22T10:00:00"
  }
}
```

**Side Effects:**

- FAB `current_stage` → `"drafting"`
- FAB `next_stage` → `"sales_check"`

### 2. Update Drafting

**Endpoint:** `PUT /drafting/{drafting_id}`

**Description:** Update drafting details

**Request Body:**

```json
{
  "notes": ["Updated layout per customer feedback", "Changed edge profile"]
}
```

**Response:** `200 OK`

### 3. Submit Drafting for Sales Check

**Endpoint:** `POST /drafting/{drafting_id}/submit`

**Description:** Drafter submits completed draft for sales review

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Drafting submitted for sales check",
  "data": {
    "id": 55,
    "status_id": 2,
    "status_name": "Completed",
    ...
  }
}
```

**Side Effects:**

- FAB `current_stage` → `"sales_check"`
- FAB `next_stage` → `"cut_list"` (if approved) or `"revision"` (if changes needed)

### 4. Add File to Drafting

**Endpoint:** `POST /drafting/{drafting_id}/add-file`

**Request Body:**

```json
{
  "file_id": 101
}
```

**Response:** `200 OK`

### 5. Delete File from Drafting

**Endpoint:** `DELETE /drafting/{drafting_id}/file/{file_id}`

**Response:** `200 OK`

### 6. Get Drafting by ID

**Endpoint:** `GET /drafting/{drafting_id}`

**Response:** `200 OK`

### 7. Get Drafting by FAB ID

**Endpoint:** `GET /drafting/fab/{fab_id}`

**Response:** `200 OK`

---

## Pre-Draft Review APIs

### 1. Create Pre-Draft Review

**Endpoint:** `POST /pre-draft-review`

**Description:** Create pre-draft review record

**Request Body:**

```json
{
  "fab_id": 25
}
```

**Response:** `201 Created`

### 2. Complete Pre-Draft Review

**Endpoint:** `POST /pre-draft-review/{review_id}/complete`

**Description:** Mark review as complete and move to drafting

**Response:** `200 OK`

**Side Effects:**

- FAB `current_stage` → `"drafting"`
- FAB `next_stage` → `"sales_check"`

### 3. Set Redraft Needed

**Endpoint:** `POST /pre-draft-review/{review_id}/set-redraft`

**Description:** Indicate that redrafting is needed

**Request Body:**

```json
{
  "reason": "Missing sink cutout dimensions"
}
```

**Response:** `200 OK`

**Side Effects:**

- FAB `current_stage` → `"templating"`
- FAB `next_stage` → `"pre_draft_review"`

### 4. Get Pre-Draft Review by FAB

**Endpoint:** `GET /pre-draft-review/fab/{fab_id}`

**Response:** `200 OK`

---

## Slab Smith Workflow APIs

### 1. Create Slab Smith Record

**Endpoint:** `POST /slabsmith`

**Request Body:**

```json
{
  "fab_id": 25
}
```

**Response:** `201 Created`

### 2. Update Slab Smith

**Endpoint:** `PUT /slabsmith/{slabsmith_id}`

**Request Body:**

```json
{
  "notes": ["Slab selected and marked"]
}
```

**Response:** `200 OK`

### 3. Complete Slab Smith

**Endpoint:** `POST /slabsmith/{slabsmith_id}/complete`

**Description:** Mark slab smith work as complete

**Response:** `200 OK`

**Side Effects:**

- FAB `current_stage` → `"sales_check"`
- FAB `next_stage` → `"cut_list"` or `"revision"`

### 4. Add File to Slab Smith

**Endpoint:** `POST /slabsmith/{slabsmith_id}/add-file`

**Request Body:**

```json
{
  "file_id": 102
}
```

**Response:** `200 OK`

### 5. Delete File from Slab Smith

**Endpoint:** `DELETE /slabsmith/{slabsmith_id}/file/{file_id}`

**Response:** `200 OK`

### 6. Get Slab Smith by FAB

**Endpoint:** `GET /slabsmith/fab/{fab_id}`

**Response:** `200 OK`

---

## Sales Check (Sales CT) APIs

### 1. Create Sales Check

**Endpoint:** `POST /sales-ct`

**Request Body:**

```json
{
  "fab_id": 25
}
```

**Response:** `201 Created`

### 2. Review - No Revision Needed

**Endpoint:** `PUT /sales-ct/{sales_ct_id}/review-no`

**Description:** Sales approves draft, no revisions needed

**Response:** `200 OK`

**Side Effects:**

- FAB `current_stage` → `"cut_list"`
- FAB `next_stage` → `"final_programming"`

### 3. Review - Revision Needed

**Endpoint:** `PUT /sales-ct/{sales_ct_id}/review-yes`

**Description:** Sales requests revisions

**Response:** `200 OK`

**Side Effects:**

- FAB `current_stage` → `"revision"`
- FAB `next_stage` → `"sales_check"`

### 4. Update Revision Details

**Endpoint:** `PUT /sales-ct/{sales_ct_id}/revision`

**Request Body:**

```json
{
  "reason": "Customer changed edge profile to ogee"
}
```

**Response:** `200 OK`

### 5. Get Sales CT by FAB

**Endpoint:** `GET /sales-ct/fab/{fab_id}`

**Response:** `200 OK`

---

## Cut List APIs

### 1. Update Cut List Details

**Endpoint:** `POST /cutlist/{cutlist_id}/update-details`

**Request Body:**

```json
{
  "notes": ["Scheduled for shop on Monday"]
}
```

**Response:** `200 OK`

---

## Final Programming APIs

### 1. Add Files to Final Programming

**Endpoint:** `POST /finalprogramming/{fp_id}/files`

**Request Body:**

```json
{
  "file_id": 105
}
```

**Response:** `200 OK`

### 2. Delete File from Final Programming

**Endpoint:** `DELETE /finalprogramming/{fp_id}/files/{file_id}`

**Response:** `200 OK`

### 3. Update Final Programming

**Endpoint:** `POST /finalprogramming/{fp_id}/update`

**Request Body:**

```json
{
  "notes": ["CNC files generated and verified"]
}
```

**Response:** `200 OK`

---

## Shop Planning APIs

### 1. Create Shop Plan

**Endpoint:** `POST /shop-planning`

**Request Body:**

```json
{
  "fab_id": 25,
  "plan_date": "2025-11-30T08:00:00"
}
```

**Response:** `201 Created`

### 2. Update Shop Plan

**Endpoint:** `PUT /shop-planning/{shop_plan_id}`

**Request Body:**

```json
{
  "notes": ["Priority job - complete first"]
}
```

**Response:** `200 OK`

### 3. Delete Shop Plan

**Endpoint:** `DELETE /shop-planning/{shop_plan_id}`

**Response:** `204 No Content`

### 4. Get Shop Plan by ID

**Endpoint:** `GET /shop-planning/{shop_plan_id}`

**Response:** `200 OK`

### 5. Get All Shop Plans

**Endpoint:** `GET /shop-planning`

**Response:** `200 OK`

### Shop Planning Sections

**Base Path:** `/shop-planning-section`

- `POST /shop-planning-section` - Create section
- `GET /shop-planning-section` - Get all sections
- `GET /shop-planning-section/{section_id}` - Get by ID
- `PUT /shop-planning-section/{section_id}` - Update section
- `DELETE /shop-planning-section/{section_id}` - Delete section

---

## Supporting Resources APIs

### Stone Types

**Base Path:** `/stone-types`

```http
GET /stone-types
POST /stone-types
GET /stone-types/{type_id}
PUT /stone-types/{type_id}
DELETE /stone-types/{type_id}
```

**Example Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Granite",
      "created_at": "2025-01-01T00:00:00"
    },
    {
      "id": 2,
      "name": "Marble",
      "created_at": "2025-01-01T00:00:00"
    }
  ]
}
```

### Stone Colors

**Base Path:** `/stone-colors`

```http
GET /stone-colors
POST /stone-colors
GET /stone-colors/{color_id}
PUT /stone-colors/{color_id}
DELETE /stone-colors/{color_id}
```

### Stone Thickness

**Base Path:** `/stone-thickness`

```http
GET /stone-thickness
POST /stone-thickness
GET /stone-thickness/{thickness_id}
PUT /stone-thickness/{thickness_id}
DELETE /stone-thickness/{thickness_id}
```

### Edges

**Base Path:** `/edges`

```http
GET /edges
POST /edges
GET /edges/{edge_id}
PUT /edges/{edge_id}
DELETE /edges/{edge_id}
```

### Accounts

**Base Path:** `/accounts`

```http
GET /accounts
POST /accounts
GET /accounts/{account_id}
PUT /accounts/{account_id}
DELETE /accounts/{account_id}
```

### Users

```http
GET /users/sales-persons
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 10,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com"
    }
  ]
}
```

### FAB Types

```http
GET /fab-types
```

**Response:**

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "standard",
      "description": "Standard fabrication"
    },
    {
      "id": 2,
      "name": "fast_track",
      "description": "Rush/priority fabrication"
    },
    {
      "id": 3,
      "name": "redo",
      "description": "Redo fabrication"
    }
  ]
}
```

---

## Error Handling

### Standard Error Response

All errors follow this format:

```json
{
  "success": false,
  "message": "Error description",
  "detail": "Detailed error information"
}
```

### Common HTTP Status Codes

| Code | Meaning               | Example                            |
| ---- | --------------------- | ---------------------------------- |
| 200  | OK                    | Successful GET, PUT, POST          |
| 201  | Created               | Successful POST (resource created) |
| 204  | No Content            | Successful DELETE                  |
| 400  | Bad Request           | Invalid request data               |
| 401  | Unauthorized          | Missing or invalid auth token      |
| 403  | Forbidden             | User doesn't have permission       |
| 404  | Not Found             | Resource doesn't exist             |
| 422  | Unprocessable Entity  | Validation error                   |
| 500  | Internal Server Error | Server error                       |

### Example Error Responses

**400 Bad Request:**

```json
{
  "success": false,
  "message": "Validation error",
  "detail": {
    "notes": ["Field 'notes' must be an array of strings"]
  }
}
```

**401 Unauthorized:**

```json
{
  "success": false,
  "message": "Could not validate credentials",
  "detail": "Token expired or invalid"
}
```

**404 Not Found:**

```json
{
  "success": false,
  "message": "Fab not found",
  "detail": "FAB with ID 999 does not exist"
}
```

**422 Unprocessable Entity:**

```json
{
  "success": false,
  "message": "Validation error",
  "detail": [
    {
      "loc": ["body", "fab_id"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## Complete Workflow Example

Here's a complete example of a FAB progressing through the workflow:

### Step 1: Create FAB

```javascript
// POST /fabs
const fabResponse = await fetch("/api/v1/fabs", {
  method: "POST",
  headers: {
    Authorization: "Bearer " + token,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    job_id: 5,
    fab_type: "standard",
    sales_person_id: 10,
    stone_type_id: 3,
    stone_color_id: 7,
    stone_thickness_id: 2,
    edge_id: 4,
    input_area: "Kitchen countertop",
    total_sqft: 120,
    notes: ["Customer prefers dark granite"],
    template_needed: true,
    drafting_needed: true,
  }),
});

// Result: FAB ID 25 created
// current_stage: "fab_created"
// next_stage: "templating"
```

### Step 2: Schedule Templating (Coordinator)

```javascript
// POST /templating/schedule
await fetch("/api/v1/templating/schedule", {
  method: "POST",
  headers: {
    Authorization: "Bearer " + token,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    fab_id: 25,
    technician_id: 15,
    schedule_start_date: "2025-11-20T08:00:00",
    schedule_due_date: "2025-11-22T17:00:00",
    total_sqft: "120",
    notes: ["Customer available mornings only"],
  }),
});

// Result: Templating ID 42 created
// FAB current_stage: "templating"
// FAB next_stage: "pre_draft_review"
```

### Step 3: View FABs in Templating Stage (Technician Dashboard)

```javascript
// GET /fabs?current_stage=templating
const templatingFabs = await fetch("/api/v1/fabs?current_stage=templating", {
  headers: { Authorization: "Bearer " + token },
});

// Shows all FABs currently in templating with:
// - templating_schedule_start_date
// - templating_schedule_due_date
// - templating_notes
// - technician_name
```

### Step 4: Complete Templating (Technician)

```javascript
// POST /templating/42/complete
await fetch("/api/v1/templating/42/complete", {
  method: "POST",
  headers: {
    Authorization: "Bearer " + token,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    actual_sqft: "125.5",
    notes: ["Template completed", "Customer changed island size"],
  }),
});

// Result:
// - total_sqft updated to 125.5
// - Notes appended: ["Customer available mornings only", "Template completed", "Customer changed island size"]
// - status_id: 2 (Completed)
// - status_name: "Completed"
```

### Step 5: Check Completed Templating (Coordinator)

```javascript
// GET /fabs?current_stage=templating
// Filter in frontend by status_name === "Completed"
const completedTemplating = fabs.filter((f) => f.status_name === "Completed");

// Coordinator sees which FABs are ready for review
```

### Step 6: Mark as Received & Move to Pre-Draft Review

```javascript
// POST /templating/42/mark-received
await fetch("/api/v1/templating/42/mark-received", {
  method: "POST",
  headers: { Authorization: "Bearer " + token },
});

// Result:
// FAB current_stage: "pre_draft_review"
// FAB next_stage: "drafting"
```

### Step 7: Get FABs in Pre-Draft Review

```javascript
// GET /fabs?current_stage=pre_draft_review
const reviewFabs = await fetch("/api/v1/fabs?current_stage=pre_draft_review", {
  headers: { Authorization: "Bearer " + token },
});
```

### Step 8: Assign to Drafter

```javascript
// POST /drafting
await fetch("/api/v1/drafting", {
  method: "POST",
  headers: {
    Authorization: "Bearer " + token,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    fab_id: 25,
    drafter_id: 12,
  }),
});

// Result:
// FAB current_stage: "drafting"
// FAB next_stage: "sales_check"
```

### Step 9: Submit Draft for Sales Check

```javascript
// POST /drafting/55/submit
await fetch("/api/v1/drafting/55/submit", {
  method: "POST",
  headers: { Authorization: "Bearer " + token },
});

// Result:
// FAB current_stage: "sales_check"
// FAB next_stage: "cut_list" (or "revision" if changes needed)
```

### Step 10: Sales Approval or Revision

**If Approved:**

```javascript
// PUT /sales-ct/60/review-no
await fetch("/api/v1/sales-ct/60/review-no", {
  method: "PUT",
  headers: { Authorization: "Bearer " + token },
});

// Result:
// FAB current_stage: "cut_list"
// FAB next_stage: "final_programming"
```

**If Revisions Needed:**

```javascript
// PUT /sales-ct/60/review-yes
await fetch("/api/v1/sales-ct/60/review-yes", {
  method: "PUT",
  headers: {
    Authorization: "Bearer " + token,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    reason: "Change edge to ogee",
  }),
});

// Result:
// FAB current_stage: "revision"
// FAB next_stage: "sales_check"
// (Loops back to drafter → sales check again)
```

---

## Frontend Implementation Tips

### 1. Dashboard Views by Stage

Create separate views/tabs for each stage:

```javascript
// Example: Templating Dashboard
const TemplatingDashboard = () => {
  const [templatingFabs, setTemplatingFabs] = useState([]);

  useEffect(() => {
    fetch("/api/v1/fabs?current_stage=templating")
      .then((res) => res.json())
      .then((data) => setTemplatingFabs(data.data));
  }, []);

  // Display cards showing:
  // - FAB details
  // - Technician name
  // - Schedule dates
  // - Status (Active/Completed)
  // - Notes history
  // - Action button: "Complete" (if technician is current user)
};
```

### 2. Notes Display

```javascript
// Display notes as list
const NotesDisplay = ({ notes }) => {
  if (!notes || notes.length === 0) return <p>No notes</p>;

  return (
    <ul>
      {notes.map((note, index) => (
        <li key={index}>{note}</li>
      ))}
    </ul>
  );
};
```

### 3. Adding Notes

```javascript
// Always send as array
const addNote = (newNote) => {
  const payload = {
    notes: [newNote], // Single note wrapped in array
  };

  // Or append to existing notes
  const payload = {
    notes: [...existingNotes, newNote],
  };
};
```

### 4. Status Indicators

```javascript
const StatusBadge = ({ statusName }) => {
  const colors = {
    Active: "blue",
    Completed: "green",
    Pending: "yellow",
    "In Progress": "orange",
  };

  return <span className={`badge-${colors[statusName]}`}>{statusName}</span>;
};
```

### 5. Stage Filters

```javascript
// Navigation showing FAB counts per stage
const StageNavigation = () => {
  const stages = [
    { key: "templating", label: "Templating" },
    { key: "pre_draft_review", label: "Pre-Draft Review" },
    { key: "drafting", label: "Drafting" },
    { key: "sales_check", label: "Sales Check" },
    { key: "revision", label: "Revisions" },
    { key: "cut_list", label: "Cut List" },
    { key: "final_programming", label: "Final Programming" },
    { key: "shop_planning", label: "Shop Planning" },
  ];

  return (
    <nav>
      {stages.map((stage) => (
        <Link to={`/fabs?stage=${stage.key}`} key={stage.key}>
          {stage.label}
          <span className="count">{getCountForStage(stage.key)}</span>
        </Link>
      ))}
    </nav>
  );
};
```

### 6. Error Handling

```javascript
const handleApiCall = async (url, options) => {
  try {
    const response = await fetch(url, options);
    const data = await response.json();

    if (!response.ok) {
      // Show user-friendly error
      showNotification("error", data.message || "An error occurred");
      return null;
    }

    return data;
  } catch (error) {
    showNotification("error", "Network error - please try again");
    return null;
  }
};
```

---

## Common Integration Patterns

### Pattern 1: List-Detail View

```javascript
// List View: Show all FABs at a stage
GET /fabs?current_stage=templating

// Detail View: Show single FAB with full info
GET /fabs/{fab_id}
```

### Pattern 2: Workflow Actions

```javascript
// User clicks "Schedule Templating" button
POST / templating / schedule;

// User clicks "Complete" button (technician)
POST / templating / { id } / complete;

// User clicks "Mark Received" button (coordinator)
POST / templating / { id } / mark - received;
```

### Pattern 3: Real-time Updates

```javascript
// Poll for updates (simple approach)
setInterval(() => {
  fetch("/api/v1/fabs?current_stage=" + currentStage)
    .then((res) => res.json())
    .then((data) => updateFabList(data.data));
}, 30000); // Every 30 seconds

// Better: Use WebSockets (if implemented)
// or Server-Sent Events for real-time updates
```

### Pattern 4: Form Validation

```javascript
// Before submitting, validate notes format
const validateForm = (formData) => {
  if (formData.notes && typeof formData.notes === "string") {
    // Convert string to array
    formData.notes = [formData.notes];
  }

  if (formData.notes && !Array.isArray(formData.notes)) {
    throw new Error("Notes must be an array");
  }

  return formData;
};
```

---

## Quick Reference Card

### Critical Endpoints for Each Role

**Coordinator:**

- `GET /fabs?current_stage={stage}` - View FABs at any stage
- `POST /templating/schedule` - Schedule templating
- `POST /templating/{id}/mark-received` - Move to pre-draft review
- `POST /drafting` - Assign drafter

**Technician:**

- `GET /fabs?current_stage=templating` - See assigned templating jobs
- `POST /templating/{id}/complete` - Mark templating complete

**Drafter:**

- `GET /fabs?current_stage=drafting` - See assigned drafts
- `POST /drafting/{id}/submit` - Submit draft for review

**Salesperson:**

- `GET /fabs?current_stage=sales_check` - See drafts to review
- `PUT /sales-ct/{id}/review-no` - Approve draft
- `PUT /sales-ct/{id}/review-yes` - Request revisions

### Must-Know Fields

| Field              | Type             | Description                             |
| ------------------ | ---------------- | --------------------------------------- |
| `current_stage`    | string           | Where FAB is now                        |
| `next_stage`       | string           | Where FAB goes next                     |
| `notes`            | array of strings | **MUST be array!**                      |
| `status_id`        | integer          | Status ID (1=Active, 2=Completed, etc.) |
| `status_name`      | string           | Human-readable status                   |
| `technician_name`  | string           | Full name of technician                 |
| `templating_notes` | array of strings | Notes from templating stage             |

---

## Support & Questions

### Getting Help

1. **API Errors**: Check error response `message` and `detail` fields
2. **Validation Issues**: Most common - sending notes as string instead of array
3. **Stage Transitions**: Verify FAB is in correct `current_stage` before actions
4. **Permissions**: Ensure JWT token is valid and user has required role

### Testing

Use tools like:

- **Postman** - Import API collection
- **Swagger UI** - Available at `/docs` endpoint
- **cURL** - Command-line testing
- **Python Test Script** - `scripts/test_all_endpoints.py`

### Change Log

| Date       | Version | Changes                              |
| ---------- | ------- | ------------------------------------ |
| 2025-11-18 | 1.0     | Initial documentation                |
| 2025-11-18 | 1.0     | Added templating completion endpoint |
| 2025-11-18 | 1.0     | Changed notes from string to array   |

---

**Last Updated**: November 18, 2025  
**Backend Version**: 1.0  
**Contact**: Backend Development Team
