"""
Unit tests for job_crud service layer functions.
Tests all business logic for job CRUD operations.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.service.job_crud import (
    create_job,
    get_jobs,
    get_job_by_id,
    update_job,
    delete_job,
    get_job_count,
    get_jobs_by_account,
    check_job_number_exists
)
from src.app.database.business_job import BusinessJob
from src.app.database.account import Account
from src.app.interface.business_schemas import JobCreate, JobUpdate


# Fixtures
@pytest.fixture
def mock_db():
    """Create a mock database session"""
    db = AsyncMock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def sample_job():
    """Create a sample job object"""
    job = BusinessJob(
        id=1,
        name="Test Job",
        job_number="JOB-2024-001",
        account_id=10,
        status_id=1,
        priority="high",
        description="Test job description",
        created_by=100,
        updated_by=100,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    return job


@pytest.fixture
def sample_account():
    """Create a sample account object"""
    account = Account(
        id=10,
        name="Test Account",
        created_at=datetime.now()
    )
    return account


# Tests for create_job
@pytest.mark.asyncio
async def test_create_job_success(mock_db, sample_account):
    """Test successful job creation"""
    # Mock account existence check
    account_result = MagicMock()
    account_result.scalar_one_or_none.return_value = sample_account
    
    # Mock job number uniqueness check
    job_number_result = MagicMock()
    job_number_result.scalar_one_or_none.return_value = None
    
    mock_db.execute.side_effect = [account_result, job_number_result]
    
    job_data = JobCreate(
        name="Test Job",
        job_number="JOB-2024-001",
        account_id=10,
        priority="high",
        description="Test job"
    )
    
    result = await create_job(mock_db, job_data, user_id=100)
    
    assert isinstance(result, BusinessJob)
    assert result.job_number == "JOB-2024-001"
    assert result.account_id == 10
    assert result.status_id == 1  # Default status
    assert result.created_by == 100
    assert mock_db.add.called
    assert mock_db.commit.called
    assert mock_db.refresh.called


@pytest.mark.asyncio
async def test_create_job_account_not_found(mock_db):
    """Test job creation fails when account doesn't exist"""
    # Mock account not found
    account_result = MagicMock()
    account_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = account_result
    
    job_data = JobCreate(
        name="Test Job",
        job_number="JOB-2024-001",
        account_id=999,
        priority="high"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await create_job(mock_db, job_data, user_id=100)
    
    assert exc_info.value.status_code == 404
    assert "Account not found" in exc_info.value.detail
    assert not mock_db.add.called


@pytest.mark.asyncio
async def test_create_job_duplicate_job_number(mock_db, sample_account, sample_job):
    """Test job creation fails with duplicate job number"""
    # Mock account exists
    account_result = MagicMock()
    account_result.scalar_one_or_none.return_value = sample_account
    
    # Mock job number already exists
    job_number_result = MagicMock()
    job_number_result.scalar_one_or_none.return_value = sample_job
    
    mock_db.execute.side_effect = [account_result, job_number_result]
    
    job_data = JobCreate(
        name="Test Job",
        job_number="JOB-2024-001",
        account_id=10,
        priority="high"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await create_job(mock_db, job_data, user_id=100)
    
    assert exc_info.value.status_code == 400
    assert "Job number already exists" in exc_info.value.detail
    assert not mock_db.add.called


# Tests for get_jobs
@pytest.mark.asyncio
async def test_get_jobs_with_filters(mock_db, sample_job):
    """Test getting jobs with filters applied"""
    # Mock query result
    result = MagicMock()
    result.scalars.return_value.all.return_value = [sample_job]
    mock_db.execute.return_value = result
    
    jobs = await get_jobs(
        mock_db,
        skip=0,
        limit=10,
        account_id=10,
        status_id=1,
        priority="high"
    )
    
    assert len(jobs) == 1
    assert jobs[0].id == sample_job.id
    assert jobs[0].account_id == 10
    assert mock_db.execute.called


@pytest.mark.asyncio
async def test_get_jobs_no_filters(mock_db, sample_job):
    """Test getting all jobs without filters"""
    result = MagicMock()
    result.scalars.return_value.all.return_value = [sample_job]
    mock_db.execute.return_value = result
    
    jobs = await get_jobs(mock_db, skip=0, limit=10)
    
    assert len(jobs) == 1
    assert mock_db.execute.called


@pytest.mark.asyncio
async def test_get_jobs_with_pagination(mock_db):
    """Test getting jobs with pagination"""
    jobs_list = [
        BusinessJob(id=i, job_number=f"JOB-{i}", account_id=10, status_id=1)
        for i in range(1, 6)
    ]
    
    result = MagicMock()
    result.scalars.return_value.all.return_value = jobs_list[2:4]  # Skip 2, limit 2
    mock_db.execute.return_value = result
    
    jobs = await get_jobs(mock_db, skip=2, limit=2)
    
    assert len(jobs) == 2
    assert mock_db.execute.called


# Tests for get_job_by_id
@pytest.mark.asyncio
async def test_get_job_by_id_success(mock_db, sample_job):
    """Test successfully retrieving a job by ID"""
    result = MagicMock()
    result.scalar_one_or_none.return_value = sample_job
    mock_db.execute.return_value = result
    
    job = await get_job_by_id(mock_db, job_id=1)
    
    assert job.id == sample_job.id
    assert job.job_number == sample_job.job_number
    assert mock_db.execute.called


@pytest.mark.asyncio
async def test_get_job_by_id_not_found(mock_db):
    """Test job not found returns 404"""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = result
    
    with pytest.raises(HTTPException) as exc_info:
        await get_job_by_id(mock_db, job_id=999)
    
    assert exc_info.value.status_code == 404
    assert "Job not found" in exc_info.value.detail


# Tests for update_job
@pytest.mark.asyncio
async def test_update_job_success(mock_db, sample_job, sample_account):
    """Test successful job update"""
    # Mock job retrieval
    job_result = MagicMock()
    job_result.scalar_one_or_none.return_value = sample_job
    
    # Mock job number check (no account check since account_id not being updated)
    job_number_result = MagicMock()
    job_number_result.scalar_one_or_none.return_value = None
    
    mock_db.execute.side_effect = [job_result, job_number_result]
    
    job_data = JobUpdate(
        job_number="JOB-2024-002",
        priority="medium",
        description="Updated description"
    )
    
    updated_job = await update_job(mock_db, job_id=1, job_data=job_data, user_id=100)
    
    assert updated_job.job_number == "JOB-2024-002"
    assert updated_job.priority == "medium"
    assert updated_job.description == "Updated description"
    assert updated_job.updated_by == 100
    assert mock_db.commit.called
    assert mock_db.refresh.called


@pytest.mark.asyncio
async def test_update_job_not_found(mock_db):
    """Test updating non-existent job returns 404"""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = result
    
    job_data = JobUpdate(priority="high")
    
    with pytest.raises(HTTPException) as exc_info:
        await update_job(mock_db, job_id=999, job_data=job_data, user_id=100)
    
    assert exc_info.value.status_code == 404
    assert "Job not found" in exc_info.value.detail
    assert not mock_db.commit.called


@pytest.mark.asyncio
async def test_update_job_account_not_found(mock_db, sample_job):
    """Test updating job with invalid account fails"""
    # Mock job exists
    job_result = MagicMock()
    job_result.scalar_one_or_none.return_value = sample_job
    
    # Mock account doesn't exist
    account_result = MagicMock()
    account_result.scalar_one_or_none.return_value = None
    
    mock_db.execute.side_effect = [job_result, account_result]
    
    job_data = JobUpdate(account_id=999)
    
    with pytest.raises(HTTPException) as exc_info:
        await update_job(mock_db, job_id=1, job_data=job_data, user_id=100)
    
    assert exc_info.value.status_code == 404
    assert "Account not found" in exc_info.value.detail
    assert not mock_db.commit.called


@pytest.mark.asyncio
async def test_update_job_duplicate_job_number(mock_db, sample_job, sample_account):
    """Test updating to duplicate job number fails"""
    # Mock job exists
    job_result = MagicMock()
    job_result.scalar_one_or_none.return_value = sample_job
    
    # Mock account exists
    account_result = MagicMock()
    account_result.scalar_one_or_none.return_value = sample_account
    
    # Mock job number already exists
    existing_job = BusinessJob(id=2, job_number="JOB-2024-002", account_id=10, status_id=1)
    job_number_result = MagicMock()
    job_number_result.scalar_one_or_none.return_value = existing_job
    
    mock_db.execute.side_effect = [job_result, account_result, job_number_result]
    
    job_data = JobUpdate(job_number="JOB-2024-002")
    
    with pytest.raises(HTTPException) as exc_info:
        await update_job(mock_db, job_id=1, job_data=job_data, user_id=100)
    
    assert exc_info.value.status_code == 400
    assert "Job number already exists" in exc_info.value.detail
    assert not mock_db.commit.called


# Tests for delete_job
@pytest.mark.asyncio
async def test_delete_job_success(mock_db, sample_job):
    """Test successful job deletion (soft delete)"""
    result = MagicMock()
    result.scalar_one_or_none.return_value = sample_job
    mock_db.execute.return_value = result
    
    await delete_job(mock_db, job_id=1, user_id=100)
    
    assert sample_job.status_id == 3  # Deleted status
    assert sample_job.updated_by == 100
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_delete_job_not_found(mock_db):
    """Test deleting non-existent job returns 404"""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = result
    
    with pytest.raises(HTTPException) as exc_info:
        await delete_job(mock_db, job_id=999, user_id=100)
    
    assert exc_info.value.status_code == 404
    assert "Job not found" in exc_info.value.detail
    assert not mock_db.commit.called


# Tests for get_job_count
@pytest.mark.asyncio
async def test_get_job_count_no_filters(mock_db):
    """Test getting total job count without filters"""
    result = MagicMock()
    result.scalar.return_value = 42
    mock_db.execute.return_value = result
    
    count = await get_job_count(mock_db)
    
    assert count == 42
    assert mock_db.execute.called


@pytest.mark.asyncio
async def test_get_job_count_with_filters(mock_db):
    """Test getting job count with filters"""
    result = MagicMock()
    result.scalar.return_value = 15
    mock_db.execute.return_value = result
    
    count = await get_job_count(mock_db, account_id=10, status_id=1)
    
    assert count == 15
    assert mock_db.execute.called


# Tests for get_jobs_by_account
@pytest.mark.asyncio
async def test_get_jobs_by_account_success(mock_db, sample_job):
    """Test getting jobs filtered by account"""
    jobs_list = [sample_job]
    result = MagicMock()
    result.scalars.return_value.all.return_value = jobs_list
    mock_db.execute.return_value = result
    
    jobs = await get_jobs_by_account(mock_db, account_id=10, skip=0, limit=10)
    
    assert len(jobs) == 1
    assert jobs[0].account_id == 10
    assert mock_db.execute.called


@pytest.mark.asyncio
async def test_get_jobs_by_account_pagination(mock_db):
    """Test getting account jobs with pagination"""
    jobs_list = [
        BusinessJob(id=i, job_number=f"JOB-{i}", account_id=10, status_id=1)
        for i in range(1, 4)
    ]
    
    result = MagicMock()
    result.scalars.return_value.all.return_value = jobs_list[1:3]
    mock_db.execute.return_value = result
    
    jobs = await get_jobs_by_account(mock_db, account_id=10, skip=1, limit=2)
    
    assert len(jobs) == 2
    assert mock_db.execute.called


# Tests for check_job_number_exists
@pytest.mark.asyncio
async def test_check_job_number_exists_true(mock_db, sample_job):
    """Test job number exists returns True"""
    result = MagicMock()
    result.scalar_one_or_none.return_value = sample_job
    mock_db.execute.return_value = result
    
    exists = await check_job_number_exists(mock_db, job_number="JOB-2024-001")
    
    assert exists is True
    assert mock_db.execute.called


@pytest.mark.asyncio
async def test_check_job_number_exists_false(mock_db):
    """Test job number doesn't exist returns False"""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = result
    
    exists = await check_job_number_exists(mock_db, job_number="JOB-9999-999")
    
    assert exists is False
    assert mock_db.execute.called


@pytest.mark.asyncio
async def test_check_job_number_exists_exclude_id(mock_db, sample_job):
    """Test job number check excludes specific job ID"""
    result = MagicMock()
    result.scalar_one_or_none.return_value = None  # No other job with this number
    mock_db.execute.return_value = result
    
    exists = await check_job_number_exists(
        mock_db, 
        job_number="JOB-2024-001", 
        exclude_job_id=1
    )
    
    assert exists is False
    assert mock_db.execute.called
