CREATE TABLE "work_stations"(
    "id" BIGINT NOT NULL,
    "name" VARCHAR(255) NOT NULL,
    "planning_sections_id" BIGINT NOT NULL,
    "status_id" BIGINT NOT NULL,
    "operatives_ids" TEXT NOT NULL,
    "machine_list" TEXT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "created_by" BIGINT NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "updated_by" BIGINT NULL
);
ALTER TABLE
    "work_stations" ADD PRIMARY KEY("id");
ALTER TABLE
    "work_stations" ADD CONSTRAINT "work_stations_name_unique" UNIQUE("name");
COMMENT
ON COLUMN
    "work_stations"."status_id" IS 'link to the status table';
COMMENT
ON COLUMN
    "work_stations"."operatives_ids" IS 'list of user ids of operative, each user id will link to the status table';
COMMENT
ON COLUMN
    "work_stations"."machine_list" IS 'List of machines, available for this works station';
COMMENT
ON COLUMN
    "work_stations"."created_by" IS 'link to the users table';
COMMENT
ON COLUMN
    "work_stations"."updated_by" IS 'link to the users table';
CREATE TABLE "planning_sections"(
    "id" BIGINT NOT NULL,
    "plan_name" VARCHAR(255) NOT NULL,
    "plan_description" TEXT NULL,
    "status_id" BIGINT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "created_by" BIGINT NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "updated_by" BIGINT NULL
);
ALTER TABLE
    "planning_sections" ADD PRIMARY KEY("id");
ALTER TABLE
    "planning_sections" ADD CONSTRAINT "planning_sections_plan_name_unique" UNIQUE("plan_name");
COMMENT
ON COLUMN
    "planning_sections"."status_id" IS 'relate to the status table';
COMMENT
ON COLUMN
    "planning_sections"."created_by" IS 'relate to the users table';
COMMENT
ON COLUMN
    "planning_sections"."updated_by" IS 'relate to the users table';
CREATE TABLE "shop_planning_planning_sections"(
    "id" BIGINT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "created_by" BIGINT NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "updated_by" BIGINT NULL,
    "shop_planning_id" BIGINT NOT NULL,
    "planning_section_id" BIGINT NOT NULL,
    "order" INTEGER NOT NULL
);
ALTER TABLE
    "shop_planning_planning_sections" ADD PRIMARY KEY("id");
COMMENT
ON COLUMN
    "shop_planning_planning_sections"."created_by" IS 'relate to the users table';
COMMENT
ON COLUMN
    "shop_planning_planning_sections"."updated_by" IS 'relate to the users table';
COMMENT
ON COLUMN
    "shop_planning_planning_sections"."order" IS 'what step or when will this planning section be run relative to the order planning section';
CREATE TABLE "shop_plannings"(
    "id" BIGINT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "created_by" BIGINT NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "updated_by" BIGINT NULL,
    "fab_id" BIGINT NOT NULL,
    "start_date" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "no_of_steps_needed" INTEGER NOT NULL,
    "status_id" BIGINT NOT NULL,
    "completed_steps" INTEGER NOT NULL,
    "current_steps" BIGINT NOT NULL
);
ALTER TABLE
    "shop_plannings" ADD PRIMARY KEY("id");
COMMENT
ON COLUMN
    "shop_plannings"."created_by" IS 'relate to the users table';
COMMENT
ON COLUMN
    "shop_plannings"."updated_by" IS 'relate to the users table';
COMMENT
ON COLUMN
    "shop_plannings"."no_of_steps_needed" IS 'equal no of shop_planning_planning_sections need for the shop planning';
COMMENT
ON COLUMN
    "shop_plannings"."status_id" IS 'link to the status table';
CREATE TABLE "shop_planning_sections"(
    "id" BIGINT NOT NULL,
    "shop_planning_planning_section_id" BIGINT NOT NULL,
    "work_station_id" BIGINT NOT NULL,
    "operator_ids" BIGINT NOT NULL,
    "order_no" BIGINT NOT NULL,
    "machine" VARCHAR(255) NOT NULL,
    "notes" TEXT NULL,
    "scheduled_duration_minuteslink to the status table" VARCHAR(255) NOT NULL,
    "required_sft" VARCHAR(255) NOT NULL,
    "completed_sqft" VARCHAR(255) NULL,
    "no of pirces" VARCHAR(255) NULL,
    "operator_duration" VARCHAR(255) NULL,
    "start_date" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "end_date" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "updated_by" BIGINT NULL,
    "status_id" BIGINT NOT NULL
);
ALTER TABLE
    "shop_planning_sections" ADD PRIMARY KEY("id");
COMMENT
ON COLUMN
    "shop_planning_sections"."operator_ids" IS 'list of operator needed for this section
each of their ids is related or link to the users table';
COMMENT
ON COLUMN
    "shop_planning_sections"."order_no" IS 'this is how to determine if this section is the first to run for the shop planning section or the second and so on';
COMMENT
ON COLUMN
    "shop_planning_sections"."machine" IS 'only list machines with status as active';
COMMENT
ON COLUMN
    "shop_planning_sections"."operator_duration" IS 'how long the task really take the operator';
COMMENT
ON COLUMN
    "shop_planning_sections"."updated_by" IS 'link to the users table';
COMMENT
ON COLUMN
    "shop_planning_sections"."status_id" IS 'link to the status table';
CREATE TABLE "operation_workflow"(
    "id" BIGINT NOT NULL,
    "shop_planning_sections" BIGINT NOT NULL,
    "started_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "finished_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "totl_sqt_done" VARCHAR(255) NOT NULL,
    "reason_for_pause" TEXT NOT NULL,
    "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL,
    "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NULL,
    "updated_by" BIGINT NULL,
    "notes" VARCHAR(255) NULL
);
ALTER TABLE
    "operation_workflow" ADD PRIMARY KEY("id");
COMMENT
ON COLUMN
    "operation_workflow"."finished_at" IS 'This can be a pause or completion';
ALTER TABLE
    "shop_planning_planning_sections" ADD CONSTRAINT "shop_planning_planning_sections_shop_planning_id_foreign" FOREIGN KEY("shop_planning_id") REFERENCES "shop_plannings"("id");
ALTER TABLE
    "shop_planning_planning_sections" ADD CONSTRAINT "shop_planning_planning_sections_planning_section_id_foreign" FOREIGN KEY("planning_section_id") REFERENCES "planning_sections"("id");
ALTER TABLE
    "shop_planning_sections" ADD CONSTRAINT "shop_planning_sections_shop_planning_planning_section_id_foreign" FOREIGN KEY(
        "shop_planning_planning_section_id"
    ) REFERENCES "shop_planning_planning_sections"("id");
ALTER TABLE
    "work_stations" ADD CONSTRAINT "work_stations_planning_sections_id_foreign" FOREIGN KEY("planning_sections_id") REFERENCES "planning_sections"("id");
ALTER TABLE
    "operation_workflow" ADD CONSTRAINT "operation_workflow_shop_planning_sections_foreign" FOREIGN KEY("shop_planning_sections") REFERENCES "shop_planning_sections"("id");