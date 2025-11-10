CREATE TABLE "users"(
    "id" BIGINT NOT NULL,
    "username" TEXT NOT NULL,
    "employee_id" UUID NOT NULL,
    "phone" VARCHAR(255) NULL,
    "email" VARCHAR(255) NOT NULL,
    "home_address" BIGINT NULL,
    "gender" VARCHAR(255) NULL,
    "profile_image_id" BIGINT NULL,
    "first name" VARCHAR(255) NOT NULL,
    "last name" VARCHAR(255) NOT NULL,
    "department" BIGINT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "status" BIGINT NOT NULL
);
ALTER TABLE
    "users" ADD PRIMARY KEY("id");
ALTER TABLE
    "users" ADD CONSTRAINT "users_username_unique" UNIQUE("username");
CREATE INDEX "users_employee_id_index" ON
    "users"("employee_id");
ALTER TABLE
    "users" ADD CONSTRAINT "users_email_unique" UNIQUE("email");
CREATE INDEX "users_status_index" ON
    "users"("status");
CREATE TABLE "status"(
    "id" BIGINT NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "slug" VARCHAR(255) NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "value_id" BIGINT NOT NULL
);
ALTER TABLE
    "status" ADD PRIMARY KEY("id");
CREATE INDEX "status_value_id_index" ON
    "status"("value_id");
CREATE TABLE "jobs"(
    "id" BIGINT NOT NULL,
    "name" BIGINT NOT NULL,
    "job_id" BIGINT NOT NULL,
    "created_by" BIGINT NOT NULL,
    "updated_by" BIGINT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "status_id" BIGINT NOT NULL,
    "account_id" BIGINT NOT NULL
);
ALTER TABLE
    "jobs" ADD PRIMARY KEY("id");
CREATE INDEX "jobs_job_id_index" ON
    "jobs"("job_id");
CREATE INDEX "jobs_status_id_index" ON
    "jobs"("status_id");
CREATE TABLE "fabs"(
    "id" BIGINT NOT NULL,
    "fab_type" VARCHAR(255) NOT NULL,
    "stone_colour" VARCHAR(255) NOT NULL,
    "stone_thickness" VARCHAR(255) NOT NULL,
    "fab_type" VARCHAR(255) NOT NULL,
    "edges" VARCHAR(255) NOT NULL,
    "input_area" TEXT NOT NULL,
    "totl_sqft" VARCHAR(255) NOT NULL,
    "notes" TEXT NULL,
    "sales_person_id" BIGINT NOT NULL,
    "job_id" BIGINT NOT NULL,
    "template_needed" BOOLEAN NOT NULL,
    "drafting_needed" BOOLEAN NOT NULL,
    "slab_smith_needed_ag" BOOLEAN NOT NULL,
    "slab_smith_needed_cust" BOOLEAN NOT NULL,
    "sct_needed" BOOLEAN NOT NULL DEFAULT '1',
    "final_programming_needed" BOOLEAN NOT NULL,
    "status_id" BIGINT NOT NULL,
    "created_by" BIGINT NOT NULL,
    "updated_by" BIGINT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "curremt_stage" VARCHAR(255) NOT NULL
);
ALTER TABLE
    "fabs" ADD PRIMARY KEY("id");
CREATE INDEX "fabs_fab_type_index" ON
    "fabs"("fab_type");
CREATE INDEX "fabs_totl_sqft_index" ON
    "fabs"("totl_sqft");
COMMENT
ON COLUMN
    "fabs"."curremt_stage" IS 'equivalent to the table name of the process e.g templatings';
CREATE TABLE "stone_types"(
    "id" BIGINT NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "descripition" TEXT NULL,
    "status_id" BIGINT NOT NULL,
    "created_by" BIGINT NOT NULL,
    "updated_by" BIGINT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL
);
ALTER TABLE
    "stone_types" ADD PRIMARY KEY("id");
