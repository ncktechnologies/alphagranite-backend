-- -------------------------------------------------------------
-- TablePlus 26.10.23(803)
--
-- https://tableplus.com/
--
-- Database: alpha_granite_staging
-- Generation Time: 2026-09-20 6:01:59.0870 PM
-- -------------------------------------------------------------


-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS pre_draft_reviews_id_seq;

-- Table Definition
CREATE TABLE "public"."pre_draft_reviews" (
    "id" int4 NOT NULL DEFAULT nextval('pre_draft_reviews_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "draft_notes" varchar NOT NULL,
    "is_redrafting_needed" int4 NOT NULL,
    "is_completed" bool NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_by" int4 NOT NULL,
    "updated_at" timestamp NOT NULL,
    "status_id" int4,
    PRIMARY KEY ("id")
);

-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS resurface_schedulings_id_seq;

-- Table Definition
CREATE TABLE "public"."resurface_schedulings" (
    "id" int4 NOT NULL DEFAULT nextval('resurface_schedulings_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "technician_id" int4,
    "scheduled_start_date" timestamp,
    "scheduled_end_date" timestamp,
    "actual_start_date" timestamp,
    "actual_end_date" timestamp,
    "total_sqft" varchar,
    "completed_sqft" varchar,
    "is_completed" bool NOT NULL,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "notes" jsonb,
    PRIMARY KEY ("id")
);

-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS shop_planning_id_seq;

-- Table Definition
CREATE TABLE "public"."shop_planning" (
    "id" int4 NOT NULL DEFAULT nextval('shop_planning_id_seq'::regclass),
    "name" varchar NOT NULL,
    "description" varchar,
    "status_id" int4 NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_by" int4,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    PRIMARY KEY ("id")
);

-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS shop_planning_sections_id_seq;

-- Table Definition
CREATE TABLE "public"."shop_planning_sections" (
    "id" int4 NOT NULL DEFAULT nextval('shop_planning_sections_id_seq'::regclass),
    "work_station_id" int4 NOT NULL,
    "operator_ids" varchar,
    "machine" varchar,
    "scheduled_sqft" varchar,
    "completed_sqft" varchar,
    "start_date" timestamp,
    "end_date" timestamp,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);

-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS slab_smiths_id_seq;

-- Table Definition
CREATE TABLE "public"."slab_smiths" (
    "id" int4 NOT NULL DEFAULT nextval('slab_smiths_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "slab_smith_type" varchar NOT NULL,
    "drafter_id" int4 NOT NULL,
    "status_id" int4 NOT NULL,
    "start_date" timestamp NOT NULL,
    "end_date" timestamp,
    "total_sqft_completed" varchar,
    "is_completed" bool NOT NULL,
    "slabsmith_completed_date" timestamp,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "file_ids" varchar,
    PRIMARY KEY ("id")
);

-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS templatings_id_seq;

-- Table Definition
CREATE TABLE "public"."templatings" (
    "id" int4 NOT NULL DEFAULT nextval('templatings_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "technician_id" int4,
    "schedule_start_date" timestamp,
    "schedule_due_date" timestamp,
    "total_sqft" varchar,
    "actual_start_date" timestamp,
    "actual_end_date" timestamp,
    "duration" int4,
    "notes" jsonb,
    "review_checklist" jsonb,
    "is_templating_schedule" bool NOT NULL,
    "rescheduled" bool NOT NULL,
    "is_completed" bool,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);

-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS wj_programmings_id_seq;

-- Table Definition
CREATE TABLE "public"."wj_programmings" (
    "id" int4 NOT NULL DEFAULT nextval('wj_programmings_id_seq'::regclass),
    "drafter_id" int4 NOT NULL,
    "fab_id" int4 NOT NULL,
    "scheduled_start_date" timestamp NOT NULL,
    "scheduled_end_date" timestamp NOT NULL,
    "drafter_start_date" timestamp,
    "drafter_end_date" timestamp,
    "is_completed" bool NOT NULL,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "file_ids" varchar,
    "no_of_pieces" varchar,
    "total_ln_ft" varchar,
    "notes" jsonb,
    PRIMARY KEY ("id")
);

-- Table Definition
CREATE TABLE "public"."alembic_version" (
    "version_num" varchar(32) NOT NULL,
    PRIMARY KEY ("version_num")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS wj_schedulings_id_seq;

-- Table Definition
CREATE TABLE "public"."wj_schedulings" (
    "id" int4 NOT NULL DEFAULT nextval('wj_schedulings_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "technician_id" int4,
    "scheduled_start_date" timestamp,
    "scheduled_end_date" timestamp,
    "actual_start_date" timestamp,
    "actual_end_date" timestamp,
    "total_ln_ft" varchar,
    "completed_ln_ft" varchar,
    "is_completed" bool NOT NULL,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "notes" jsonb,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS cnc_drafting_session_notes_id_seq;

-- Table Definition
CREATE TABLE "public"."cnc_drafting_session_notes" (
    "id" int4 NOT NULL DEFAULT nextval('cnc_drafting_session_notes_id_seq'::regclass),
    "session_id" int4 NOT NULL,
    "fab_id" int4 NOT NULL,
    "action" varchar NOT NULL,
    "timestamp" timestamp NOT NULL,
    "note" varchar,
    "sqft_drafted" varchar,
    "work_percentage_done" int4,
    "created_at" timestamp NOT NULL,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS cnc_drafting_sessions_id_seq;

-- Table Definition
CREATE TABLE "public"."cnc_drafting_sessions" (
    "id" int4 NOT NULL DEFAULT nextval('cnc_drafting_sessions_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "drafter_id" int4 NOT NULL,
    "status" varchar NOT NULL,
    "session_start_time" timestamp NOT NULL,
    "session_end_time" timestamp,
    "current_pause_start_time" timestamp,
    "total_pause_duration" int4 NOT NULL,
    "total_time_spent" int4 NOT NULL,
    "cumulative_sqft_drafted" varchar,
    "work_percentage_done" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS cut_list_id_seq;

-- Table Definition
CREATE TABLE "public"."cut_list" (
    "id" int4 NOT NULL DEFAULT nextval('cut_list_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "is_final_progreamming_completed" bool NOT NULL,
    "is_completed" bool NOT NULL,
    "shop_schedule_date" timestamp,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "no_of_piece" varchar,
    "total_sqft" varchar,
    "installation_date" timestamp,
    "Ln_ft_map" varchar,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS drafting_session_notes_id_seq;

-- Table Definition
CREATE TABLE "public"."drafting_session_notes" (
    "id" int4 NOT NULL DEFAULT nextval('drafting_session_notes_id_seq'::regclass),
    "session_id" int4 NOT NULL,
    "fab_id" int4 NOT NULL,
    "action" varchar NOT NULL,
    "timestamp" timestamp NOT NULL,
    "note" varchar,
    "sqft_drafted" varchar,
    "work_percentage_done" int4,
    "created_at" timestamp NOT NULL,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS drafting_sessions_id_seq;

-- Table Definition
CREATE TABLE "public"."drafting_sessions" (
    "id" int4 NOT NULL DEFAULT nextval('drafting_sessions_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "drafter_id" int4 NOT NULL,
    "status" varchar NOT NULL,
    "session_start_time" timestamp NOT NULL,
    "session_end_time" timestamp,
    "current_pause_start_time" timestamp,
    "total_pause_duration" int4 NOT NULL,
    "total_time_spent" int4 NOT NULL,
    "cumulative_sqft_drafted" varchar,
    "work_percentage_done" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS fab_type_id_seq;

-- Table Definition
CREATE TABLE "public"."fab_type" (
    "name" varchar(100) NOT NULL,
    "description" varchar,
    "id" int4 NOT NULL DEFAULT nextval('fab_type_id_seq'::regclass),
    "created_at" timestamp DEFAULT now(),
    "updated_at" timestamp,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS final_programmings_id_seq;

-- Table Definition
CREATE TABLE "public"."final_programmings" (
    "id" int4 NOT NULL DEFAULT nextval('final_programmings_id_seq'::regclass),
    "drafter_id" int4 NOT NULL,
    "fab_id" int4 NOT NULL,
    "scheduled_start_date" timestamp NOT NULL,
    "scheduled_end_date" timestamp NOT NULL,
    "drafter_start_date" timestamp,
    "drafter_end_date" timestamp,
    "is_completed" bool NOT NULL,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "file_ids" varchar,
    "no_of_piece_drafted" varchar,
    "total_sqft_required_to_draft" varchar NOT NULL,
    "total_sqft_drafted" varchar,
    "notes" jsonb,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS install_schedulings_id_seq;

-- Table Definition
CREATE TABLE "public"."install_schedulings" (
    "id" int4 NOT NULL DEFAULT nextval('install_schedulings_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "installer_id" int4,
    "extra_crew_1_id" int4,
    "extra_crew_2_id" int4,
    "extra_crew_3_id" int4,
    "scheduled_install_date" timestamp,
    "scheduled_end_date" timestamp,
    "actual_install_date" timestamp,
    "total_sqft" varchar,
    "is_completed" bool NOT NULL,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "notes" jsonb,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS job_technician_workflows_id_seq;

-- Table Definition
CREATE TABLE "public"."job_technician_workflows" (
    "id" int4 NOT NULL DEFAULT nextval('job_technician_workflows_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "technician_id" int4 NOT NULL,
    "table_name" varchar NOT NULL,
    "notes" jsonb,
    "pause_reason" varchar,
    "total_sqft_done" varchar NOT NULL,
    "started_at" timestamp NOT NULL,
    "completed_at" timestamp NOT NULL,
    "table_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS operation_workflow_id_seq;

-- Table Definition
CREATE TABLE "public"."operation_workflow" (
    "id" int4 NOT NULL DEFAULT nextval('operation_workflow_id_seq'::regclass),
    "shop_planning_sections" int4 NOT NULL,
    "started_at" timestamp NOT NULL,
    "finished_at" timestamp NOT NULL,
    "total_sqft_done" varchar NOT NULL,
    "reason_for_pause" varchar NOT NULL,
    "notes" jsonb,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS users_id_seq;

-- Table Definition
CREATE TABLE "public"."users" (
    "id" int4 NOT NULL DEFAULT nextval('users_id_seq'::regclass),
    "username" varchar NOT NULL,
    "employee_id" uuid NOT NULL,
    "phone" varchar(255),
    "email" varchar(255) NOT NULL,
    "home_address" varchar(255),
    "gender" varchar(255),
    "profile_image_id" int4,
    "first_name" varchar(255) NOT NULL,
    "last_name" varchar(255) NOT NULL,
    "department" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp NOT NULL,
    "status" int4 NOT NULL,
    "is_super_admin" bool NOT NULL,
    "password" varchar(255) NOT NULL,
    "failed_login_attempts" int4 NOT NULL,
    "is_locked" bool NOT NULL,
    "locked_at" timestamp,
    "is_first_login" bool NOT NULL,
    "role_id" int4,
    "email_notifications_enabled" bool NOT NULL,
    "hcp_employee_id" varchar(255),
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS status_id_seq;

-- Table Definition
CREATE TABLE "public"."status" (
    "id" int4 NOT NULL DEFAULT nextval('status_id_seq'::regclass),
    "name" varchar(255) NOT NULL,
    "slug" varchar(255) NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp NOT NULL,
    "value_id" int4 NOT NULL,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS departments_id_seq;

-- Table Definition
CREATE TABLE "public"."departments" (
    "id" int4 NOT NULL DEFAULT nextval('departments_id_seq'::regclass),
    "name" varchar(255) NOT NULL,
    "description" varchar(255),
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp NOT NULL,
    "status" int4 NOT NULL,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS action_menus_id_seq;

-- Table Definition
CREATE TABLE "public"."action_menus" (
    "id" int4 NOT NULL DEFAULT nextval('action_menus_id_seq'::regclass),
    "name" varchar(255) NOT NULL,
    "code" varchar(255) NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp NOT NULL,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS roles_id_seq;

-- Table Definition
CREATE TABLE "public"."roles" (
    "id" int4 NOT NULL DEFAULT nextval('roles_id_seq'::regclass),
    "name" varchar(255) NOT NULL,
    "description" varchar(255),
    "status" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp NOT NULL,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS permissions_id_seq;

-- Table Definition
CREATE TABLE "public"."permissions" (
    "id" int4 NOT NULL DEFAULT nextval('permissions_id_seq'::regclass),
    "name" varchar(255) NOT NULL,
    "description" varchar(255),
    "can_create" bool NOT NULL,
    "can_update" bool NOT NULL,
    "can_delete" bool NOT NULL,
    "can_read" bool NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp NOT NULL,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS role_permissions_id_seq;

-- Table Definition
CREATE TABLE "public"."role_permissions" (
    "id" int4 NOT NULL DEFAULT nextval('role_permissions_id_seq'::regclass),
    "permission_id" int4 NOT NULL,
    "role_id" int4 NOT NULL,
    "action_menu_id" int4,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp NOT NULL,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS accounts_id_seq;

-- Table Definition
CREATE TABLE "public"."accounts" (
    "id" int4 NOT NULL DEFAULT nextval('accounts_id_seq'::regclass),
    "name" varchar(255) NOT NULL,
    "account_number" varchar(100),
    "description" varchar,
    "contact_person" varchar(255),
    "email" varchar(255),
    "phone" varchar(50),
    "address" varchar,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS edges_id_seq;

-- Table Definition
CREATE TABLE "public"."edges" (
    "id" int4 NOT NULL DEFAULT nextval('edges_id_seq'::regclass),
    "name" varchar(255) NOT NULL,
    "edge_type" varchar(100) NOT NULL,
    "description" varchar,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS password_reset_otps_id_seq;

-- Table Definition
CREATE TABLE "public"."password_reset_otps" (
    "id" int4 NOT NULL DEFAULT nextval('password_reset_otps_id_seq'::regclass),
    "user_id" int4 NOT NULL,
    "otp" varchar(6) NOT NULL,
    "expires_at" timestamp NOT NULL,
    "attempts" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS planning_sections_id_seq;

-- Table Definition
CREATE TABLE "public"."planning_sections" (
    "id" int4 NOT NULL DEFAULT nextval('planning_sections_id_seq'::regclass),
    "plan_name" varchar(255) NOT NULL,
    "plan_description" varchar,
    "is_active" bool NOT NULL,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS service_level_settings_id_seq;

-- Table Definition
CREATE TABLE "public"."service_level_settings" (
    "id" int4 NOT NULL DEFAULT nextval('service_level_settings_id_seq'::regclass),
    "fab_type" varchar(100) NOT NULL,
    "stage_name" varchar(100) NOT NULL,
    "target_days" float8 NOT NULL,
    "at_risk_days" float8 NOT NULL,
    "is_applicable" bool NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS shop_plannings_id_seq;

-- Table Definition
CREATE TABLE "public"."shop_plannings" (
    "id" int4 NOT NULL DEFAULT nextval('shop_plannings_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "start_date" timestamp NOT NULL,
    "no_of_steps_needed" int4 NOT NULL,
    "status_id" int4 NOT NULL,
    "completed_steps" int4 NOT NULL,
    "current_steps" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS stone_thickness_id_seq;

-- Table Definition
CREATE TABLE "public"."stone_thickness" (
    "id" int4 NOT NULL DEFAULT nextval('stone_thickness_id_seq'::regclass),
    "thickness" varchar(100) NOT NULL,
    "thickness_mm" float8,
    "description" varchar,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS audit_trails_id_seq;

-- Table Definition
CREATE TABLE "public"."audit_trails" (
    "id" int4 NOT NULL DEFAULT nextval('audit_trails_id_seq'::regclass),
    "activity_message" varchar NOT NULL,
    "user_id" int4 NOT NULL,
    "activity_table_name" varchar(255),
    "record_id" int4,
    "device_id" varchar(255),
    "ip_address" varchar(45),
    "browser" varchar(255),
    "created_at" timestamp NOT NULL,
    "operation" varchar(50),
    "resource_type" varchar(100),
    "changed_fields" json,
    "old_values" json,
    "new_values" json,
    "request_path" varchar(500),
    "request_method" varchar(10),
    "response_status_code" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS work_stations_id_seq;

-- Table Definition
CREATE TABLE "public"."work_stations" (
    "id" int4 NOT NULL DEFAULT nextval('work_stations_id_seq'::regclass),
    "name" varchar(255) NOT NULL,
    "is_active" bool NOT NULL,
    "status_id" int4 NOT NULL,
    "planning_section_id" int4,
    "operator_ids" jsonb,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "attendance_required" bool NOT NULL DEFAULT false,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS stone_types_id_seq;

-- Table Definition
CREATE TABLE "public"."stone_types" (
    "id" int4 NOT NULL DEFAULT nextval('stone_types_id_seq'::regclass),
    "name" varchar(255) NOT NULL,
    "description" varchar,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS user_roles_id_seq;

-- Table Definition
CREATE TABLE "public"."user_roles" (
    "id" int4 NOT NULL DEFAULT nextval('user_roles_id_seq'::regclass),
    "user_id" int4 NOT NULL,
    "role_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "update_at" timestamp NOT NULL,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS business_jobs_id_seq;

-- Table Definition
CREATE TABLE "public"."business_jobs" (
    "name" varchar(255) NOT NULL,
    "job_number" varchar(100) NOT NULL,
    "account_id" int4,
    "description" text,
    "priority" varchar(50),
    "start_date" date,
    "due_date" date,
    "project_value" numeric(15,2),
    "status_id" int4 NOT NULL,
    "created_by" int4 NOT NULL,
    "sq_ft" float8,
    "sales_person_id" int4,
    "created_at" timestamp DEFAULT now(),
    "updated_at" timestamp,
    "updated_by" int4,
    "need_to_invoice" bool NOT NULL,
    "invoice_note" varchar,
    "invoiced_at" timestamp,
    "id" int4 NOT NULL DEFAULT nextval('business_jobs_id_seq'::regclass),
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS shop_planning_planning_sections_id_seq;

-- Table Definition
CREATE TABLE "public"."shop_planning_planning_sections" (
    "id" int4 NOT NULL DEFAULT nextval('shop_planning_planning_sections_id_seq'::regclass),
    "shop_planning_id" int4 NOT NULL,
    "planning_section_id" int4 NOT NULL,
    "order" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS stone_colors_id_seq;

-- Table Definition
CREATE TABLE "public"."stone_colors" (
    "id" int4 NOT NULL DEFAULT nextval('stone_colors_id_seq'::regclass),
    "stone_type_id" int4,
    "name" varchar(255) NOT NULL,
    "color_code" varchar(50),
    "description" varchar,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS cost_of_stones_id_seq;

-- Table Definition
CREATE TABLE "public"."cost_of_stones" (
    "id" int4 NOT NULL DEFAULT nextval('cost_of_stones_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "stone_color_id" int4,
    "stone_type_id" int4,
    "total_sqft" varchar,
    "cost_per_sqft" varchar,
    "total_cost" varchar,
    "waste_percentage" varchar,
    "calculated_by" int4,
    "is_completed" bool NOT NULL,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "notes" jsonb,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS job_notes_id_seq;

-- Table Definition
CREATE TABLE "public"."job_notes" (
    "id" int4 NOT NULL DEFAULT nextval('job_notes_id_seq'::regclass),
    "job_id" int4 NOT NULL,
    "note" varchar NOT NULL,
    "created_by" int4 NOT NULL,
    "created_at" timestamp,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS fabs_id_seq;

-- Table Definition
CREATE TABLE "public"."fabs" (
    "id" int4 NOT NULL DEFAULT nextval('fabs_id_seq'::regclass),
    "job_id" int4 NOT NULL,
    "fab_type" varchar(255) NOT NULL,
    "sales_person_id" int4 NOT NULL,
    "stone_type_id" int4 NOT NULL,
    "stone_color_id" int4 NOT NULL,
    "stone_thickness_id" int4 NOT NULL,
    "edge_id" int4 NOT NULL,
    "input_area" varchar,
    "total_sqft" float8 NOT NULL,
    "notes" jsonb,
    "cost_of_stone" float8,
    "redo_total_sqft" float8,
    "redo_department" int4,
    "cost_per_sqft" float8,
    "redo_requested_by" int4,
    "template_needed" bool NOT NULL,
    "drafting_needed" bool NOT NULL,
    "slab_smith_cust_needed" bool NOT NULL,
    "slab_smith_ag_needed" bool NOT NULL,
    "sct_needed" bool NOT NULL,
    "final_programming_needed" bool NOT NULL,
    "slabsmith_time_minutes" int4,
    "drafter_id" int4,
    "drafter_assigned_by" int4,
    "drafter_assigned_at" timestamp,
    "template_received" bool NOT NULL,
    "template_review_complete" bool NOT NULL,
    "draft_completed" bool NOT NULL,
    "cad_review_complete" bool NOT NULL,
    "no_of_pieces" int4,
    "revenue" float8,
    "gp" float8,
    "sct_completed" bool NOT NULL,
    "revised" bool NOT NULL,
    "shop_date_schedule" timestamp,
    "final_programming_complete" bool NOT NULL,
    "cutlist_complete" bool,
    "final_programming_completed_date" timestamp,
    "slab_smith_used" bool NOT NULL,
    "fp_not_needed" bool NOT NULL,
    "confirmed_date" timestamp,
    "wj_time_minutes" int4,
    "wj_linft" float8,
    "edging_linft" float8,
    "cnc_linft" float8,
    "miter_linft" float8,
    "installation_date" timestamp,
    "saw_cut_lnft" float8,
    "current_stage" varchar(255),
    "next_stage" varchar(255),
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "cost_of_stone_id" int4,
    "slabsmith_completed_date" timestamp,
    "sales_ct_completed_date" timestamp,
    "template_completed_date" timestamp,
    "predraft_completed_date" timestamp,
    "draft_completed_date" timestamp,
    "revision_completed_date" timestamp,
    "sct_completed_date" timestamp,
    "slab_smith_approved" bool,
    "block_drawing_approved" bool,
    "shop_est_completion_date" timestamp,
    "saw_miter_lnft" float8,
    "wj_miter_lnft" float8,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS cnc_draftings_id_seq;

-- Table Definition
CREATE TABLE "public"."cnc_draftings" (
    "id" int4 NOT NULL DEFAULT nextval('cnc_draftings_id_seq'::regclass),
    "drafter_id" int4 NOT NULL,
    "fab_id" int4 NOT NULL,
    "scheduled_start_date" timestamp NOT NULL,
    "scheduled_end_date" timestamp NOT NULL,
    "drafter_start_date" timestamp,
    "drafter_end_date" timestamp,
    "status_id" int4 NOT NULL,
    "total_sqft" float8,
    "no_of_pieces" int4,
    "cad_review_complete" bool,
    "draft_completed" bool,
    "notes" varchar,
    "current_stage" varchar,
    "total_sqft_required_to_draft" varchar NOT NULL,
    "total_sqft_drafted" float8,
    "no_of_piece_drafted" int4,
    "draft_note" varchar,
    "mentions" varchar,
    "total_hours_drafted" float8,
    "is_completed" bool NOT NULL,
    "file_ids" varchar,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS draftings_id_seq;

-- Table Definition
CREATE TABLE "public"."draftings" (
    "id" int4 NOT NULL DEFAULT nextval('draftings_id_seq'::regclass),
    "drafter_id" int4 NOT NULL,
    "fab_id" int4 NOT NULL,
    "scheduled_start_date" timestamp NOT NULL,
    "scheduled_end_date" timestamp NOT NULL,
    "drafter_start_date" timestamp,
    "drafter_end_date" timestamp,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "file_ids" varchar,
    "no_of_piece_drafted" int4,
    "total_sqft_required_to_draft" varchar NOT NULL,
    "total_sqft_drafted" float8,
    "draft_note" varchar,
    "mentions" varchar,
    "total_hours_drafted" float8,
    "is_redrafting" bool NOT NULL,
    "is_completed" bool NOT NULL,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS fab_notes_id_seq;

-- Table Definition
CREATE TABLE "public"."fab_notes" (
    "id" int4 NOT NULL DEFAULT nextval('fab_notes_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "stage" varchar(255) NOT NULL,
    "note" text,
    "created_by" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS installer_job_timer_sessions_id_seq;

-- Table Definition
CREATE TABLE "public"."installer_job_timer_sessions" (
    "id" int4 NOT NULL DEFAULT nextval('installer_job_timer_sessions_id_seq'::regclass),
    "job_id" int4 NOT NULL,
    "fab_id" int4,
    "installer_id" int4 NOT NULL,
    "installer_role" varchar(20) NOT NULL,
    "status" varchar(20) NOT NULL,
    "session_start_at" timestamp NOT NULL,
    "current_run_start_at" timestamp,
    "current_pause_start_at" timestamp,
    "stopped_at" timestamp,
    "total_work_seconds" int4 NOT NULL,
    "total_pause_seconds" int4 NOT NULL,
    "sqft_installed" float8,
    "sqft_not_installed" float8,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS operator_job_timer_sessions_id_seq;

-- Table Definition
CREATE TABLE "public"."operator_job_timer_sessions" (
    "id" int4 NOT NULL DEFAULT nextval('operator_job_timer_sessions_id_seq'::regclass),
    "job_id" int4 NOT NULL,
    "fab_id" int4,
    "operator_id" int4 NOT NULL,
    "workstation_id" int4,
    "status" varchar(20) NOT NULL,
    "session_start_at" timestamp NOT NULL,
    "current_run_start_at" timestamp,
    "current_pause_start_at" timestamp,
    "stopped_at" timestamp,
    "total_work_seconds" int4 NOT NULL,
    "total_pause_seconds" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS shop_cut_plans_id_seq;

-- Table Definition
CREATE TABLE "public"."shop_cut_plans" (
    "id" int4 NOT NULL DEFAULT nextval('shop_cut_plans_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "workstation_id" int4 NOT NULL,
    "planning_section_id" int4 NOT NULL,
    "user_id" int4 NOT NULL,
    "sequence" int4 NOT NULL,
    "estimated_hours" float8 NOT NULL,
    "scheduled_start_date" timestamp,
    "actual_start_date" timestamp,
    "actual_end_date" timestamp,
    "work_percentage" int4 NOT NULL,
    "notes" varchar,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "scheduled_end_date" timestamp,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS revisions_id_seq;

-- Table Definition
CREATE TABLE "public"."revisions" (
    "id" int4 NOT NULL DEFAULT nextval('revisions_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "revision_type" varchar NOT NULL,
    "requested_by" int4 NOT NULL,
    "assigned_to" int4,
    "scheduled_start_date" timestamp,
    "scheduled_end_date" timestamp,
    "actual_start_date" timestamp,
    "actual_end_date" timestamp,
    "revision_reason" varchar,
    "revision_notes" varchar,
    "department" varchar(255),
    "person_name" varchar(255),
    "is_completed" bool NOT NULL,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "file_ids" varchar,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS sales_cts_id_seq;

-- Table Definition
CREATE TABLE "public"."sales_cts" (
    "id" int4 NOT NULL DEFAULT nextval('sales_cts_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "revision_type" varchar,
    "is_revision_needed" bool NOT NULL,
    "is_revision_completed" bool,
    "is_completed" bool NOT NULL,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "no_of_revisions" varchar,
    "current_revision_count" varchar,
    "revision_reason" varchar,
    "slab_smith_type" varchar NOT NULL,
    "drafter_id" int4 NOT NULL,
    "start_date" timestamp NOT NULL,
    "end_date" timestamp NOT NULL,
    "total_sqft_completed" varchar,
    "file_ids" varchar,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS shop_notes_id_seq;

-- Table Definition
CREATE TABLE "public"."shop_notes" (
    "id" int4 NOT NULL DEFAULT nextval('shop_notes_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "note" varchar NOT NULL,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS templater_job_timer_sessions_id_seq;

-- Table Definition
CREATE TABLE "public"."templater_job_timer_sessions" (
    "id" int4 NOT NULL DEFAULT nextval('templater_job_timer_sessions_id_seq'::regclass),
    "job_id" int4 NOT NULL,
    "fab_id" int4,
    "templater_id" int4 NOT NULL,
    "status" varchar(20) NOT NULL,
    "session_start_at" timestamp NOT NULL,
    "current_run_start_at" timestamp,
    "current_pause_start_at" timestamp,
    "stopped_at" timestamp,
    "total_work_seconds" int4 NOT NULL,
    "total_pause_seconds" int4 NOT NULL,
    "sqft_templated" float8,
    "sqft_not_templated" float8,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS shop_revisions_id_seq;

-- Table Definition
CREATE TABLE "public"."shop_revisions" (
    "id" int4 NOT NULL DEFAULT nextval('shop_revisions_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "revision_note" varchar NOT NULL,
    "requested_by" int4 NOT NULL,
    "assigned_to" int4,
    "revision_feedback" varchar,
    "revision_completed" bool NOT NULL,
    "completed_at" timestamp,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "file_ids" varchar,
    "shop_revision_type" text,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS files_id_seq;

-- Table Definition
CREATE TABLE "public"."files" (
    "id" int4 NOT NULL DEFAULT nextval('files_id_seq'::regclass),
    "name" varchar(255) NOT NULL,
    "file_path" varchar(255) NOT NULL,
    "file_type" varchar(255) NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp NOT NULL,
    "file_size" varchar(255) NOT NULL,
    "job_id" int4,
    "fab_id" int4,
    "task_id" int4,
    "uploaded_by" int4,
    "stage" varchar,
    "file_design" varchar(255),
    "stage_name" varchar(255),
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS installer_job_timer_events_id_seq;

-- Table Definition
CREATE TABLE "public"."installer_job_timer_events" (
    "id" int4 NOT NULL DEFAULT nextval('installer_job_timer_events_id_seq'::regclass),
    "session_id" int4 NOT NULL,
    "job_id" int4 NOT NULL,
    "fab_id" int4,
    "installer_id" int4 NOT NULL,
    "action" varchar(20) NOT NULL,
    "event_at" timestamp NOT NULL,
    "note" varchar,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS operator_job_timer_events_id_seq;

-- Table Definition
CREATE TABLE "public"."operator_job_timer_events" (
    "id" int4 NOT NULL DEFAULT nextval('operator_job_timer_events_id_seq'::regclass),
    "session_id" int4 NOT NULL,
    "job_id" int4 NOT NULL,
    "fab_id" int4,
    "operator_id" int4 NOT NULL,
    "workstation_id" int4,
    "action" varchar(20) NOT NULL,
    "event_at" timestamp NOT NULL,
    "note" varchar,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_events_fab_id ON public.operator_job_timer_events USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_events_job_id ON public.operator_job_timer_events USING btree (job_id);
CREATE INDEX ix_operator_job_timer_events_operator_id ON public.operator_job_timer_events USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_events_session_id ON public.operator_job_timer_events USING btree (session_id);
CREATE INDEX ix_operator_job_timer_events_workstation_id ON public.operator_job_timer_events USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."operator_job_timer_sessions"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS shop_cut_plan_timer_sessions_id_seq;

-- Table Definition
CREATE TABLE "public"."shop_cut_plan_timer_sessions" (
    "id" int4 NOT NULL DEFAULT nextval('shop_cut_plan_timer_sessions_id_seq'::regclass),
    "shop_cut_plan_id" int4 NOT NULL,
    "operator_id" int4 NOT NULL,
    "status" varchar(20) NOT NULL,
    "session_start_at" timestamp NOT NULL,
    "current_run_start_at" timestamp,
    "current_pause_start_at" timestamp,
    "stopped_at" timestamp,
    "total_work_seconds" int4 NOT NULL,
    "total_pause_seconds" int4 NOT NULL,
    "work_percentage" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_events_fab_id ON public.operator_job_timer_events USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_events_job_id ON public.operator_job_timer_events USING btree (job_id);
CREATE INDEX ix_operator_job_timer_events_operator_id ON public.operator_job_timer_events USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_events_session_id ON public.operator_job_timer_events USING btree (session_id);
CREATE INDEX ix_operator_job_timer_events_workstation_id ON public.operator_job_timer_events USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."operator_job_timer_sessions"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS templater_job_timer_events_id_seq;

-- Table Definition
CREATE TABLE "public"."templater_job_timer_events" (
    "id" int4 NOT NULL DEFAULT nextval('templater_job_timer_events_id_seq'::regclass),
    "session_id" int4 NOT NULL,
    "job_id" int4 NOT NULL,
    "fab_id" int4,
    "templater_id" int4 NOT NULL,
    "action" varchar(20) NOT NULL,
    "event_at" timestamp NOT NULL,
    "note" varchar,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_events_fab_id ON public.operator_job_timer_events USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_events_job_id ON public.operator_job_timer_events USING btree (job_id);
CREATE INDEX ix_operator_job_timer_events_operator_id ON public.operator_job_timer_events USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_events_session_id ON public.operator_job_timer_events USING btree (session_id);
CREATE INDEX ix_operator_job_timer_events_workstation_id ON public.operator_job_timer_events USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."operator_job_timer_sessions"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_events_fab_id ON public.templater_job_timer_events USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_events_job_id ON public.templater_job_timer_events USING btree (job_id);
CREATE INDEX ix_templater_job_timer_events_session_id ON public.templater_job_timer_events USING btree (session_id);
CREATE INDEX ix_templater_job_timer_events_templater_id ON public.templater_job_timer_events USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."templater_job_timer_sessions"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS shop_cut_plan_timer_events_id_seq;

-- Table Definition
CREATE TABLE "public"."shop_cut_plan_timer_events" (
    "id" int4 NOT NULL DEFAULT nextval('shop_cut_plan_timer_events_id_seq'::regclass),
    "session_id" int4 NOT NULL,
    "shop_cut_plan_id" int4 NOT NULL,
    "operator_id" int4 NOT NULL,
    "action" varchar(20) NOT NULL,
    "event_at" timestamp NOT NULL,
    "note" varchar,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_events_fab_id ON public.operator_job_timer_events USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_events_job_id ON public.operator_job_timer_events USING btree (job_id);
CREATE INDEX ix_operator_job_timer_events_operator_id ON public.operator_job_timer_events USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_events_session_id ON public.operator_job_timer_events USING btree (session_id);
CREATE INDEX ix_operator_job_timer_events_workstation_id ON public.operator_job_timer_events USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."operator_job_timer_sessions"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_events_fab_id ON public.templater_job_timer_events USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_events_job_id ON public.templater_job_timer_events USING btree (job_id);
CREATE INDEX ix_templater_job_timer_events_session_id ON public.templater_job_timer_events USING btree (session_id);
CREATE INDEX ix_templater_job_timer_events_templater_id ON public.templater_job_timer_events USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."templater_job_timer_sessions"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."shop_cut_plan_timer_sessions"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS slab_smith_sessions_id_seq;

-- Table Definition
CREATE TABLE "public"."slab_smith_sessions" (
    "id" int4 NOT NULL DEFAULT nextval('slab_smith_sessions_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "user_id" int4 NOT NULL,
    "status" varchar NOT NULL DEFAULT 'active'::character varying,
    "session_start_time" timestamp NOT NULL,
    "session_end_time" timestamp,
    "current_pause_start_time" timestamp,
    "total_pause_duration" int4 NOT NULL DEFAULT 0,
    "total_time_spent" int4 NOT NULL DEFAULT 0,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_events_fab_id ON public.operator_job_timer_events USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_events_job_id ON public.operator_job_timer_events USING btree (job_id);
CREATE INDEX ix_operator_job_timer_events_operator_id ON public.operator_job_timer_events USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_events_session_id ON public.operator_job_timer_events USING btree (session_id);
CREATE INDEX ix_operator_job_timer_events_workstation_id ON public.operator_job_timer_events USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."operator_job_timer_sessions"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_events_fab_id ON public.templater_job_timer_events USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_events_job_id ON public.templater_job_timer_events USING btree (job_id);
CREATE INDEX ix_templater_job_timer_events_session_id ON public.templater_job_timer_events USING btree (session_id);
CREATE INDEX ix_templater_job_timer_events_templater_id ON public.templater_job_timer_events USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."templater_job_timer_sessions"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."shop_cut_plan_timer_sessions"("id");


-- Indices
CREATE INDEX ix_slab_smith_sessions_fab_id ON public.slab_smith_sessions USING btree (fab_id);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS slab_smith_session_notes_id_seq;

-- Table Definition
CREATE TABLE "public"."slab_smith_session_notes" (
    "id" int4 NOT NULL DEFAULT nextval('slab_smith_session_notes_id_seq'::regclass),
    "session_id" int4 NOT NULL,
    "fab_id" int4 NOT NULL,
    "user_id" int4 NOT NULL,
    "action" varchar NOT NULL,
    "timestamp" timestamp NOT NULL,
    "note" varchar,
    "created_at" timestamp NOT NULL,
    "sqft_completed" float8,
    "work_percentage_done" float8,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_events_fab_id ON public.operator_job_timer_events USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_events_job_id ON public.operator_job_timer_events USING btree (job_id);
CREATE INDEX ix_operator_job_timer_events_operator_id ON public.operator_job_timer_events USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_events_session_id ON public.operator_job_timer_events USING btree (session_id);
CREATE INDEX ix_operator_job_timer_events_workstation_id ON public.operator_job_timer_events USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."operator_job_timer_sessions"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_events_fab_id ON public.templater_job_timer_events USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_events_job_id ON public.templater_job_timer_events USING btree (job_id);
CREATE INDEX ix_templater_job_timer_events_session_id ON public.templater_job_timer_events USING btree (session_id);
CREATE INDEX ix_templater_job_timer_events_templater_id ON public.templater_job_timer_events USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."templater_job_timer_sessions"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."shop_cut_plan_timer_sessions"("id");


-- Indices
CREATE INDEX ix_slab_smith_sessions_fab_id ON public.slab_smith_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_slab_smith_session_notes_session_id ON public.slab_smith_session_notes USING btree (session_id);
CREATE INDEX ix_slab_smith_session_notes_fab_id ON public.slab_smith_session_notes USING btree (fab_id);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS final_programming_sessions_id_seq;

-- Table Definition
CREATE TABLE "public"."final_programming_sessions" (
    "id" int4 NOT NULL DEFAULT nextval('final_programming_sessions_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "user_id" int4 NOT NULL,
    "status" varchar NOT NULL DEFAULT 'active'::character varying,
    "session_start_time" timestamp NOT NULL,
    "session_end_time" timestamp,
    "current_pause_start_time" timestamp,
    "total_pause_duration" int4 NOT NULL DEFAULT 0,
    "total_time_spent" int4 NOT NULL DEFAULT 0,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_events_fab_id ON public.operator_job_timer_events USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_events_job_id ON public.operator_job_timer_events USING btree (job_id);
CREATE INDEX ix_operator_job_timer_events_operator_id ON public.operator_job_timer_events USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_events_session_id ON public.operator_job_timer_events USING btree (session_id);
CREATE INDEX ix_operator_job_timer_events_workstation_id ON public.operator_job_timer_events USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."operator_job_timer_sessions"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_events_fab_id ON public.templater_job_timer_events USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_events_job_id ON public.templater_job_timer_events USING btree (job_id);
CREATE INDEX ix_templater_job_timer_events_session_id ON public.templater_job_timer_events USING btree (session_id);
CREATE INDEX ix_templater_job_timer_events_templater_id ON public.templater_job_timer_events USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."templater_job_timer_sessions"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."shop_cut_plan_timer_sessions"("id");


-- Indices
CREATE INDEX ix_slab_smith_sessions_fab_id ON public.slab_smith_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_slab_smith_session_notes_session_id ON public.slab_smith_session_notes USING btree (session_id);
CREATE INDEX ix_slab_smith_session_notes_fab_id ON public.slab_smith_session_notes USING btree (fab_id);


-- Indices
CREATE INDEX ix_final_programming_sessions_fab_id ON public.final_programming_sessions USING btree (fab_id);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS hcp_payroll_source_configs_id_seq;

-- Table Definition
CREATE TABLE "public"."hcp_payroll_source_configs" (
    "id" int4 NOT NULL DEFAULT nextval('hcp_payroll_source_configs_id_seq'::regclass),
    "name" varchar(255) NOT NULL,
    "base_url" varchar(255) NOT NULL DEFAULT 'https://secure.saashr.com'::character varying,
    "company_id" varchar(100) NOT NULL DEFAULT '83943830'::character varying,
    "grant_type" varchar(100) NOT NULL DEFAULT 'client_credentials'::character varying,
    "client_id" varchar(255),
    "client_secret" varchar(255),
    "report_settings_id" varchar(100) NOT NULL DEFAULT '89798180'::character varying,
    "schedule_type" varchar(50) NOT NULL DEFAULT 'weekly'::character varying,
    "schedule_interval" int4 NOT NULL DEFAULT 1,
    "schedule_weekday" int4 NOT NULL DEFAULT 0,
    "schedule_hour" int4 NOT NULL DEFAULT 1,
    "schedule_minute" int4 NOT NULL DEFAULT 0,
    "is_active" bool NOT NULL DEFAULT true,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "created_by" int4,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_events_fab_id ON public.operator_job_timer_events USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_events_job_id ON public.operator_job_timer_events USING btree (job_id);
CREATE INDEX ix_operator_job_timer_events_operator_id ON public.operator_job_timer_events USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_events_session_id ON public.operator_job_timer_events USING btree (session_id);
CREATE INDEX ix_operator_job_timer_events_workstation_id ON public.operator_job_timer_events USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."operator_job_timer_sessions"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_events_fab_id ON public.templater_job_timer_events USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_events_job_id ON public.templater_job_timer_events USING btree (job_id);
CREATE INDEX ix_templater_job_timer_events_session_id ON public.templater_job_timer_events USING btree (session_id);
CREATE INDEX ix_templater_job_timer_events_templater_id ON public.templater_job_timer_events USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."templater_job_timer_sessions"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."shop_cut_plan_timer_sessions"("id");


-- Indices
CREATE INDEX ix_slab_smith_sessions_fab_id ON public.slab_smith_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_slab_smith_session_notes_session_id ON public.slab_smith_session_notes USING btree (session_id);
CREATE INDEX ix_slab_smith_session_notes_fab_id ON public.slab_smith_session_notes USING btree (fab_id);


-- Indices
CREATE INDEX ix_final_programming_sessions_fab_id ON public.final_programming_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX hcp_payroll_source_configs_name_key ON public.hcp_payroll_source_configs USING btree (name);
CREATE INDEX ix_hcp_payroll_source_configs_base_url ON public.hcp_payroll_source_configs USING btree (base_url);
CREATE INDEX ix_hcp_payroll_source_configs_company_id ON public.hcp_payroll_source_configs USING btree (company_id);
CREATE INDEX ix_hcp_payroll_source_configs_is_active ON public.hcp_payroll_source_configs USING btree (is_active);
CREATE INDEX ix_hcp_payroll_source_configs_name ON public.hcp_payroll_source_configs USING btree (name);
CREATE INDEX ix_hcp_payroll_source_configs_report_settings_id ON public.hcp_payroll_source_configs USING btree (report_settings_id);
ALTER TABLE "public"."hcp_payroll_source_configs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."hcp_payroll_source_configs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS final_programming_session_notes_id_seq;

-- Table Definition
CREATE TABLE "public"."final_programming_session_notes" (
    "id" int4 NOT NULL DEFAULT nextval('final_programming_session_notes_id_seq'::regclass),
    "session_id" int4 NOT NULL,
    "fab_id" int4 NOT NULL,
    "user_id" int4 NOT NULL,
    "action" varchar NOT NULL,
    "timestamp" timestamp NOT NULL,
    "note" varchar,
    "created_at" timestamp NOT NULL,
    "sqft_completed" float8,
    "work_percentage_done" float8,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_events_fab_id ON public.operator_job_timer_events USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_events_job_id ON public.operator_job_timer_events USING btree (job_id);
CREATE INDEX ix_operator_job_timer_events_operator_id ON public.operator_job_timer_events USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_events_session_id ON public.operator_job_timer_events USING btree (session_id);
CREATE INDEX ix_operator_job_timer_events_workstation_id ON public.operator_job_timer_events USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."operator_job_timer_sessions"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_events_fab_id ON public.templater_job_timer_events USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_events_job_id ON public.templater_job_timer_events USING btree (job_id);
CREATE INDEX ix_templater_job_timer_events_session_id ON public.templater_job_timer_events USING btree (session_id);
CREATE INDEX ix_templater_job_timer_events_templater_id ON public.templater_job_timer_events USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."templater_job_timer_sessions"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."shop_cut_plan_timer_sessions"("id");


-- Indices
CREATE INDEX ix_slab_smith_sessions_fab_id ON public.slab_smith_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_slab_smith_session_notes_session_id ON public.slab_smith_session_notes USING btree (session_id);
CREATE INDEX ix_slab_smith_session_notes_fab_id ON public.slab_smith_session_notes USING btree (fab_id);


-- Indices
CREATE INDEX ix_final_programming_sessions_fab_id ON public.final_programming_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX hcp_payroll_source_configs_name_key ON public.hcp_payroll_source_configs USING btree (name);
CREATE INDEX ix_hcp_payroll_source_configs_base_url ON public.hcp_payroll_source_configs USING btree (base_url);
CREATE INDEX ix_hcp_payroll_source_configs_company_id ON public.hcp_payroll_source_configs USING btree (company_id);
CREATE INDEX ix_hcp_payroll_source_configs_is_active ON public.hcp_payroll_source_configs USING btree (is_active);
CREATE INDEX ix_hcp_payroll_source_configs_name ON public.hcp_payroll_source_configs USING btree (name);
CREATE INDEX ix_hcp_payroll_source_configs_report_settings_id ON public.hcp_payroll_source_configs USING btree (report_settings_id);
ALTER TABLE "public"."hcp_payroll_source_configs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."hcp_payroll_source_configs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_final_programming_session_notes_session_id ON public.final_programming_session_notes USING btree (session_id);
CREATE INDEX ix_final_programming_session_notes_fab_id ON public.final_programming_session_notes USING btree (fab_id);
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS hcp_payroll_ingestion_runs_id_seq;

-- Table Definition
CREATE TABLE "public"."hcp_payroll_ingestion_runs" (
    "id" int4 NOT NULL DEFAULT nextval('hcp_payroll_ingestion_runs_id_seq'::regclass),
    "source_config_id" int4 NOT NULL,
    "status" varchar(50) NOT NULL,
    "token_request_url" varchar(500),
    "token_response_json" jsonb,
    "token_acquired_at" timestamp,
    "token_expires_in" int4,
    "report_request_url" varchar(500),
    "report_http_status" int4,
    "report_content_type" varchar(255),
    "error_message" varchar(2000),
    "row_count" int4 NOT NULL DEFAULT 0,
    "created_at" timestamp NOT NULL,
    "started_at" timestamp NOT NULL,
    "finished_at" timestamp,
    "created_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_events_fab_id ON public.operator_job_timer_events USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_events_job_id ON public.operator_job_timer_events USING btree (job_id);
CREATE INDEX ix_operator_job_timer_events_operator_id ON public.operator_job_timer_events USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_events_session_id ON public.operator_job_timer_events USING btree (session_id);
CREATE INDEX ix_operator_job_timer_events_workstation_id ON public.operator_job_timer_events USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."operator_job_timer_sessions"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_events_fab_id ON public.templater_job_timer_events USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_events_job_id ON public.templater_job_timer_events USING btree (job_id);
CREATE INDEX ix_templater_job_timer_events_session_id ON public.templater_job_timer_events USING btree (session_id);
CREATE INDEX ix_templater_job_timer_events_templater_id ON public.templater_job_timer_events USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."templater_job_timer_sessions"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."shop_cut_plan_timer_sessions"("id");


-- Indices
CREATE INDEX ix_slab_smith_sessions_fab_id ON public.slab_smith_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_slab_smith_session_notes_session_id ON public.slab_smith_session_notes USING btree (session_id);
CREATE INDEX ix_slab_smith_session_notes_fab_id ON public.slab_smith_session_notes USING btree (fab_id);


-- Indices
CREATE INDEX ix_final_programming_sessions_fab_id ON public.final_programming_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX hcp_payroll_source_configs_name_key ON public.hcp_payroll_source_configs USING btree (name);
CREATE INDEX ix_hcp_payroll_source_configs_base_url ON public.hcp_payroll_source_configs USING btree (base_url);
CREATE INDEX ix_hcp_payroll_source_configs_company_id ON public.hcp_payroll_source_configs USING btree (company_id);
CREATE INDEX ix_hcp_payroll_source_configs_is_active ON public.hcp_payroll_source_configs USING btree (is_active);
CREATE INDEX ix_hcp_payroll_source_configs_name ON public.hcp_payroll_source_configs USING btree (name);
CREATE INDEX ix_hcp_payroll_source_configs_report_settings_id ON public.hcp_payroll_source_configs USING btree (report_settings_id);
ALTER TABLE "public"."hcp_payroll_source_configs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."hcp_payroll_source_configs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_final_programming_session_notes_session_id ON public.final_programming_session_notes USING btree (session_id);
CREATE INDEX ix_final_programming_session_notes_fab_id ON public.final_programming_session_notes USING btree (fab_id);


-- Indices
CREATE INDEX ix_hcp_payroll_ingestion_runs_source_config_id ON public.hcp_payroll_ingestion_runs USING btree (source_config_id);
CREATE INDEX ix_hcp_payroll_ingestion_runs_status ON public.hcp_payroll_ingestion_runs USING btree (status);
ALTER TABLE "public"."hcp_payroll_ingestion_runs" ADD FOREIGN KEY ("source_config_id") REFERENCES "public"."hcp_payroll_source_configs"("id");
ALTER TABLE "public"."hcp_payroll_ingestion_runs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS hcp_payroll_report_snapshots_id_seq;

-- Table Definition
CREATE TABLE "public"."hcp_payroll_report_snapshots" (
    "id" int4 NOT NULL DEFAULT nextval('hcp_payroll_report_snapshots_id_seq'::regclass),
    "source_config_id" int4 NOT NULL,
    "ingestion_run_id" int4 NOT NULL,
    "report_settings_id" varchar(100) NOT NULL,
    "report_title" varchar(255),
    "payload_format" varchar(50) NOT NULL,
    "raw_payload_text" text NOT NULL,
    "row_count" int4 NOT NULL DEFAULT 0,
    "created_at" timestamp NOT NULL,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_events_fab_id ON public.operator_job_timer_events USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_events_job_id ON public.operator_job_timer_events USING btree (job_id);
CREATE INDEX ix_operator_job_timer_events_operator_id ON public.operator_job_timer_events USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_events_session_id ON public.operator_job_timer_events USING btree (session_id);
CREATE INDEX ix_operator_job_timer_events_workstation_id ON public.operator_job_timer_events USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."operator_job_timer_sessions"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_events_fab_id ON public.templater_job_timer_events USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_events_job_id ON public.templater_job_timer_events USING btree (job_id);
CREATE INDEX ix_templater_job_timer_events_session_id ON public.templater_job_timer_events USING btree (session_id);
CREATE INDEX ix_templater_job_timer_events_templater_id ON public.templater_job_timer_events USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."templater_job_timer_sessions"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."shop_cut_plan_timer_sessions"("id");


-- Indices
CREATE INDEX ix_slab_smith_sessions_fab_id ON public.slab_smith_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_slab_smith_session_notes_session_id ON public.slab_smith_session_notes USING btree (session_id);
CREATE INDEX ix_slab_smith_session_notes_fab_id ON public.slab_smith_session_notes USING btree (fab_id);


-- Indices
CREATE INDEX ix_final_programming_sessions_fab_id ON public.final_programming_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX hcp_payroll_source_configs_name_key ON public.hcp_payroll_source_configs USING btree (name);
CREATE INDEX ix_hcp_payroll_source_configs_base_url ON public.hcp_payroll_source_configs USING btree (base_url);
CREATE INDEX ix_hcp_payroll_source_configs_company_id ON public.hcp_payroll_source_configs USING btree (company_id);
CREATE INDEX ix_hcp_payroll_source_configs_is_active ON public.hcp_payroll_source_configs USING btree (is_active);
CREATE INDEX ix_hcp_payroll_source_configs_name ON public.hcp_payroll_source_configs USING btree (name);
CREATE INDEX ix_hcp_payroll_source_configs_report_settings_id ON public.hcp_payroll_source_configs USING btree (report_settings_id);
ALTER TABLE "public"."hcp_payroll_source_configs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."hcp_payroll_source_configs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_final_programming_session_notes_session_id ON public.final_programming_session_notes USING btree (session_id);
CREATE INDEX ix_final_programming_session_notes_fab_id ON public.final_programming_session_notes USING btree (fab_id);


-- Indices
CREATE INDEX ix_hcp_payroll_ingestion_runs_source_config_id ON public.hcp_payroll_ingestion_runs USING btree (source_config_id);
CREATE INDEX ix_hcp_payroll_ingestion_runs_status ON public.hcp_payroll_ingestion_runs USING btree (status);
ALTER TABLE "public"."hcp_payroll_ingestion_runs" ADD FOREIGN KEY ("source_config_id") REFERENCES "public"."hcp_payroll_source_configs"("id");
ALTER TABLE "public"."hcp_payroll_ingestion_runs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_hcp_payroll_report_snapshots_source_config_id ON public.hcp_payroll_report_snapshots USING btree (source_config_id);
CREATE INDEX ix_hcp_payroll_report_snapshots_ingestion_run_id ON public.hcp_payroll_report_snapshots USING btree (ingestion_run_id);
CREATE INDEX ix_hcp_payroll_report_snapshots_report_settings_id ON public.hcp_payroll_report_snapshots USING btree (report_settings_id);
ALTER TABLE "public"."hcp_payroll_report_snapshots" ADD FOREIGN KEY ("ingestion_run_id") REFERENCES "public"."hcp_payroll_ingestion_runs"("id");
ALTER TABLE "public"."hcp_payroll_report_snapshots" ADD FOREIGN KEY ("source_config_id") REFERENCES "public"."hcp_payroll_source_configs"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS hcp_payroll_report_rows_id_seq;

-- Table Definition
CREATE TABLE "public"."hcp_payroll_report_rows" (
    "id" int4 NOT NULL DEFAULT nextval('hcp_payroll_report_rows_id_seq'::regclass),
    "snapshot_id" int4 NOT NULL,
    "source_config_id" int4 NOT NULL,
    "ingestion_run_id" int4 NOT NULL,
    "row_kind" varchar(50) NOT NULL,
    "row_index" int4 NOT NULL,
    "cost_center_name" varchar(255),
    "employee_first_name" varchar(255),
    "employee_last_name" varchar(255),
    "hourly_pay" float8,
    "regular_hours" float8,
    "holiday_hours" float8,
    "pto_hours" float8,
    "total_reg_pto_hol_wages" float8,
    "overtime_hours" float8,
    "total_ot_wages" float8,
    "raw_line_text" text,
    "created_at" timestamp NOT NULL,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_events_fab_id ON public.operator_job_timer_events USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_events_job_id ON public.operator_job_timer_events USING btree (job_id);
CREATE INDEX ix_operator_job_timer_events_operator_id ON public.operator_job_timer_events USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_events_session_id ON public.operator_job_timer_events USING btree (session_id);
CREATE INDEX ix_operator_job_timer_events_workstation_id ON public.operator_job_timer_events USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."operator_job_timer_sessions"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_events_fab_id ON public.templater_job_timer_events USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_events_job_id ON public.templater_job_timer_events USING btree (job_id);
CREATE INDEX ix_templater_job_timer_events_session_id ON public.templater_job_timer_events USING btree (session_id);
CREATE INDEX ix_templater_job_timer_events_templater_id ON public.templater_job_timer_events USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."templater_job_timer_sessions"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."shop_cut_plan_timer_sessions"("id");


-- Indices
CREATE INDEX ix_slab_smith_sessions_fab_id ON public.slab_smith_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_slab_smith_session_notes_session_id ON public.slab_smith_session_notes USING btree (session_id);
CREATE INDEX ix_slab_smith_session_notes_fab_id ON public.slab_smith_session_notes USING btree (fab_id);


-- Indices
CREATE INDEX ix_final_programming_sessions_fab_id ON public.final_programming_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX hcp_payroll_source_configs_name_key ON public.hcp_payroll_source_configs USING btree (name);
CREATE INDEX ix_hcp_payroll_source_configs_base_url ON public.hcp_payroll_source_configs USING btree (base_url);
CREATE INDEX ix_hcp_payroll_source_configs_company_id ON public.hcp_payroll_source_configs USING btree (company_id);
CREATE INDEX ix_hcp_payroll_source_configs_is_active ON public.hcp_payroll_source_configs USING btree (is_active);
CREATE INDEX ix_hcp_payroll_source_configs_name ON public.hcp_payroll_source_configs USING btree (name);
CREATE INDEX ix_hcp_payroll_source_configs_report_settings_id ON public.hcp_payroll_source_configs USING btree (report_settings_id);
ALTER TABLE "public"."hcp_payroll_source_configs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."hcp_payroll_source_configs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_final_programming_session_notes_session_id ON public.final_programming_session_notes USING btree (session_id);
CREATE INDEX ix_final_programming_session_notes_fab_id ON public.final_programming_session_notes USING btree (fab_id);


-- Indices
CREATE INDEX ix_hcp_payroll_ingestion_runs_source_config_id ON public.hcp_payroll_ingestion_runs USING btree (source_config_id);
CREATE INDEX ix_hcp_payroll_ingestion_runs_status ON public.hcp_payroll_ingestion_runs USING btree (status);
ALTER TABLE "public"."hcp_payroll_ingestion_runs" ADD FOREIGN KEY ("source_config_id") REFERENCES "public"."hcp_payroll_source_configs"("id");
ALTER TABLE "public"."hcp_payroll_ingestion_runs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_hcp_payroll_report_snapshots_source_config_id ON public.hcp_payroll_report_snapshots USING btree (source_config_id);
CREATE INDEX ix_hcp_payroll_report_snapshots_ingestion_run_id ON public.hcp_payroll_report_snapshots USING btree (ingestion_run_id);
CREATE INDEX ix_hcp_payroll_report_snapshots_report_settings_id ON public.hcp_payroll_report_snapshots USING btree (report_settings_id);
ALTER TABLE "public"."hcp_payroll_report_snapshots" ADD FOREIGN KEY ("ingestion_run_id") REFERENCES "public"."hcp_payroll_ingestion_runs"("id");
ALTER TABLE "public"."hcp_payroll_report_snapshots" ADD FOREIGN KEY ("source_config_id") REFERENCES "public"."hcp_payroll_source_configs"("id");


-- Indices
CREATE INDEX ix_hcp_payroll_report_rows_snapshot_id ON public.hcp_payroll_report_rows USING btree (snapshot_id);
CREATE INDEX ix_hcp_payroll_report_rows_source_config_id ON public.hcp_payroll_report_rows USING btree (source_config_id);
CREATE INDEX ix_hcp_payroll_report_rows_ingestion_run_id ON public.hcp_payroll_report_rows USING btree (ingestion_run_id);
CREATE INDEX ix_hcp_payroll_report_rows_row_kind ON public.hcp_payroll_report_rows USING btree (row_kind);
CREATE INDEX ix_hcp_payroll_report_rows_row_index ON public.hcp_payroll_report_rows USING btree (row_index);
CREATE INDEX ix_hcp_payroll_report_rows_cost_center_name ON public.hcp_payroll_report_rows USING btree (cost_center_name);
ALTER TABLE "public"."hcp_payroll_report_rows" ADD FOREIGN KEY ("source_config_id") REFERENCES "public"."hcp_payroll_source_configs"("id");
ALTER TABLE "public"."hcp_payroll_report_rows" ADD FOREIGN KEY ("ingestion_run_id") REFERENCES "public"."hcp_payroll_ingestion_runs"("id");
ALTER TABLE "public"."hcp_payroll_report_rows" ADD FOREIGN KEY ("snapshot_id") REFERENCES "public"."hcp_payroll_report_snapshots"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS installer_rate_history_id_seq;

-- Table Definition
CREATE TABLE "public"."installer_rate_history" (
    "id" int4 NOT NULL DEFAULT nextval('installer_rate_history_id_seq'::regclass),
    "installer_id" int4 NOT NULL,
    "hourly_rate" float8 NOT NULL,
    "effective_from" timestamp NOT NULL,
    "effective_to" timestamp,
    "is_active" bool NOT NULL DEFAULT true,
    "created_at" timestamp NOT NULL,
    "created_by" int4 NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_events_fab_id ON public.operator_job_timer_events USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_events_job_id ON public.operator_job_timer_events USING btree (job_id);
CREATE INDEX ix_operator_job_timer_events_operator_id ON public.operator_job_timer_events USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_events_session_id ON public.operator_job_timer_events USING btree (session_id);
CREATE INDEX ix_operator_job_timer_events_workstation_id ON public.operator_job_timer_events USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."operator_job_timer_sessions"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_events_fab_id ON public.templater_job_timer_events USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_events_job_id ON public.templater_job_timer_events USING btree (job_id);
CREATE INDEX ix_templater_job_timer_events_session_id ON public.templater_job_timer_events USING btree (session_id);
CREATE INDEX ix_templater_job_timer_events_templater_id ON public.templater_job_timer_events USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."templater_job_timer_sessions"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."shop_cut_plan_timer_sessions"("id");


-- Indices
CREATE INDEX ix_slab_smith_sessions_fab_id ON public.slab_smith_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_slab_smith_session_notes_session_id ON public.slab_smith_session_notes USING btree (session_id);
CREATE INDEX ix_slab_smith_session_notes_fab_id ON public.slab_smith_session_notes USING btree (fab_id);


-- Indices
CREATE INDEX ix_final_programming_sessions_fab_id ON public.final_programming_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX hcp_payroll_source_configs_name_key ON public.hcp_payroll_source_configs USING btree (name);
CREATE INDEX ix_hcp_payroll_source_configs_base_url ON public.hcp_payroll_source_configs USING btree (base_url);
CREATE INDEX ix_hcp_payroll_source_configs_company_id ON public.hcp_payroll_source_configs USING btree (company_id);
CREATE INDEX ix_hcp_payroll_source_configs_is_active ON public.hcp_payroll_source_configs USING btree (is_active);
CREATE INDEX ix_hcp_payroll_source_configs_name ON public.hcp_payroll_source_configs USING btree (name);
CREATE INDEX ix_hcp_payroll_source_configs_report_settings_id ON public.hcp_payroll_source_configs USING btree (report_settings_id);
ALTER TABLE "public"."hcp_payroll_source_configs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."hcp_payroll_source_configs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_final_programming_session_notes_session_id ON public.final_programming_session_notes USING btree (session_id);
CREATE INDEX ix_final_programming_session_notes_fab_id ON public.final_programming_session_notes USING btree (fab_id);


-- Indices
CREATE INDEX ix_hcp_payroll_ingestion_runs_source_config_id ON public.hcp_payroll_ingestion_runs USING btree (source_config_id);
CREATE INDEX ix_hcp_payroll_ingestion_runs_status ON public.hcp_payroll_ingestion_runs USING btree (status);
ALTER TABLE "public"."hcp_payroll_ingestion_runs" ADD FOREIGN KEY ("source_config_id") REFERENCES "public"."hcp_payroll_source_configs"("id");
ALTER TABLE "public"."hcp_payroll_ingestion_runs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_hcp_payroll_report_snapshots_source_config_id ON public.hcp_payroll_report_snapshots USING btree (source_config_id);
CREATE INDEX ix_hcp_payroll_report_snapshots_ingestion_run_id ON public.hcp_payroll_report_snapshots USING btree (ingestion_run_id);
CREATE INDEX ix_hcp_payroll_report_snapshots_report_settings_id ON public.hcp_payroll_report_snapshots USING btree (report_settings_id);
ALTER TABLE "public"."hcp_payroll_report_snapshots" ADD FOREIGN KEY ("ingestion_run_id") REFERENCES "public"."hcp_payroll_ingestion_runs"("id");
ALTER TABLE "public"."hcp_payroll_report_snapshots" ADD FOREIGN KEY ("source_config_id") REFERENCES "public"."hcp_payroll_source_configs"("id");


-- Indices
CREATE INDEX ix_hcp_payroll_report_rows_snapshot_id ON public.hcp_payroll_report_rows USING btree (snapshot_id);
CREATE INDEX ix_hcp_payroll_report_rows_source_config_id ON public.hcp_payroll_report_rows USING btree (source_config_id);
CREATE INDEX ix_hcp_payroll_report_rows_ingestion_run_id ON public.hcp_payroll_report_rows USING btree (ingestion_run_id);
CREATE INDEX ix_hcp_payroll_report_rows_row_kind ON public.hcp_payroll_report_rows USING btree (row_kind);
CREATE INDEX ix_hcp_payroll_report_rows_row_index ON public.hcp_payroll_report_rows USING btree (row_index);
CREATE INDEX ix_hcp_payroll_report_rows_cost_center_name ON public.hcp_payroll_report_rows USING btree (cost_center_name);
ALTER TABLE "public"."hcp_payroll_report_rows" ADD FOREIGN KEY ("source_config_id") REFERENCES "public"."hcp_payroll_source_configs"("id");
ALTER TABLE "public"."hcp_payroll_report_rows" ADD FOREIGN KEY ("ingestion_run_id") REFERENCES "public"."hcp_payroll_ingestion_runs"("id");
ALTER TABLE "public"."hcp_payroll_report_rows" ADD FOREIGN KEY ("snapshot_id") REFERENCES "public"."hcp_payroll_report_snapshots"("id");


-- Indices
CREATE INDEX ix_installer_rate_history_installer_id ON public.installer_rate_history USING btree (installer_id);
CREATE INDEX ix_installer_rate_history_effective_from ON public.installer_rate_history USING btree (effective_from);
CREATE INDEX ix_installer_rate_history_effective_to ON public.installer_rate_history USING btree (effective_to);
CREATE INDEX ix_installer_rate_history_is_active ON public.installer_rate_history USING btree (is_active);
ALTER TABLE "public"."installer_rate_history" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_rate_history" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_rate_history" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
-- Sequence and defined type
CREATE SEQUENCE IF NOT EXISTS install_completions_id_seq;

-- Table Definition
CREATE TABLE "public"."install_completions" (
    "id" int4 NOT NULL DEFAULT nextval('install_completions_id_seq'::regclass),
    "fab_id" int4 NOT NULL,
    "installer_id" int4 NOT NULL,
    "install_date" timestamp NOT NULL,
    "completion_date" timestamp,
    "total_sqft_installed" varchar,
    "customer_signature" varchar,
    "completion_notes" varchar,
    "is_completed" bool NOT NULL,
    "status_id" int4 NOT NULL,
    "created_at" timestamp NOT NULL,
    "updated_at" timestamp,
    "updated_by" int4,
    "file_ids" varchar,
    "is_confirmed" bool NOT NULL DEFAULT false,
    PRIMARY KEY ("id")
);



-- Indices
CREATE UNIQUE INDEX alembic_version_pkc ON public.alembic_version USING btree (version_num);


-- Indices
CREATE INDEX ix_cnc_drafting_session_notes_fab_id ON public.cnc_drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_cnc_drafting_session_notes_session_id ON public.cnc_drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_cnc_drafting_sessions_fab_id ON public.cnc_drafting_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_drafting_session_notes_fab_id ON public.drafting_session_notes USING btree (fab_id);
CREATE INDEX ix_drafting_session_notes_session_id ON public.drafting_session_notes USING btree (session_id);


-- Indices
CREATE INDEX ix_drafting_sessions_fab_id ON public.drafting_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX ix_fab_type_name ON public.fab_type USING btree (name);


-- Indices
CREATE INDEX ix_users_email ON public.users USING btree (email);
CREATE INDEX ix_users_employee_id ON public.users USING btree (employee_id);
CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);
ALTER TABLE "public"."users" ADD FOREIGN KEY ("department") REFERENCES "public"."departments"("id");


-- Indices
CREATE UNIQUE INDEX status_value_id_key ON public.status USING btree (value_id);


-- Indices
CREATE UNIQUE INDEX ix_departments_name ON public.departments USING btree (name);
ALTER TABLE "public"."departments" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_action_menus_code ON public.action_menus USING btree (code);


-- Indices
CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);
ALTER TABLE "public"."roles" ADD FOREIGN KEY ("status") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_permissions_name ON public.permissions USING btree (name);
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("action_menu_id") REFERENCES "public"."action_menus"("id");
ALTER TABLE "public"."role_permissions" ADD FOREIGN KEY ("permission_id") REFERENCES "public"."permissions"("id");


-- Indices
CREATE UNIQUE INDEX ix_accounts_account_number ON public.accounts USING btree (account_number);
CREATE UNIQUE INDEX ix_accounts_name ON public.accounts USING btree (name);
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."accounts" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_edges_name ON public.edges USING btree (name);
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."edges" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_password_reset_otps_user_id ON public.password_reset_otps USING btree (user_id);
ALTER TABLE "public"."password_reset_otps" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_planning_sections_plan_name ON public.planning_sections USING btree (plan_name);
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_service_level_settings_fab_type ON public.service_level_settings USING btree (fab_type);
CREATE INDEX ix_service_level_settings_stage_name ON public.service_level_settings USING btree (stage_name);
ALTER TABLE "public"."service_level_settings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_plannings" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE UNIQUE INDEX ix_stone_thickness_thickness ON public.stone_thickness USING btree (thickness);
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_thickness" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");


-- Indices
CREATE INDEX ix_audit_trails_user_created ON public.audit_trails USING btree (user_id, created_at);
CREATE INDEX ix_audit_trails_resource_record_created ON public.audit_trails USING btree (resource_type, record_id, created_at);
CREATE INDEX ix_audit_trails_operation_created ON public.audit_trails USING btree (operation, created_at);
ALTER TABLE "public"."audit_trails" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE UNIQUE INDEX ix_work_stations_name ON public.work_stations USING btree (name);
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."work_stations" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");


-- Indices
CREATE UNIQUE INDEX ix_stone_types_name ON public.stone_types USING btree (name);
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_types" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."user_roles" ADD FOREIGN KEY ("role_id") REFERENCES "public"."roles"("id");


-- Indices
CREATE UNIQUE INDEX ix_business_jobs_job_number ON public.business_jobs USING btree (job_number);
CREATE INDEX ix_business_jobs_name ON public.business_jobs USING btree (name);
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("account_id") REFERENCES "public"."accounts"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."business_jobs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_planning_planning_sections" ADD FOREIGN KEY ("shop_planning_id") REFERENCES "public"."shop_plannings"("id");


-- Indices
CREATE UNIQUE INDEX uq_stone_colors_type_name ON public.stone_colors USING btree (stone_type_id, name);
CREATE INDEX ix_stone_colors_name ON public.stone_colors USING btree (name);
CREATE INDEX ix_stone_colors_stone_type_id ON public.stone_colors USING btree (stone_type_id);
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."stone_colors" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_job_notes_created_by ON public.job_notes USING btree (created_by);
CREATE INDEX ix_job_notes_id ON public.job_notes USING btree (id);
CREATE INDEX ix_job_notes_job_id ON public.job_notes USING btree (job_id);
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."job_notes" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_assigned_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("sales_person_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("redo_department") REFERENCES "public"."departments"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("status_id") REFERENCES "public"."status"("value_id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_type_id") REFERENCES "public"."stone_types"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("edge_id") REFERENCES "public"."edges"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_color_id") REFERENCES "public"."stone_colors"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("drafter_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("stone_thickness_id") REFERENCES "public"."stone_thickness"("id");
ALTER TABLE "public"."fabs" ADD FOREIGN KEY ("cost_of_stone_id") REFERENCES "public"."cost_of_stones"("id");


-- Indices
CREATE UNIQUE INDEX cnc_draftings_fab_id_key ON public.cnc_draftings USING btree (fab_id);
ALTER TABLE "public"."cnc_draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX draftings_fab_id_key ON public.draftings USING btree (fab_id);
ALTER TABLE "public"."draftings" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_fab_notes_fab_id ON public.fab_notes USING btree (fab_id);
CREATE INDEX ix_fab_notes_stage ON public.fab_notes USING btree (stage);
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."fab_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_sessions_fab_id ON public.installer_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_sessions_installer_id ON public.installer_job_timer_sessions USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_sessions_job_id ON public.installer_job_timer_sessions USING btree (job_id);
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_sessions_fab_id ON public.operator_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_sessions_job_id ON public.operator_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_operator_job_timer_sessions_operator_id ON public.operator_job_timer_sessions USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_sessions_workstation_id ON public.operator_job_timer_sessions USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("planning_section_id") REFERENCES "public"."planning_sections"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plans" ADD FOREIGN KEY ("user_id") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_revisions_fab_id ON public.revisions USING btree (fab_id);
ALTER TABLE "public"."revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE UNIQUE INDEX sales_cts_fab_id_key ON public.sales_cts USING btree (fab_id);
ALTER TABLE "public"."sales_cts" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."shop_notes" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_sessions_fab_id ON public.templater_job_timer_sessions USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_sessions_job_id ON public.templater_job_timer_sessions USING btree (job_id);
CREATE INDEX ix_templater_job_timer_sessions_templater_id ON public.templater_job_timer_sessions USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."templater_job_timer_sessions" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");


-- Indices
CREATE INDEX ix_shop_revisions_created_at ON public.shop_revisions USING btree (created_at);
CREATE INDEX ix_shop_revisions_fab_id ON public.shop_revisions USING btree (fab_id);
CREATE INDEX ix_shop_revisions_revision_completed ON public.shop_revisions USING btree (revision_completed);
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("requested_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("assigned_to") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_revisions" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_files_fab_id ON public.files USING btree (fab_id);
CREATE INDEX ix_files_file_design ON public.files USING btree (file_design);
CREATE INDEX ix_files_job_id ON public.files USING btree (job_id);
CREATE INDEX ix_files_stage ON public.files USING btree (stage);
CREATE INDEX ix_files_stage_name ON public.files USING btree (stage_name);
CREATE INDEX ix_files_task_id ON public.files USING btree (task_id);
CREATE INDEX ix_files_uploaded_by ON public.files USING btree (uploaded_by);
ALTER TABLE "public"."files" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("task_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."files" ADD FOREIGN KEY ("uploaded_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_installer_job_timer_events_fab_id ON public.installer_job_timer_events USING btree (fab_id);
CREATE INDEX ix_installer_job_timer_events_installer_id ON public.installer_job_timer_events USING btree (installer_id);
CREATE INDEX ix_installer_job_timer_events_job_id ON public.installer_job_timer_events USING btree (job_id);
CREATE INDEX ix_installer_job_timer_events_session_id ON public.installer_job_timer_events USING btree (session_id);
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."installer_job_timer_sessions"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");


-- Indices
CREATE INDEX ix_operator_job_timer_events_fab_id ON public.operator_job_timer_events USING btree (fab_id);
CREATE INDEX ix_operator_job_timer_events_job_id ON public.operator_job_timer_events USING btree (job_id);
CREATE INDEX ix_operator_job_timer_events_operator_id ON public.operator_job_timer_events USING btree (operator_id);
CREATE INDEX ix_operator_job_timer_events_session_id ON public.operator_job_timer_events USING btree (session_id);
CREATE INDEX ix_operator_job_timer_events_workstation_id ON public.operator_job_timer_events USING btree (workstation_id);
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("workstation_id") REFERENCES "public"."work_stations"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."operator_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."operator_job_timer_sessions"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_sessions" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_templater_job_timer_events_fab_id ON public.templater_job_timer_events USING btree (fab_id);
CREATE INDEX ix_templater_job_timer_events_job_id ON public.templater_job_timer_events USING btree (job_id);
CREATE INDEX ix_templater_job_timer_events_session_id ON public.templater_job_timer_events USING btree (session_id);
CREATE INDEX ix_templater_job_timer_events_templater_id ON public.templater_job_timer_events USING btree (templater_id);
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."templater_job_timer_sessions"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("job_id") REFERENCES "public"."business_jobs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("fab_id") REFERENCES "public"."fabs"("id");
ALTER TABLE "public"."templater_job_timer_events" ADD FOREIGN KEY ("templater_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("shop_cut_plan_id") REFERENCES "public"."shop_cut_plans"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("operator_id") REFERENCES "public"."users"("id");
ALTER TABLE "public"."shop_cut_plan_timer_events" ADD FOREIGN KEY ("session_id") REFERENCES "public"."shop_cut_plan_timer_sessions"("id");


-- Indices
CREATE INDEX ix_slab_smith_sessions_fab_id ON public.slab_smith_sessions USING btree (fab_id);


-- Indices
CREATE INDEX ix_slab_smith_session_notes_session_id ON public.slab_smith_session_notes USING btree (session_id);
CREATE INDEX ix_slab_smith_session_notes_fab_id ON public.slab_smith_session_notes USING btree (fab_id);


-- Indices
CREATE INDEX ix_final_programming_sessions_fab_id ON public.final_programming_sessions USING btree (fab_id);


-- Indices
CREATE UNIQUE INDEX hcp_payroll_source_configs_name_key ON public.hcp_payroll_source_configs USING btree (name);
CREATE INDEX ix_hcp_payroll_source_configs_base_url ON public.hcp_payroll_source_configs USING btree (base_url);
CREATE INDEX ix_hcp_payroll_source_configs_company_id ON public.hcp_payroll_source_configs USING btree (company_id);
CREATE INDEX ix_hcp_payroll_source_configs_is_active ON public.hcp_payroll_source_configs USING btree (is_active);
CREATE INDEX ix_hcp_payroll_source_configs_name ON public.hcp_payroll_source_configs USING btree (name);
CREATE INDEX ix_hcp_payroll_source_configs_report_settings_id ON public.hcp_payroll_source_configs USING btree (report_settings_id);
ALTER TABLE "public"."hcp_payroll_source_configs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."hcp_payroll_source_configs" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_final_programming_session_notes_session_id ON public.final_programming_session_notes USING btree (session_id);
CREATE INDEX ix_final_programming_session_notes_fab_id ON public.final_programming_session_notes USING btree (fab_id);


-- Indices
CREATE INDEX ix_hcp_payroll_ingestion_runs_source_config_id ON public.hcp_payroll_ingestion_runs USING btree (source_config_id);
CREATE INDEX ix_hcp_payroll_ingestion_runs_status ON public.hcp_payroll_ingestion_runs USING btree (status);
ALTER TABLE "public"."hcp_payroll_ingestion_runs" ADD FOREIGN KEY ("source_config_id") REFERENCES "public"."hcp_payroll_source_configs"("id");
ALTER TABLE "public"."hcp_payroll_ingestion_runs" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");


-- Indices
CREATE INDEX ix_hcp_payroll_report_snapshots_source_config_id ON public.hcp_payroll_report_snapshots USING btree (source_config_id);
CREATE INDEX ix_hcp_payroll_report_snapshots_ingestion_run_id ON public.hcp_payroll_report_snapshots USING btree (ingestion_run_id);
CREATE INDEX ix_hcp_payroll_report_snapshots_report_settings_id ON public.hcp_payroll_report_snapshots USING btree (report_settings_id);
ALTER TABLE "public"."hcp_payroll_report_snapshots" ADD FOREIGN KEY ("ingestion_run_id") REFERENCES "public"."hcp_payroll_ingestion_runs"("id");
ALTER TABLE "public"."hcp_payroll_report_snapshots" ADD FOREIGN KEY ("source_config_id") REFERENCES "public"."hcp_payroll_source_configs"("id");


-- Indices
CREATE INDEX ix_hcp_payroll_report_rows_snapshot_id ON public.hcp_payroll_report_rows USING btree (snapshot_id);
CREATE INDEX ix_hcp_payroll_report_rows_source_config_id ON public.hcp_payroll_report_rows USING btree (source_config_id);
CREATE INDEX ix_hcp_payroll_report_rows_ingestion_run_id ON public.hcp_payroll_report_rows USING btree (ingestion_run_id);
CREATE INDEX ix_hcp_payroll_report_rows_row_kind ON public.hcp_payroll_report_rows USING btree (row_kind);
CREATE INDEX ix_hcp_payroll_report_rows_row_index ON public.hcp_payroll_report_rows USING btree (row_index);
CREATE INDEX ix_hcp_payroll_report_rows_cost_center_name ON public.hcp_payroll_report_rows USING btree (cost_center_name);
ALTER TABLE "public"."hcp_payroll_report_rows" ADD FOREIGN KEY ("source_config_id") REFERENCES "public"."hcp_payroll_source_configs"("id");
ALTER TABLE "public"."hcp_payroll_report_rows" ADD FOREIGN KEY ("ingestion_run_id") REFERENCES "public"."hcp_payroll_ingestion_runs"("id");
ALTER TABLE "public"."hcp_payroll_report_rows" ADD FOREIGN KEY ("snapshot_id") REFERENCES "public"."hcp_payroll_report_snapshots"("id");


-- Indices
CREATE INDEX ix_installer_rate_history_installer_id ON public.installer_rate_history USING btree (installer_id);
CREATE INDEX ix_installer_rate_history_effective_from ON public.installer_rate_history USING btree (effective_from);
CREATE INDEX ix_installer_rate_history_effective_to ON public.installer_rate_history USING btree (effective_to);
CREATE INDEX ix_installer_rate_history_is_active ON public.installer_rate_history USING btree (is_active);
ALTER TABLE "public"."installer_rate_history" ADD FOREIGN KEY ("updated_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_rate_history" ADD FOREIGN KEY ("created_by") REFERENCES "public"."users"("id");
ALTER TABLE "public"."installer_rate_history" ADD FOREIGN KEY ("installer_id") REFERENCES "public"."users"("id");
