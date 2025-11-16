# Alpha Granit Backend API Documentation

This document provides a comprehensive overview of all API endpoints in the Alpha Granit Backend system. The API follows RESTful principles and uses JSON for request/response bodies.

## Table of Contents
- [Job Management](#job-management)
- [Job Applications](#job-applications)
- [Job Extras](#job-extras)
  - [Templating](#templating)
  - [Technician Workflow](#technician-workflow)
  - [Final Programming](#final-programming)
  - [Sales CT](#sales-ct)
  - [SlabSmith](#slabsmith)
  - [Drafting](#drafting)
  - [Planning Section](#planning-section)

## Job Management

### List Jobs
- **URL**: `GET /api/v1/jobs/`
- **Description**: Get a list of published jobs with filtering options
- **Query Parameters**:
  - `status` (optional): Filter by job status (draft/published/closed/archived)
  - `job_type` (optional): Filter by job type (full_time/part_time/contract/internship/temporary)
  - `experience_level` (optional): Filter by experience level (entry/mid/senior/executive)
  - `is_remote` (optional): Filter by remote jobs (true/false)
  - `search` (optional): Search term to filter jobs
  - `skip` (optional): Number of records to skip (default: 0)
  - `limit` (optional): Maximum number of records to return (default: 10)
- **Response**: List of job objects with pagination metadata

### Get Job Details
- **URL**: `GET /api/v1/jobs/{job_id}`
- **Description**: Get details of a specific job
- **Path Parameters**:
  - `job_id`: ID of the job to retrieve
- **Response**: Job details object

### Create Job
- **URL**: `POST /api/v1/jobs/`
- **Description**: Create a new job posting
- **Request Body**:
  ```json
  {
    "title": "string",
    "description": "string",
    "requirements": "string",
    "responsibilities": "string",
    "location": "string",
    "job_type": "full_time|part_time|contract|internship|temporary",
    "experience_level": "entry|mid|senior|executive",
    "salary_min": 0.0,
    "salary_max": 0.0,
    "salary_currency": "string (default: USD)",
    "is_remote": false,
    "status": "draft|published|closed|archived (default: draft)",
    "application_deadline": "datetime (optional)",
    "skills_required": ["string"]
  }
  ```
- **Response**: Created job object

### Update Job
- **URL**: `PUT /api/v1/jobs/{job_id}`
- **Description**: Update an existing job posting
- **Path Parameters**:
  - `job_id`: ID of the job to update
- **Request Body**: Same as Create Job
- **Response**: Updated job object

### Delete Job
- **URL**: `DELETE /api/v1/jobs/{job_id}`
- **Description**: Delete a job posting
- **Path Parameters**:
  - `job_id`: ID of the job to delete
- **Response**: Success/error message

## Job Applications

### Apply for a Job
- **URL**: `POST /api/v1/jobs/{job_id}/apply`
- **Description**: Submit an application for a job
- **Path Parameters**:
  - `job_id`: ID of the job to apply for
- **Request Body**:
  ```json
  {
    "cover_letter": "string",
    "resume_url": "string",
    "status": "string (default: applied)"
  }
  ```
- **Response**: Created application object

### Get Job Applications
- **URL**: `GET /api/v1/jobs/{job_id}/applications`
- **Description**: Get applications for a specific job (for job poster/recruiter)
- **Path Parameters**:
  - `job_id`: ID of the job
- **Query Parameters**:
  - `status` (optional): Filter applications by status
  - `skip` (optional): Number of records to skip (default: 0)
  - `limit` (optional): Maximum number of records to return (default: 20)
- **Response**: List of application objects with pagination metadata

### Update Application Status
- **URL**: `PUT /api/v1/applications/{application_id}/status`
- **Description**: Update the status of a job application
- **Path Parameters**:
  - `application_id`: ID of the application to update
- **Query Parameters**:
  - `status`: New status for the application
  - `notes` (optional): Additional notes about the status change
- **Response**: Updated application object

## Job Extras

### Templating

#### Schedule Templating
- **URL**: `POST /api/v1/job-extras/templating/schedule`
- **Description**: Schedule a templating job
- **Form Data**:
  - `fab_id`: ID of the FAB (Fabrication)
  - `technician_id`: ID of the technician
  - `schedule_start_date`: Scheduled start date
  - `schedule_due_date`: Scheduled due date
  - `total_sqft`: Total square footage
  - `notes` (optional): Additional notes
- **Response**: Scheduling result

#### Mark Template as Received
- **URL**: `POST /api/v1/job-extras/templating/{fab_id}/received`
- **Description**: Mark a template as received
- **Path Parameters**:
  - `fab_id`: ID of the FAB
- **Response**: Success/error message

### Technician Workflow

#### Save Technician Clock
- **URL**: `POST /api/v1/job-extras/technician/clock`
- **Description**: Save technician work clock entry
- **Form Data**:
  - `fab_id`: ID of the FAB
  - `technician_id`: ID of the technician
  - `table_name`: Name of the work table
  - `started_at`: Start time
  - `completed_at`: Completion time
  - `total_sqft_done`: Square footage completed
  - `notes` (optional): Additional notes
  - `pause_reason` (optional): Reason for work pause
  - `table_id` (optional): ID of the work table
- **Response**: Created clock entry

#### Update Technician Clock
- **URL**: `PUT /api/v1/job-extras/technician/clock/{workflow_id}`
- **Description**: Update an existing technician clock entry
- **Path Parameters**:
  - `workflow_id`: ID of the workflow to update
- **Form Data**:
  - `started_at` (optional): Updated start time
  - `completed_at` (optional): Updated completion time
  - `total_sqft_done` (optional): Updated square footage
  - `notes` (optional): Updated notes
  - `pause_reason` (optional): Updated pause reason
- **Response**: Updated clock entry

### Final Programming

#### Add Files to Final Programming
- **URL**: `POST /api/v1/job-extras/final-programming/{fp_id}/files`
- **Description**: Upload files for final programming
- **Path Parameters**:
  - `fp_id`: ID of the final programming entry
- **Form Data**:
  - `files`: List of files to upload
- **Response**: Success/error message with file details

#### Update Final Programming
- **URL**: `PUT /api/v1/job-extras/final-programming/{fp_id}`
- **Description**: Update final programming details
- **Path Parameters**:
  - `fp_id`: ID of the final programming entry
- **Form Data**:
  - `note` (optional): Updated notes
  - `status` (optional): Updated status
- **Response**: Updated final programming entry

### Sales CT

#### Set SCT Review (No Changes)
- **URL**: `POST /api/v1/job-extras/sct/{sct_id}/review-no`
- **Description**: Mark SCT review as complete with no changes needed
- **Path Parameters**:
  - `sct_id`: ID of the SCT entry
- **Form Data**:
  - `revenue`: Revenue amount
- **Response**: Updated SCT entry

#### Set SCT Review (With Changes)
- **URL**: `POST /api/v1/job-extras/sct/{sct_id}/review-yes`
- **Description**: Mark SCT review as complete with changes needed
- **Path Parameters**:
  - `sct_id`: ID of the SCT entry
- **Form Data**:
  - `revision_reason`: Reason for revision
  - `files` (optional): List of files related to the revision
- **Response**: Updated SCT entry

### SlabSmith

#### Mark SlabSmith as Completed
- **URL**: `POST /api/v1/job-extras/slabsmith/{slabsmith_id}/complete`
- **Description**: Mark a SlabSmith job as completed
- **Path Parameters**:
  - `slabsmith_id`: ID of the SlabSmith entry
- **Response**: Success/error message

#### Add Files to SlabSmith
- **URL**: `POST /api/v1/job-extras/slabsmith/{slabsmith_id}/files`
- **Description**: Upload files for a SlabSmith job
- **Path Parameters**:
  - `slabsmith_id`: ID of the SlabSmith entry
- **Form Data**:
  - `files`: List of files to upload
- **Response**: Success/error message with file details

### Drafting

#### Submit Draft for Review
- **URL**: `POST /api/v1/job-extras/drafting/{drafting_id}/submit`
- **Description**: Submit a draft for review
- **Path Parameters**:
  - `drafting_id`: ID of the drafting entry
- **Form Data**:
  - `file_ids`: Comma-separated list of file IDs
  - `no_of_piece_drafted`: Number of pieces drafted
  - `total_sqft_drafted`: Total square footage drafted
  - `draft_note`: Notes about the draft
  - `mentions`: User mentions in the notes
  - `is_completed`: Whether the draft is complete
- **Response**: Updated drafting entry

### Planning Section

#### Create Workstation
- **URL**: `POST /api/v1/job-extras/planning/workstation`
- **Description**: Create a new workstation in the planning section
- **Form Data**:
  - `planning_section_id`: ID of the planning section
  - `workstation_name`: Name of the workstation
  - `status`: Current status
  - `assigned_operatives`: JSON string of assigned operatives
  - `machines`: JSON string of machines
  - `machine_statuses`: JSON string of machine statuses
- **Response**: Created workstation entry