CREATE INDEX "stone_types_name_index" ON
    "stone_types"("name");
CREATE INDEX "stone_types_status_id_index" ON
    "stone_types"("status_id");
CREATE TABLE "accounts"(
    "id" BIGINT NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "account_id" BIGINT NOT NULL,
    "descripition" TEXT NULL,
    "status_id" BIGINT NOT NULL,
    "created_by" BIGINT NOT NULL,
    "updated_by" BIGINT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "status_id" BIGINT NOT NULL
);
ALTER TABLE
    "accounts" ADD PRIMARY KEY("id");
CREATE INDEX "accounts_name_index" ON
    "accounts"("name");
CREATE INDEX "accounts_account_id_index" ON
    "accounts"("account_id");
CREATE INDEX "accounts_status_id_index" ON
    "accounts"("status_id");
CREATE TABLE "templatings"(
    "id" BIGINT NOT NULL,
    "fab_id" BIGINT NOT NULL,
    "is_templating_schedule" BOOLEAN NOT NULL DEFAULT '0',
    "is_templating_received" BOOLEAN NOT NULL DEFAULT '0',
    "schedule_start_date" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "technician_id" BIGINT NULL,
    "schedule_due_date" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "total_sqft" VARCHAR(255) NULL,
    "technician_start_date" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "technician_end_date" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "status_id" BIGINT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "updated_by" BIGINT NOT NULL
);
ALTER TABLE
    "templatings" ADD PRIMARY KEY("id");
CREATE TABLE "draftings"(
    "id" BIGINT NOT NULL,
    "drafter_id" BIGINT NOT NULL,
    "fab_id" BIGINT NOT NULL,
    "scheduled_start_date" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "scheduled_end_date" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "drafter_start_date" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "drafter_end_date" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "status_id" BIGINT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "updated_by" BIGINT NULL,
    "file_ids" TEXT NULL,
    "no_of_piece_drafted" VARCHAR(255) NULL,
    "total_sqft_required_to_draft" VARCHAR(255) NOT NULL,
    "total_sqft_drafted" VARCHAR(255) NULL,
    "draft_note" VARCHAR(255) NULL,
    "mentions" TEXT NULL,
    "is_redrafting" BOOLEAN NOT NULL DEFAULT '0'
);
ALTER TABLE
    "draftings" ADD PRIMARY KEY("id");
COMMENT
ON COLUMN
    "draftings"."file_ids" IS 'stores a list of differrent file id that belongs to this drafting, each pointing to a file on the files table';
COMMENT
ON COLUMN
    "draftings"."mentions" IS 'List of user_ids of user to be notified of the draft submission';
CREATE TABLE "pre_draft_reviews"(
    "id" BIGINT NOT NULL,
    "fab_id" BIGINT NOT NULL,
    "draft_notes" BIGINT NOT NULL,
    "is_redrafting_needed" BIGINT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_by" BIGINT NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "status_id" BIGINT NULL
);
ALTER TABLE
    "pre_draft_reviews" ADD PRIMARY KEY("id");
CREATE TABLE "sales_cts"(
    "id" BIGINT NOT NULL,
    "fab_id" BIGINT NOT NULL,
    "is_revision_needed" BOOLEAN NOT NULL,
    "is_revision_completed" BOOLEAN NULL,
    "status_id" BIGINT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "updated_by" BIGINT NULL,
    "no_of_revisions" VARCHAR(255) NULL,
    "current_revision_count" VARCHAR(255) NULL
);
ALTER TABLE
    "sales_cts" ADD PRIMARY KEY("id");
CREATE INDEX "sales_cts_status_id_index" ON
    "sales_cts"("status_id");
