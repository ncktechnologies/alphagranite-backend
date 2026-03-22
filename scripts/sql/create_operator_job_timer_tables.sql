CREATE TABLE IF NOT EXISTS operator_job_timer_sessions (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES business_jobs(id) ON DELETE CASCADE,
    operator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workstation_id INTEGER NULL REFERENCES work_stations(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL,
    session_start_at TIMESTAMP NOT NULL,
    current_run_start_at TIMESTAMP NULL,
    current_pause_start_at TIMESTAMP NULL,
    stopped_at TIMESTAMP NULL,
    total_work_seconds INTEGER NOT NULL DEFAULT 0,
    total_pause_seconds INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_by INTEGER NOT NULL REFERENCES users(id),
    updated_at TIMESTAMP NULL,
    updated_by INTEGER NULL REFERENCES users(id),
    CONSTRAINT chk_operator_job_timer_sessions_status
        CHECK (status IN ('running', 'paused', 'stopped'))
);

CREATE INDEX IF NOT EXISTS ix_operator_job_timer_sessions_job_id
    ON operator_job_timer_sessions (job_id);

CREATE INDEX IF NOT EXISTS ix_operator_job_timer_sessions_operator_id
    ON operator_job_timer_sessions (operator_id);

CREATE INDEX IF NOT EXISTS ix_operator_job_timer_sessions_workstation_id
    ON operator_job_timer_sessions (workstation_id);

CREATE INDEX IF NOT EXISTS ix_operator_job_timer_sessions_operator_job_status
    ON operator_job_timer_sessions (operator_id, job_id, status);


CREATE TABLE IF NOT EXISTS operator_job_timer_events (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES operator_job_timer_sessions(id) ON DELETE CASCADE,
    job_id INTEGER NOT NULL REFERENCES business_jobs(id) ON DELETE CASCADE,
    operator_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    workstation_id INTEGER NULL REFERENCES work_stations(id) ON DELETE SET NULL,
    action VARCHAR(20) NOT NULL,
    event_at TIMESTAMP NOT NULL DEFAULT NOW(),
    note TEXT NULL,
    CONSTRAINT chk_operator_job_timer_events_action
        CHECK (action IN ('start', 'pause', 'resume', 'stop'))
);

CREATE INDEX IF NOT EXISTS ix_operator_job_timer_events_session_id
    ON operator_job_timer_events (session_id);

CREATE INDEX IF NOT EXISTS ix_operator_job_timer_events_job_id
    ON operator_job_timer_events (job_id);

CREATE INDEX IF NOT EXISTS ix_operator_job_timer_events_operator_id
    ON operator_job_timer_events (operator_id);

CREATE INDEX IF NOT EXISTS ix_operator_job_timer_events_workstation_id
    ON operator_job_timer_events (workstation_id);

CREATE INDEX IF NOT EXISTS ix_operator_job_timer_events_operator_job_event_at
    ON operator_job_timer_events (operator_id, job_id, event_at);