CREATE TABLE "sct_revision_queue"(
    "id" BIGINT NOT NULL,
    "sales_cts_id" BIGINT NOT NULL,
    "revision_type" VARCHAR(255) NOT NULL,
    "status_id" BIGINT NOT NULL,
    "draftings_id" BIGINT NOT NULL,
    "file_ids" TEXT NULL,
    "revision_number" INTEGER NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "start_date" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "end_date" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "updated_by" BIGINT NULL,
    "revision_reason" TEXT NOT NULL
);
ALTER TABLE
    "sct_revision_queue" ADD PRIMARY KEY("id");
COMMENT
ON COLUMN
    "sct_revision_queue"."file_ids" IS 'files added by the sales persion for this current revision';
CREATE TABLE "slab_smiths"(
    "id" BIGINT NOT NULL,
    "fab_id" BIGINT NOT NULL,
    "slab_smith_type" VARCHAR(255) NOT NULL,
    "drafter_id" BIGINT NOT NULL,
    "status_id" BIGINT NOT NULL,
    "start_date" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "end_date" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "total_sqft_completed" VARCHAR(255) NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "updated_by" BIGINT NULL,
    "file_ids" TEXT NULL
);
ALTER TABLE
    "slab_smiths" ADD PRIMARY KEY("id");
COMMENT
ON COLUMN
    "slab_smiths"."file_ids" IS 'stores a list of differrent file id that belongs to this drafting, each pointing to a file on the files table';
CREATE TABLE "cut_list"(
    "id" BIGINT NOT NULL,
    "fab_id" BIGINT NOT NULL,
    "is_final_progreamming_completed" BOOLEAN NOT NULL DEFAULT '0',
    "shop_schedule_date" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "status_id" BIGINT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "updated_by" BIGINT NULL,
    "no_of_piece" VARCHAR(255) NULL,
    "total_sqft" VARCHAR(255) NULL,
    "installation_date" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "Ln_ft_map" TEXT NULL
);
ALTER TABLE
    "cut_list" ADD PRIMARY KEY("id");
COMMENT
ON COLUMN
    "cut_list"."Ln_ft_map" IS 'contains the map of key value pair of Lnft e.g water jet Ln ft and so on';
CREATE TABLE "job_technician_workflows"(
    "id" BIGINT NOT NULL,
    "fab_id" BIGINT NOT NULL,
    "technician_id" BIGINT NOT NULL,
    "table_name" VARCHAR(255) NOT NULL,
    "notes" VARCHAR(255) NULL,
    "pause_reason" TEXT NULL,
    "total_sqft_done" VARCHAR(255) NOT NULL,
    "started_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "completed_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "table_id" BIGINT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "created_by" BIGINT NOT NULL
);
ALTER TABLE
    "job_technician_workflows" ADD PRIMARY KEY("id");
CREATE INDEX "job_technician_workflows_table_name_index" ON
    "job_technician_workflows"("table_name");
CREATE INDEX "job_technician_workflows_table_id_index" ON
    "job_technician_workflows"("table_id");
COMMENT
ON COLUMN
    "job_technician_workflows"."table_name" IS 'templating';
COMMENT
ON COLUMN
    "job_technician_workflows"."completed_at" IS 'this is is when workflow finished , it may be that the only fabid was puase or the  section was done';
COMMENT
ON COLUMN
    "job_technician_workflows"."table_id" IS 'related to the id for the table_name';
CREATE TABLE "final_programmings"(
    "id" BIGINT NOT NULL,
    "drafter_id" BIGINT NOT NULL,
    "fab_id" BIGINT NOT NULL,
    "scheduled_start_date" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "scheduled_end_date" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "drafter_start_date" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "drafter_end_date" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "status_id" BIGINT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "updated_by" BIGINT NULL,
    "file_ids" TEXT NULL,
    "no_of_piece_drafted" VARCHAR(255) NULL,
    "total_sqft_required_to_draft" VARCHAR(255) NOT NULL,
    "total_sqft_drafted" VARCHAR(255) NULL,
    "notes" VARCHAR(255) NULL
);
ALTER TABLE
    "final_programmings" ADD PRIMARY KEY("id");
COMMENT
ON COLUMN
    "final_programmings"."file_ids" IS 'stores a list of differrent file id that belongs to this drafting, each pointing to a file on the files table';
ALTER TABLE
    "job_technician_workflows" ADD CONSTRAINT "job_technician_workflows_fab_id_foreign" FOREIGN KEY("fab_id") REFERENCES "fabs"("id");
ALTER TABLE
    "slab_smiths" ADD CONSTRAINT "slab_smiths_status_id_foreign" FOREIGN KEY("status_id") REFERENCES "status"("id");
ALTER TABLE
    "pre_draft_reviews" ADD CONSTRAINT "pre_draft_reviews_status_id_foreign" FOREIGN KEY("status_id") REFERENCES "status"("id");
ALTER TABLE
    "draftings" ADD CONSTRAINT "draftings_drafter_id_foreign" FOREIGN KEY("drafter_id") REFERENCES "users"("id");
ALTER TABLE
    "fabs" ADD CONSTRAINT "fabs_updated_by_foreign" FOREIGN KEY("updated_by") REFERENCES "users"("id");
ALTER TABLE
    "jobs" ADD CONSTRAINT "jobs_updated_by_foreign" FOREIGN KEY("updated_by") REFERENCES "users"("id");
ALTER TABLE
    "jobs" ADD CONSTRAINT "jobs_created_by_foreign" FOREIGN KEY("created_by") REFERENCES "users"("id");
ALTER TABLE
    "final_programmings" ADD CONSTRAINT "final_programmings_status_id_foreign" FOREIGN KEY("status_id") REFERENCES "status"("id");
ALTER TABLE
    "templatings" ADD CONSTRAINT "templatings_status_id_foreign" FOREIGN KEY("status_id") REFERENCES "users"("id");
ALTER TABLE
    "pre_draft_reviews" ADD CONSTRAINT "pre_draft_reviews_updated_by_foreign" FOREIGN KEY("updated_by") REFERENCES "users"("id");
ALTER TABLE
    "job_technician_workflows" ADD CONSTRAINT "job_technician_workflows_technician_id_foreign" FOREIGN KEY("technician_id") REFERENCES "users"("id");
ALTER TABLE
    "job_technician_workflows" ADD CONSTRAINT "job_technician_workflows_created_by_foreign" FOREIGN KEY("created_by") REFERENCES "users"("id");
ALTER TABLE
    "draftings" ADD CONSTRAINT "draftings_status_id_foreign" FOREIGN KEY("status_id") REFERENCES "status"("id");
ALTER TABLE
    "sct_revision_queue" ADD CONSTRAINT "sct_revision_queue_draftings_id_foreign" FOREIGN KEY("draftings_id") REFERENCES "final_programmings"("id");
ALTER TABLE
    "draftings" ADD CONSTRAINT "draftings_fab_id_foreign" FOREIGN KEY("fab_id") REFERENCES "fabs"("id");
ALTER TABLE
    "templatings" ADD CONSTRAINT "templatings_technician_id_foreign" FOREIGN KEY("technician_id") REFERENCES "users"("id");
ALTER TABLE
    "cut_list" ADD CONSTRAINT "cut_list_fab_id_foreign" FOREIGN KEY("fab_id") REFERENCES "fabs"("id");
ALTER TABLE
    "sct_revision_queue" ADD CONSTRAINT "sct_revision_queue_draftings_id_foreign" FOREIGN KEY("draftings_id") REFERENCES "draftings"("id");
ALTER TABLE
    "final_programmings" ADD CONSTRAINT "final_programmings_drafter_id_foreign" FOREIGN KEY("drafter_id") REFERENCES "users"("id");
ALTER TABLE
    "templatings" ADD CONSTRAINT "templatings_fab_id_foreign" FOREIGN KEY("fab_id") REFERENCES "fabs"("id");
ALTER TABLE
    "draftings" ADD CONSTRAINT "draftings_updated_by_foreign" FOREIGN KEY("updated_by") REFERENCES "users"("id");
ALTER TABLE
    "templatings" ADD CONSTRAINT "templatings_updated_by_foreign" FOREIGN KEY("updated_by") REFERENCES "users"("id");
ALTER TABLE
    "fabs" ADD CONSTRAINT "fabs_sales_person_id_foreign" FOREIGN KEY("sales_person_id") REFERENCES "users"("id");
ALTER TABLE
    "cut_list" ADD CONSTRAINT "cut_list_status_id_foreign" FOREIGN KEY("status_id") REFERENCES "status"("id");
ALTER TABLE
    "slab_smiths" ADD CONSTRAINT "slab_smiths_drafter_id_foreign" FOREIGN KEY("drafter_id") REFERENCES "users"("id");
ALTER TABLE
    "sales_cts" ADD CONSTRAINT "sales_cts_updated_by_foreign" FOREIGN KEY("updated_by") REFERENCES "users"("id");
ALTER TABLE
    "sales_cts" ADD CONSTRAINT "sales_cts_fab_id_foreign" FOREIGN KEY("fab_id") REFERENCES "fabs"("id");
ALTER TABLE
    "fabs" ADD CONSTRAINT "fabs_created_by_foreign" FOREIGN KEY("created_by") REFERENCES "users"("id");
ALTER TABLE
    "templatings" ADD CONSTRAINT "templatings_status_id_foreign" FOREIGN KEY("status_id") REFERENCES "status"("id");
ALTER TABLE
    "jobs" ADD CONSTRAINT "jobs_status_id_foreign" FOREIGN KEY("status_id") REFERENCES "status"("id");
ALTER TABLE
    "jobs" ADD CONSTRAINT "jobs_account_id_foreign" FOREIGN KEY("account_id") REFERENCES "accounts"("id");
ALTER TABLE
    "final_programmings" ADD CONSTRAINT "final_programmings_fab_id_foreign" FOREIGN KEY("fab_id") REFERENCES "fabs"("id");
ALTER TABLE
    "sct_revision_queue" ADD CONSTRAINT "sct_revision_queue_status_id_foreign" FOREIGN KEY("status_id") REFERENCES "status"("id");
ALTER TABLE
    "fabs" ADD CONSTRAINT "fabs_job_id_foreign" FOREIGN KEY("job_id") REFERENCES "jobs"("id");
ALTER TABLE
    "final_programmings" ADD CONSTRAINT "final_programmings_updated_by_foreign" FOREIGN KEY("updated_by") REFERENCES "users"("id");
ALTER TABLE
    "cut_list" ADD CONSTRAINT "cut_list_updated_by_foreign" FOREIGN KEY("updated_by") REFERENCES "users"("id");
ALTER TABLE
    "slab_smiths" ADD CONSTRAINT "slab_smiths_fab_id_foreign" FOREIGN KEY("fab_id") REFERENCES "fabs"("id");
ALTER TABLE
    "sct_revision_queue" ADD CONSTRAINT "sct_revision_queue_updated_by_foreign" FOREIGN KEY("updated_by") REFERENCES "users"("id");
ALTER TABLE
    "fabs" ADD CONSTRAINT "fabs_status_id_foreign" FOREIGN KEY("status_id") REFERENCES "status"("id");
ALTER TABLE
    "sct_revision_queue" ADD CONSTRAINT "sct_revision_queue_sales_cts_id_foreign" FOREIGN KEY("sales_cts_id") REFERENCES "sales_cts"("id");
ALTER TABLE
    "users" ADD CONSTRAINT "users_status_foreign" FOREIGN KEY("status") REFERENCES "status"("value_id");
ALTER TABLE
    "sales_cts" ADD CONSTRAINT "sales_cts_status_id_foreign" FOREIGN KEY("status_id") REFERENCES "status"("id");