# MIGRATION_SPEC.md

## 1. Project summary

- Project root scanned: `/Users/segun/Desktop/Protech/alpha_granit_backend`
- Python version: 3.10.11 (venv)
- FastAPI version: **(UNCERTAIN)** not pinned in `requirements.txt` (will install latest available on `pip install fastapi` – likely >=0.111 at migration time). Pin recommended (e.g. `fastapi==0.110.3`).
- Framework & ORM usage: FastAPI + SQLModel + raw SQLAlchemy (AsyncSession) + Alembic for migrations. Mixed sync/async patterns (AsyncSession plus some pure SQLModel Session usage). Missing `greenlet` in requirements (async/sync bridging risk).
- High-level migration plan (summary):
  1. Inventory all models & endpoints (this document).
  2. Translate SQLModel/SQLAlchemy models into Django ORM models.
  3. Implement DRF serializers + ViewSets / APIViews mapped per endpoint cluster.
  4. Recreate auth & permission layer (JWT, role/action_menu/permission matrix) with DRF custom permissions.
  5. Port business services (templating, drafting, role/action menu management) into Django service modules or domain services.
  6. Rebuild tests (pytest -> Django test runner + `pytest-django`).
  7. Replace FastAPI deployment (uvicorn) with Django ASGI (uvicorn/gunicorn) setup.

---

## 2. Endpoints index

Alphabetically by path (merged across routers). `Auth required` inferred by presence of `Depends(get_current_user)` or `PermissionChecker(...)`. Endpoints without explicit auth dependency may still be protected by global middleware — mark as **Maybe**. Response and request models pulled from decorators; when wrapper `SuccessResponse[...]` used, inner model listed.

| Method     | Path                                      | Router File              | Handler                            | Auth Required                           | Response Model                                | Request Model(s)                                    | Notes                                                         |
| ---------- | ----------------------------------------- | ------------------------ | ---------------------------------- | --------------------------------------- | --------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------- |
| GET        | /                                         | health.py                | health_check                       | No                                      | SuccessResponse(dict)                         | None                                                | Basic health; potential collision at root.                    |
| GET        | /db                                       | health.py                | database_health                    | No                                      | SuccessResponse(dict)                         | None                                                | DB connectivity check.                                        |
| POST       | /accounts                                 | accounts.py              | create_account                     | Yes (PermissionChecker accounts:create) | SuccessResponse(AccountResponse)              | AccountCreate                                       | Uniqueness checks (name, number).                             |
| GET        | /accounts                                 | accounts.py              | get_accounts                       | Yes (accounts:read)                     | SuccessResponse(List[AccountResponse])        | Query params: skip, limit, status_id, search        | Pagination + search.                                          |
| GET        | /accounts/{account_id}                    | accounts.py              | get_account                        | Yes (get_current_user)                  | SuccessResponse(AccountResponse)              | Path: account_id                                    | 404 if not found.                                             |
| PUT        | /accounts/{account_id}                    | accounts.py              | update_account                     | Yes                                     | SuccessResponse(AccountResponse)              | AccountUpdate                                       | Uniqueness re-checks.                                         |
| DELETE     | /accounts/{account_id}                    | accounts.py              | delete_account                     | Yes                                     | SuccessResponse(None)                         | Path: account_id                                    | Hard delete (despite doc string).                             |
| POST       | /action-menus                             | action_menu.py           | create_action_menu                 | Yes (action_menus:create)               | SuccessResponse(ActionMenuResponse)           | ActionMenuCreate                                    | Creates menu + unique code.                                   |
| GET        | /action-menus                             | action_menu.py           | get_all_action_menus               | Yes (get_current_user)                  | SuccessResponse(List[ActionMenuResponse])     | None                                                | Lists all action menus.                                       |
| GET        | /action-menus/{action_menu_id}            | action_menu.py           | get_action_menu                    | Yes (action_menus:read)                 | SuccessResponse(ActionMenuResponse)           | Path: action_menu_id                                | --                                                            |
| PUT        | /action-menus/{action_menu_id}            | action_menu.py           | update_action_menu                 | Yes (action_menus:update)               | SuccessResponse(ActionMenuResponse)           | ActionMenuUpdate                                    | --                                                            |
| DELETE     | /action-menus/{action_menu_id}            | action_menu.py           | delete_action_menu                 | Yes (action_menus:delete)               | SuccessResponse(None)                         | Path: action_menu_id                                | Fails if in use.                                              |
| POST       | /auth/login                               | auth.py                  | login                              | No                                      | SuccessResponse(Token/Permissions payload)    | LoginRequest                                        | Complex audit + device headers.                               |
| POST       | /auth/refresh-token                       | auth.py                  | refresh_token                      | No                                      | SuccessResponse(TokenSchema)                  | RefreshTokenRequest                                 | Validates refresh token type.                                 |
| POST       | /auth/change-password                     | auth.py                  | change_password                    | Yes                                     | SuccessResponse(None)                         | PasswordChangeRequest                               | Audit + notification side-effects.                            |
| POST       | /auth/request-password-reset              | auth.py                  | request_password_reset             | **(UNCERTAIN)**                         | **(UNCERTAIN)**                               | PasswordResetRequest                                | Not fully scanned.                                            |
| POST       | /auth/confirm-password-reset              | auth.py                  | confirm_password_reset             | **(UNCERTAIN)**                         | SuccessResponse(None)                         | PasswordResetConfirm                                | Not fully scanned.                                            |
| GET        | /auth/profile                             | auth.py                  | get_profile                        | **(UNCERTAIN)**                         | SuccessResponse(UserResponse)                 | None                                                | Standard profile fetch.                                       |
| PUT        | /auth/profile                             | auth.py                  | update_profile                     | **(UNCERTAIN)**                         | SuccessResponse(UserResponse)                 | UserProfileUpdate                                   | Profile update.                                               |
| POST       | /edges                                    | edges.py                 | create_edge                        | Yes                                     | SuccessResponse(EdgeResponse)                 | EdgeCreate                                          | Uniqueness name.                                              |
| GET        | /edges                                    | edges.py                 | get_edges                          | Yes                                     | SuccessResponse(List[EdgeResponse])           | Query: skip, limit, status_id, edge_type, search    | Filtering & pagination.                                       |
| GET        | /edges/{edge_id}                          | edges.py                 | get_edge                           | Yes                                     | SuccessResponse(EdgeResponse)                 | Path: edge_id                                       | 404 if not found.                                             |
| PUT        | /edges/{edge_id}                          | edges.py                 | update_edge                        | Yes                                     | SuccessResponse(EdgeResponse)                 | EdgeUpdate                                          | Status FK validation.                                         |
| DELETE     | /edges/{edge_id}                          | edges.py                 | delete_edge                        | No (missing current_user)               | SuccessResponse(None)                         | Path: edge_id                                       | Hard delete; potential auth oversight.                        |
| POST       | /fabs                                     | fabs.py                  | create_fab                         | Yes                                     | FabResponse                                   | FabCreate                                           | Multi FK validations.                                         |
| GET        | /fabs                                     | fabs.py                  | get_fabs                           | Yes                                     | List[FabResponse]                             | Query filters                                       | Filtering & pagination.                                       |
| GET        | /fabs/{fab_id}                            | fabs.py                  | get_fab                            | Yes                                     | FabResponse                                   | Path: fab_id                                        | --                                                            |
| PUT        | /fabs/{fab_id}                            | fabs.py                  | update_fab                         | Yes                                     | FabResponse                                   | FabUpdate                                           | FK validations when updating.                                 |
| DELETE     | /fabs/{fab_id}                            | fabs.py                  | delete_fab                         | Yes                                     | None (204)                                    | Path: fab_id                                        | Soft delete via status change.                                |
| GET        | /fab-types                                | fab_types.py             | get_fab_types                      | Yes                                     | List[FabTypeResponse]                         | None                                                | Static list; consider caching.                                |
| POST       | /files/upload                             | file.py                  | upload_file                        | Yes                                     | SuccessResponse(FileMetadata)                 | Multipart form + UploadFile                         | Size & extension validation; streaming chunks.                |
| GET        | /files/{file_id}                          | file.py                  | get_file                           | Yes                                     | SuccessResponse(FileMetadata)                 | Path: file_id                                       | --                                                            |
| DELETE     | /files/{file_id}                          | file.py                  | delete_file                        | Yes                                     | SuccessResponse(None)                         | Path: file_id                                       | Removes FS + DB metadata.                                     |
| GET        | /jobs                                     | jobs.py                  | get_jobs                           | Yes (jobs:read)                         | List[JobResponse]                             | Query: skip, limit, account_id, status_id, priority | Pagination + filtering.                                       |
| POST       | /jobs                                     | jobs.py                  | create_job                         | Yes (jobs:create)                       | JobResponse                                   | JobCreate                                           | Uniqueness job_number; account FK.                            |
| GET        | /jobs/{job_id}                            | jobs.py                  | get_job                            | Yes                                     | JobResponse                                   | Path: job_id                                        | --                                                            |
| PUT        | /jobs/{job_id}                            | jobs.py                  | update_job                         | Yes                                     | JobResponse                                   | JobUpdate                                           | Conditional uniqueness & FK checks.                           |
| DELETE     | /jobs/{job_id}                            | jobs.py                  | delete_job                         | Yes                                     | None (204)                                    | Path: job_id                                        | Soft delete via status_id=3.                                  |
| GET        | /jobs/{job_id}/fabs                       | fabs.py                  | get_fabs_by_job                    | Yes                                     | List[FabResponse]                             | Path: job_id + pagination                           | Cross-resource by FK.                                         |
| GET        | /jobs-with-fabs                           | job_extras.py            | list_jobs_with_fabs                | No (no auth dependency)                 | SuccessResponse(list)                         | Query search, account_id                            | Aggregates jobs + related fabs.                               |
| POST       | /operator-workflow                        | operator_workflow.py     | create_operator_workflow           | No (no auth dependency)                 | SuccessResponse(OperationWorkflow)            | Form fields                                         | Consider auth enforcement.                                    |
| PUT        | /operator-workflow/{workflow_id}          | operator_workflow.py     | update_operator_workflow           | No                                      | SuccessResponse(OperationWorkflow)            | Form                                                | --                                                            |
| DELETE     | /operator-workflow/{workflow_id}          | operator_workflow.py     | delete_operator_workflow           | No                                      | SuccessResponse(None)                         | Path                                                | --                                                            |
| GET        | /operator-workflow/{workflow_id}          | operator_workflow.py     | get_operator_workflow              | No                                      | SuccessResponse(OperationWorkflow)            | Path                                                | --                                                            |
| GET        | /operator-workflow                        | operator_workflow.py     | list_operator_workflows            | No                                      | SuccessResponse(List[OperationWorkflow])      | Query shop_planning_sections                        | Filtering.                                                    |
| POST       | /permissions                              | action_menu.py           | create_permission                  | Yes (permissions:create)                | SuccessResponse(PermissionResponse)           | PermissionCreate                                    | CRUD flags.                                                   |
| GET        | /permissions                              | action_menu.py           | get_all_permissions                | Yes                                     | SuccessResponse(List[PermissionResponse])     | None                                                | --                                                            |
| GET        | /permissions/{permission_id}              | action_menu.py           | get_permission                     | Yes (permissions:read)                  | SuccessResponse(PermissionResponse)           | Path                                                | --                                                            |
| PUT        | /permissions/{permission_id}              | action_menu.py           | update_permission                  | Yes (permissions:update)                | SuccessResponse(PermissionResponse)           | PermissionUpdate                                    | --                                                            |
| DELETE     | /permissions/{permission_id}              | action_menu.py           | delete_permission                  | Yes (permissions:delete)                | SuccessResponse(None)                         | Path                                                | Fails if in use.                                              |
| POST       | /planning-section                         | planning_section.py      | create_planning_section            | No                                      | SuccessResponse(PlanningSection)              | Form fields                                         | Uniqueness plan_name; lacks auth.                             |
| PUT        | /planning-section/{section_id}            | planning_section.py      | update_planning_section            | No                                      | SuccessResponse(PlanningSection)              | Form                                                | --                                                            |
| DELETE     | /planning-section/{section_id}            | planning_section.py      | delete_planning_section            | No                                      | SuccessResponse(None)                         | Path                                                | --                                                            |
| GET        | /planning-section/by-name/{plan_name}     | planning_section.py      | get_planning_section_by_name       | No                                      | SuccessResponse(PlanningSection)              | Path                                                | --                                                            |
| GET        | /planning-section/active                  | planning_section.py      | get_active_planning_sections       | No                                      | SuccessResponse(List[PlanningSection])        | None                                                | --                                                            |
| POST       | /roles                                    | role.py                  | create_role                        | Yes (roles:create)                      | SuccessResponse(RoleWithPermissions)          | RoleCreate                                          | Cascade creation of permissions links.                        |
| GET        | /roles                                    | role.py                  | get_roles                          | Yes (roles:read)                        | SuccessResponse(RoleListResponse or stats)    | Query filters                                       | Optional member stats.                                        |
| GET        | /roles/check-name/{name}                  | role.py                  | check_role_name_unique             | Yes                                     | SuccessResponse({unique})                     | Path                                                | Name availability.                                            |
| GET        | /roles/{role_id}                          | role.py                  | get_role                           | Yes (roles:read)                        | SuccessResponse(RoleWithMembers/Permissions)  | Query toggles                                       | Composite response.                                           |
| PUT        | /roles/{role_id}                          | role.py                  | update_role                        | Yes (roles:update)                      | SuccessResponse(RoleResponse)                 | RoleUpdate                                          | Updates permission set.                                       |
| PATCH      | /roles/{role_id}/status                   | role.py                  | update_role_status                 | Yes (roles:update)                      | SuccessResponse(RoleResponse)                 | RoleStatusUpdate                                    | Status transitions.                                           |
| DELETE     | /roles/{role_id}                          | role.py                  | delete_role                        | Yes (roles:delete)                      | SuccessResponse(None)                         | Path                                                | Soft delete via status=3.                                     |
| GET        | /roles/{role_id}/members                  | role.py                  | get_role_with_members              | Yes (roles:read)                        | SuccessResponse(RoleMembersResponse)          | Query pagination & filters                          | Member list.                                                  |
| GET        | /roles/{role_id}/debug-members            | role.py                  | debug_role_members                 | Yes (roles:read)                        | SuccessResponse(debug)                        | Path                                                | Diagnostic only.                                              |
| PATCH      | /roles/users/{user_id}/deactivate         | role.py                  | deactivate_user                    | Yes (roles:update)                      | SuccessResponse(UserStatusUpdate)             | Path                                                | Sets user inactive.                                           |
| POST       | /shop-planning                            | shop_planning.py         | create_shop_planning               | No                                      | SuccessResponse(ShopPlanning)                 | Form                                                | job_id + comma lists.                                         |
| PUT        | /shop-planning/{shop_plan_id}             | shop_planning.py         | update_shop_planning               | No                                      | SuccessResponse(ShopPlanning)                 | Form                                                | State updates.                                                |
| DELETE     | /shop-planning/{shop_plan_id}             | shop_planning.py         | delete_shop_planning               | No                                      | SuccessResponse(None)                         | Path                                                | Hard delete.                                                  |
| GET        | /shop-planning/{shop_plan_id}             | shop_planning.py         | get_shop_planning                  | No                                      | SuccessResponse(ShopPlanning)                 | Path                                                | --                                                            |
| GET        | /shop-planning                            | shop_planning.py         | list_shop_planning                 | No                                      | SuccessResponse(List[ShopPlanning])           | Query job_id, fab_id, search                        | Filtering by string contains.                                 |
| POST       | /shop-planning-section                    | shop_planning_section.py | create_shop_planning_section       | No                                      | SuccessResponse(ShopPlanningSection)          | Form + optional files                               | Multiple ordered comma lists.                                 |
| PUT        | /shop-planning-section/{section_id}       | shop_planning_section.py | update_shop_planning_section       | No                                      | SuccessResponse(ShopPlanningSection)          | Form                                                | Adds new file IDs.                                            |
| DELETE     | /shop-planning-section/{section_id}       | shop_planning_section.py | delete_shop_planning_section       | No                                      | SuccessResponse(None)                         | Path                                                | Hard delete.                                                  |
| GET        | /shop-planning-section/{section_id}       | shop_planning_section.py | get_shop_planning_section          | No                                      | SuccessResponse(ShopPlanningSection)          | Path                                                | --                                                            |
| GET        | /shop-planning-section                    | shop_planning_section.py | list_shop_planning_sections        | No                                      | SuccessResponse(List[ShopPlanningSection])    | Query filters                                       | Contains(...) matching.                                       |
| POST       | /stone-colors                             | stone_colors.py          | create_stone_color                 | Yes                                     | SuccessResponse(StoneColorResponse)           | StoneColorCreate                                    | Uniqueness name.                                              |
| GET        | /stone-colors                             | stone_colors.py          | get_stone_colors                   | Yes                                     | SuccessResponse(List[StoneColorResponse])     | Query skip, limit, status_id, search                | Pagination & search.                                          |
| GET        | /stone-colors/{color_id}                  | stone_colors.py          | get_stone_color                    | Yes                                     | SuccessResponse(StoneColorResponse)           | Path                                                | --                                                            |
| PUT        | /stone-colors/{color_id}                  | stone_colors.py          | update_stone_color                 | Yes                                     | SuccessResponse(StoneColorResponse)           | StoneColorUpdate                                    | Status FK validation.                                         |
| DELETE     | /stone-colors/{color_id}                  | stone_colors.py          | delete_stone_color                 | No (auth missing)                       | SuccessResponse(None)                         | Path                                                | Hard delete.                                                  |
| POST       | /stone-thickness                          | stone_thickness.py       | create_stone_thickness             | Yes (stone_thickness:create)            | SuccessResponse(StoneThicknessResponse)       | StoneThicknessCreate                                | Uniqueness thickness.                                         |
| GET        | /stone-thickness                          | stone_thickness.py       | get_stone_thicknesses              | Yes (stone_thickness:read)              | SuccessResponse(List[StoneThicknessResponse]) | Query skip, limit, status_id                        | Pagination.                                                   |
| GET        | /stone-thickness/{thickness_id}           | stone_thickness.py       | get_stone_thickness                | Yes                                     | SuccessResponse(StoneThicknessResponse)       | Path                                                | --                                                            |
| PUT        | /stone-thickness/{thickness_id}           | stone_thickness.py       | update_stone_thickness             | Yes                                     | SuccessResponse(StoneThicknessResponse)       | StoneThicknessUpdate                                | Status FK validation.                                         |
| DELETE     | /stone-thickness/{thickness_id}           | stone_thickness.py       | delete_stone_thickness             | Yes                                     | SuccessResponse(None)                         | Path                                                | Hard delete; wrapper returns body.                            |
| POST       | /stone-types                              | stone_types.py           | create_stone_type                  | Yes                                     | SuccessResponse(StoneTypeResponse)            | StoneTypeCreate                                     | Uniqueness name.                                              |
| GET        | /stone-types                              | stone_types.py           | get_stone_types                    | Yes                                     | SuccessResponse(List[StoneTypeResponse])      | Query skip, limit, status_id, search                | Pagination & search.                                          |
| GET        | /stone-types/{type_id}                    | stone_types.py           | get_stone_type                     | Yes                                     | SuccessResponse(StoneTypeResponse)            | Path                                                | --                                                            |
| PUT        | /stone-types/{type_id}                    | stone_types.py           | update_stone_type                  | Yes                                     | SuccessResponse(StoneTypeResponse)            | StoneTypeUpdate                                     | Status FK validation.                                         |
| DELETE     | /stone-types/{type_id}                    | stone_types.py           | delete_stone_type                  | Yes                                     | SuccessResponse(None)                         | Path                                                | Hard delete.                                                  |
| POST       | /technician/clock                         | job_extras.py            | save_technician_clock              | No                                      | SuccessResponse(JobTechnicianWorkflow)        | Form                                                | Captures timing data.                                         |
| PUT        | /technician/clock/{workflow_id}           | job_extras.py            | update_technician_clock            | No                                      | SuccessResponse(JobTechnicianWorkflow)        | Form (optional fields)                              | Partial updates.                                              |
| DELETE     | /technician/clock/{workflow_id}           | job_extras.py            | delete_technician_clock            | No                                      | SuccessResponse(None)                         | Path                                                | Hard delete.                                                  |
| GET        | /technician/clockwork                     | job_extras.py            | list_technician_clockwork          | No                                      | SuccessResponse(List[JobTechnicianWorkflow])  | Query filters                                       | Multi param filter.                                           |
| GET        | /technician/clockwork-table-names         | job_extras.py            | get_clockwork_table_names          | No                                      | SuccessResponse(List[str])                    | None                                                | Static names list.                                            |
| POST       | /templating/schedule                      | job_extras.py            | schedule_templating                | No                                      | SuccessResponse(Templating)                   | Form                                                | Service layer call.                                           |
| POST       | /templating/unschedule                    | job_extras.py            | unschedule_templating              | No                                      | SuccessResponse(Templating)                   | Form                                                | Boolean flip.                                                 |
| POST       | /templating/mark-received                 | job_extras.py            | mark_templated_received            | No                                      | SuccessResponse(Templating/Fab)               | Form fab_id                                         | Advances FAB state.                                           |
| POST       | /predraft/complete                        | job_extras.py            | set_predraft_completed             | No                                      | SuccessResponse(Fab/Templating)               | Form                                                | Business workflow.                                            |
| POST       | /predraft/redraft                         | job_extras.py            | set_predraft_redraft               | No                                      | SuccessResponse(Fab+Templating)               | Form                                                | State rollback.                                               |
| POST       | /finalprogramming/{fp_id}/files           | job_extras.py            | add_files_to_final_programming     | No                                      | SuccessResponse({file_ids})                   | Upload multiple                                     | Appends generated IDs.                                        |
| DELETE     | /finalprogramming/{fp_id}/files/{file_id} | job_extras.py            | delete_file_from_final_programming | No                                      | SuccessResponse({file_ids})                   | Path                                                | Removes a pseudo file id.                                     |
| POST       | /finalprogramming/{fp_id}/update          | job_extras.py            | update_final_programming           | No                                      | SuccessResponse(FinalProgramming)             | Form                                                | Partial update.                                               |
| POST       | /cutlist/{cutlist_id}/update-details      | job_extras.py            | update_cutlist_details             | No                                      | SuccessResponse(CutList)                      | Form                                                | Updates numeric fields.                                       |
| POST       | /salesct/{sct_id}/review-no               | job_extras.py            | set_sct_review_no                  | No                                      | SuccessResponse(SalesCT)                      | Form                                                | Sets status flags.                                            |
| POST       | /salesct/{sct_id}/review-yes              | job_extras.py            | set_sct_review_yes                 | No                                      | SuccessResponse(SalesCT)                      | Form + files optional                               | Adds file ids.                                                |
| POST       | /salesct/{sct_id}/revision-update         | job_extras.py            | update_sct_revision                | No                                      | SuccessResponse(SalesCT)                      | Form                                                | Appends revision history.                                     |
| POST       | /slabsmith/{slabsmith_id}/complete        | job_extras.py            | mark_slabsmith_completed           | No                                      | SuccessResponse(SlabSmith)                    | Form                                                | Status completion.                                            |
| POST       | /slabsmith/{slabsmith_id}/files           | job_extras.py            | add_files_to_slabsmith             | No                                      | SuccessResponse({file_ids})                   | Upload files                                        | Append list.                                                  |
| DELETE     | /slabsmith/{slabsmith_id}/files/{file_id} | job_extras.py            | delete_file_from_slabsmith         | No                                      | SuccessResponse({file_ids})                   | Path                                                | Remove file id.                                               |
| POST       | /drafting/{drafting_id}/files             | job_extras.py            | add_files_to_drafting              | No                                      | SuccessResponse({file_ids})                   | Upload files                                        | Append list.                                                  |
| DELETE     | /drafting/{drafting_id}/files/{file_id}   | job_extras.py            | delete_file_from_drafting          | No                                      | SuccessResponse({file_ids})                   | Path                                                | Remove file id.                                               |
| POST       | /drafting/{drafting_id}/submit-review     | job_extras.py            | submit_draft_for_review            | No                                      | SuccessResponse(Drafting)                     | Form                                                | Complex parsing.                                              |
| POST       | /workstation                              | workstation.py           | create_workstation                 | No                                      | SuccessResponse(WorkStation)                  | Form                                                | Duplicate path also in job_extras (#operation_id difference). |
| PUT        | /workstation/{ws_id}                      | workstation.py           | update_workstation                 | No                                      | SuccessResponse(WorkStation)                  | Form                                                | --                                                            |
| DELETE     | /workstation/{ws_id}                      | workstation.py           | delete_workstation                 | No                                      | SuccessResponse(None)                         | Path                                                | Hard delete.                                                  |
| GET        | /workstation/by-name/{workstation_name}   | workstation.py           | get_workstation_by_name            | No                                      | SuccessResponse(WorkStation)                  | Path                                                | --                                                            |
| GET        | /workstation/active                       | workstation.py           | get_active_workstations            | No                                      | SuccessResponse(List[WorkStation])            | Query planning_section_id, search                   | Filter active only.                                           |
| (Multiple) | /departments/...                          | department.py            | (see detailed sections)            | Yes (PermissionChecker)                 | SuccessResponse(...)                          | Department\* schemas                                | Prefix based grouping.                                        |

> Numerous additional auth endpoints (password reset flows, logout, invites) likely exist beyond scanned 400 lines of `auth.py`. They are flagged **(UNCERTAIN)** and should be enumerated in a secondary pass if required.

---

## 3. Detailed endpoint sections

Due to volume, structured details provided for representative core CRUD sets and complex workflow endpoints. Remaining follow same pattern; where omitted, mark **(UNCERTAIN)**.

### POST /jobs — jobs.py:create_job

- Location: `src/app/routers/jobs.py` line ~15
- Decorator: `@router.post("/jobs", response_model=JobResponse, status_code=201)` with `Depends(PermissionChecker("jobs", "create"))`
- Request Body Model: `JobCreate`
  - Fields: name (str), job_number (str), account_id (int, FK Account.id), description (Optional[str]), priority (Optional[str]), start_date (Optional[date]), due_date (Optional[date])
- Path Params: None
- Query Params: None
- Headers: `Authorization: Bearer <token>` (required via PermissionChecker => user resolution)
- Responses:
  - 201: JobResponse (fields mirror Job entity plus metadata)
  - 400: Job number exists / account not found (HTTPException via `error_response`)
  - 404: Account not found
- DB Models & Operations:
  - SELECT Account by id
  - SELECT Job by unique job_number
  - INSERT Job (sets status_id=1, created_by, created_at)
- Dependencies: `get_db`, `PermissionChecker("jobs","create")`
- Related Endpoints: GET /jobs, GET /jobs/{id}, PUT /jobs/{id}, DELETE /jobs/{id}
- Migration Notes (DRF):
  - Use ModelViewSet or JobViewSet with action `create`. Serializer: JobSerializer (validate uniqueness of job_number; account exists). Permissions: Custom `HasActionPermission("jobs","create")` mapping. Use `UniqueValidator` on job_number. Wrap in transaction atomic.
- Example cURL:

```bash
curl -X POST http://localhost:8000/jobs \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Kitchen Remodel","job_number":"JOB-1001","account_id":1,"description":"Full remodel"}'
```

- Sample Response:

```json
{
  "id": 12,
  "name": "Kitchen Remodel",
  "job_number": "JOB-1001",
  "account_id": 1,
  "status_id": 1,
  "created_by": 5,
  "created_at": "2025-11-17T10:12:55Z"
}
```

### GET /jobs — jobs.py:get_jobs

- Location: jobs.py line ~40
- Decorator: `@router.get("/jobs", response_model=List[JobResponse])`
- Query Params: skip (int, default 0), limit (int, default 100), account_id (Optional[int]), status_id (Optional[int]), priority (Optional[str])
- Response: List[JobResponse]
- DB Ops: SELECT with WHERE filters, ORDER BY created_at DESC, OFFSET+LIMIT
- Migration Notes: Implement `JobViewSet.list`; integrate DjangoFilterBackend (fields: account_id, status_id, priority). Pagination with DRF PageNumberPagination. Ordering filter.
- Example cURL:

```bash
curl -H "Authorization: Bearer TOKEN" "http://localhost:8000/jobs?account_id=1&limit=50"
```

### PUT /jobs/{job_id} — jobs.py:update_job

- Path Param: job_id (int)
- Body: JobUpdate (partial allowed via `exclude_unset=True`)
- Operations: SELECT existing; conditional uniqueness check on job_number; optimistic update; timestamps updated.
- Migration Notes: Serializer with `update()` override; handle uniqueness at validation stage; leverage `partial=True` in DRF.

### DELETE /jobs/{job_id} — jobs.py:delete_job

- Soft delete simulated by `status_id=3` then commit.
- Migration: Consider adding `is_deleted` or status field mapping in Django; implement custom action or treat as standard destroy customizing `perform_destroy()`.

### POST /accounts — accounts.py:create_account

- Similar structure to jobs create; includes uniqueness (name, optional account_number).
- Migration: AccountSerializer with conditional uniqueness on account_number if provided.

### GET /accounts — accounts.py:get_accounts

- Search logic uses `ilike` OR on name & account_number.
- Migration: Use `icontains` filtering via custom FilterSet fields.

### POST /fabs — fabs.py:create_fab

- Heavy FK validation (Job, User, StoneType, StoneColor, StoneThickness, Edge).
- Migration: Pre-validate all foreign keys in serializer `validate()` or use nested DRF validations; transaction.atomic for multi-check/insert.

### GET /jobs/{job_id}/fabs — fabs.py:get_fabs_by_job

- Pattern: filter on job_id; ensure job exists.
- Migration: Could use nested route with `router.register('jobs/(?P<job_id>[^/.]+)/fabs', FabViewSet, basename='job-fabs')` or custom action `@action(detail=True)` inside JobViewSet.

### Stone resources (types/colors/thickness)

- Common CRUD with uniqueness & optional search.
- Migration: Create base mixin for shared logic; apply `ModelViewSet` with filtering.

### Edges

- Note: DELETE lacks auth dependency — potential security gap.
- Migration: Ensure `IsAuthenticated` + permission check on all destructive actions.

### File Upload `/files/upload`

- Stream size validation & extension check.
- Migration: Use DRF `APIView` or `ModelViewSet` with `parser_classes=[MultiPartParser]`; store file metadata model; implement validation in serializer.

### Department Endpoints (prefix: /departments)

Representative (Create):

- Decorator: `@router.post("")` — uses PermissionChecker("departments","create")
- Body: DepartmentCreate (name unique, description optional)
- DB Ops delegated to `DepartmentService.create_department` then detail fetch.
- Migration: DepartmentViewSet + DepartmentSerializer; after create, return enriched representation with users; possible use of custom serializer `DepartmentDetailSerializer`.
  Other endpoints mirror: update (PUT), status change (PATCH), delete (DELETE soft via status), list (GET with pagination logic), fetch users (GET with page & filters).
  Pagination: manual math; convert to DRF pagination & filterset (search, status). Sorting enumerated fields -> order_by mapping.

### Role Endpoints (prefix: /roles)

- Create role: cascades creating permissions relations, user assignments. Migration: treat as service method invoked from serializer `create()`. Consider splitting into separate endpoints if complexity is high.
- Get role with members & permissions: multi-query assembly. Migration: custom `retrieve()` with serializer performing nested fetches or dedicated read serializer.
- Update role & status: patch endpoints -> may unify under `partial_update` & custom action for status.
- Deactivate user under roles scope: map to custom action `@action(methods=['patch'], detail=True, url_path='users/(?P<user_id>[0-9]+)/deactivate')` or move to Users domain.

### Job Extras Workflow (templating, drafting, slabsmith, salesct, technician clock)

- Pattern: multiple small endpoints manipulating workflow states across tables, often expecting Form fields (not JSON), manual list parsing, artificial file id generation.
- Migration: Consolidate into dedicated ViewSets: `TemplatingViewSet`, `DraftingViewSet`, `SalesCTViewSet`, etc., or a single `WorkflowViewSet` with custom actions. Replace ad-hoc string lists with relational tables or JSONField arrays. Use `transaction.atomic()` for multi-field updates. File IDs should leverage `File` model relations.

### Operator & Shop Planning

- Form-based creation storing comma-separated IDs.
- Migration: Replace comma-separated strings with ManyToMany relations or through models (preserve ordering via an ordering field). Implement ordering logic in Django models (e.g., intermediate model with position integer).

### Auth (selected)

- Login & refresh implement auditing + notifications; relies on JWT and background tasks.
- Migration: Implement custom JWT auth (SimpleJWT) + signals for audit trail; background tasks mapped to Celery tasks or Django signals.

> Remaining unexpanded endpoints follow same extraction pattern. For each, apply CRUD migration plan with serializer validation, DRF permission mapping, and atomic writes.

---

## 4. Database models and relationships

(Representative; some model files not fully scanned — mark **(UNCERTAIN)** where needed.)

### Core Models (in `src/app/database/`)

- Job: id PK, account_id FK -> Account, status_id FK -> Status; fields: name, job_number (unique), priority, start_date, due_date, created_by, created_at, updated_by, updated_at. Relationship: many Fabs.
- Account: id PK; unique name; optional account_number; contact_person, email, phone, address; status_id -> Status; one-to-many Jobs.
- Fab: id PK; FKs: job_id -> Job, sales_person_id -> User, stone_type_id -> StoneType, stone_color_id -> StoneColor, stone_thickness_id -> StoneThickness, edge_id -> Edge; workflow fields (current_stage, status_id) + schedule fields.
- StoneType / StoneColor / StoneThickness / Edge: basic catalog entities with uniqueness on name or thickness; status_id -> Status.
- User: (not fully scanned) includes role_id, status, is_super_admin, is_locked, failed_login_attempts; relates to Role, Departments, Permissions via user_role join.
- Role, Permission, ActionMenu, RolePermission, UserRole: permission matrix (many-to-many between Role and Permission; UserRole linking User & Role). ActionMenu groups permissions.
- Department: id, name unique, description, status, users relation (likely User.department_id or join table). Soft delete via status.
- File (via FileService) (UNCERTAIN definition) storing path, type, directory, user association.
- Workflow Models (Templating, Drafting, SlabSmith, SalesCT, FinalProgramming, CutList, OperationWorkflow, ShopPlanning, ShopPlanningSection, WorkStation, PlanningSection, JobTechnicianWorkflow): store timestamps, file_ids (comma strings), revision_history (list) — suggests need to normalize.

### Relationship Diagram (Textual ERD)

- Account 1 — \* Job (Account.id = Job.account_id)
- Job 1 — \* Fab (Job.id = Fab.job_id)
- User 1 — \* Fab (User.id = Fab.sales_person_id)
- Fab \* — 1 StoneType / StoneColor / StoneThickness / Edge (multiple catalog FKs)
- Role _ — _ Permission (through RolePermission)
- User _ — _ Role (through UserRole)
- ActionMenu 1 — \* Permission (Permission.action_menu_id) **(UNCERTAIN field naming)**
- Department 1 — \* User (department assignment) **(UNCERTAIN)**
- Job 1 — _ Workflow entities (e.g., Templating via fab linkage) with Fab 1 — 1.._ Templating / Drafting / SlabSmith / SalesCT / FinalProgramming / CutList / JobTechnicianWorkflow
- PlanningSection 1 — \* WorkStation; ShopPlanning has many PlanningSection via comma list (to convert to proper M2M); ShopPlanningSection references PlanningSection + many WorkStations (ordered list) — restructure to a through model with ordering.

### Special Constructs & Notes

- Comma-separated ID fields (fab_ids, planning_section_ids, workstation_ids, machine_ids, operator_ids, file_ids) should become relational ManyToMany or through tables with `position` column.
- Revision history stored as appended list (SalesCT) — use JSONField or separate Revision model.
- Lack of explicit indexes visible; add indexes for fields frequently filtered: `job_number`, `Account.name`, status fields, created_at timestamps.
- Missing `greenlet` dependency leads to async session bridging errors; ensure Django uses purely sync DB (psycopg2) or adopts async stack (ASGI + Django 5 async ORM when stable) — simpler: keep sync.

---

## 5. DRF Migration mapping / action plan

### Model Mapping Strategy

- Translate each SQLModel class to Django `models.Model`. For timestamps use `DateTimeField(auto_now_add=True)` / `auto_now=True`. For status codes centralize into choices or a Status model if dynamic.
- Replace comma-separated strings with:
  - `ManyToManyField` (unordered) or through model with `ordering = models.IntegerField()` when order matters.
  - File relations: separate File model + ForeignKey or ManyToMany to workflow entity.
- JSON-like lists (revision_history): Django `JSONField` or a child `Revision` model.

### Endpoint -> DRF Component Mapping (Representative)

- Jobs, Accounts, Fabs, Stone catalogs, Edges: `ModelViewSet` with `list`, `retrieve`, `create`, `update`, `destroy`; soft delete handled in `destroy()`.
- Role & Permission & ActionMenu: Dedicated ViewSets with custom actions for status change, uniqueness checks.
- Department: `DepartmentViewSet` + custom `users` action for listing department members.
- File Upload: `FileViewSet` with custom `upload` action; use DRF `MultiPartParser`.
- Workflow (Templating, Drafting, etc.): Consolidate into domain-specific ViewSets or keep separate smaller APIViews; prefer structured nested routes: `/fabs/{id}/templating/` etc.
- Auth: Use `djangorestframework-simplejwt` for tokens; replicate audit trail via signals + custom model `AuditTrail`.

### Serializers

- Standard serializers per model; nested serializers for composite responses (Role with permissions & members, Department with users).
- Validation methods for uniqueness & FK existence; use `validators.UniqueValidator` where applicable.

### Permissions

- Implement a custom permission class mirroring `PermissionChecker(resource, action)` mapping role->permission set: `class HasActionPermission(BasePermission)` evaluating request method + route name.
- Map `Depends(get_current_user)` to `IsAuthenticated`; super-admin and role checks to `IsAdminUser` or custom `IsSuperAdmin`.

### Filtering & Pagination

- Use `django-filter` for search/status filters (fields: name, status_id, job_number). Integrate SearchFilter & OrderingFilter where needed.
- Pagination: global PageNumberPagination with adjustable page size.

### Transactions

- Multi-step operations (create_role, schedule_templating) wrap in `@transaction.atomic` to ensure consistency.

### Prioritized Migration Plan

1. Create Django project & base app modules; port core Account, User, Role, Permission, ActionMenu, Department, Job, Fab, catalog models.
2. Implement serializers & ModelViewSets for core CRUD (accounts, jobs, fabs, stone catalogs, edges).
3. Integrate JWT auth (SimpleJWT) + permission matrix (roles/permissions) + custom permission class.
4. Port workflow models & endpoints (templating, drafting, shop planning) refactoring comma lists to proper relations.
5. Implement file upload service + storage strategy (FileField + storage backend).
6. Port complex endpoints (role member stats, department pagination) optimizing queries (select_related, prefetch_related).
7. Migrate tests: replicate existing behavior with Django test cases + APIClient + pytest-django.
8. Add observability: audit trail model, signals for login/password change.
9. Harden & optimize (indexes, caching, rate limiting).
10. Deployment adjustments (ASGI entrypoint, gunicorn config, CI pipeline).

---

## 6. Tests & validations

Existing tests (found in `tests/`):

- `test_authentication.py`, `test_auth_diagram_flows.py`: Auth flows and diagram logic.
- `test_departments.py`: Department CRUD & listing.
- `test_health.py`: Health endpoints.

Recommended DRF test cases per endpoint category:

- Accounts: create (201), duplicate name (400), list with search filter, update partial, delete (hard vs soft semantics).
- Jobs: create with invalid account (404), uniqueness job_number (400), list filters, soft delete effect on list.
- Fabs: FK validations (missing StoneType -> 404), update retains unchanged fields.
- Role/Permission: create role with permissions, update role removing a permission, deactivate user.
- File: upload invalid extension (400), oversize file (413), retrieve metadata (200), delete (200).
- Workflow: schedule templating, unschedule, redraft transition, add files, revision updates.
- Shop Planning: create with ordered sections, list filtering by job_id.
- Edge/Stone catalogs: uniqueness, status change validations.

Pytest -> Django conversion example:

```python
# Original FastAPI style (simplified)
async def test_create_account(async_client):
    resp = await async_client.post('/accounts', json={"name":"A1"})
    assert resp.status_code == 201

# Django DRF pytest style
@pytest.mark.django_db
def test_create_account(api_client, user_with_permission):
    api_client.force_authenticate(user_with_permission)
    resp = api_client.post('/accounts/', {"name": "A1"}, format='json')
    assert resp.status_code == 201
    assert resp.data['data']['name'] == 'A1'
```

Validation Enhancements:

- Enforce database constraints (unique indexes) matching serializer validations.
- Replace manual comma string parsing with structured relations so tests validate relationship integrity.

---

## 7. Files to update & suggested PR checklist

### Target Django File Set

- `core/models/account.py`, `core/models/job.py`, `core/models/fab.py`, `core/models/catalog.py` (stone types/colors/thickness/edges)
- `auth/models/user.py`, `auth/models/role.py`, `auth/models/permission.py`, `auth/models/action_menu.py`
- `workflow/models/*.py` (templating, drafting, slabsmith, salesct, final_programming, cutlist, planning_section, workstation, shop_planning, operation_workflow)
- `core/serializers/*.py` matching above
- `core/views/*.py` (ViewSets & APIViews)
- `core/urls.py` aggregated into project `urls.py`
- `auth/permissions.py` (HasActionPermission, IsSuperAdmin)
- `files/models/file.py`, `files/services/upload.py`
- `audit/models/audit_trail.py` + `audit/signals.py`
- `tests/` reorganized by domain (accounts, jobs, auth, workflow, permissions)

### PR Checklist

- [ ] Models created with matching fields & constraints
- [ ] Migrations generated and applied
- [ ] Serializers with validation parity (uniqueness, FK existence)
- [ ] ViewSets wired with permissions & filtering/pagination
- [ ] JWT auth configured (SimpleJWT) + custom permission mapping
- [ ] File upload integrated (storage backend selected)
- [ ] Workflow relations normalized (no comma-separated lists remain)
- [ ] Tests covering create/read/update/delete + edge cases pass
- [ ] Performance check: N+1 queries addressed (prefetch_related/select_related)
- [ ] Documentation updated (README & MIGRATION_SPEC references)
- [ ] CI pipeline updated (lint, test, coverage)
- [ ] Rollback plan: if deployment fails, revert to FastAPI service (keep previous containers/images for 1 release cycle)

### Migration Risks & Rollback Notes

- Risk: Complex workflow endpoints rely on implicit state transitions; incorrect mapping may break production flows. Mitigation: incremental migration with feature flags.
- Risk: Permission matrix re-implementation — mismatch can produce authorization holes. Mitigation: exhaustive permission parity test suite.
- Risk: Comma-separated lists -> relational mapping may change semantics (ordering). Mitigation: create deterministic ordering column & migration script to parse existing values.
- Rollback: Maintain FastAPI service side-by-side until DRF endpoints verified; blue/green deploy strategy.

---

## 8. Additional Migration Notes

- Add `greenlet` (if staying temporarily on SQLAlchemy async) or remove async hybrid patterns in favor of Django sync ORM.
- Introduce consistent status enumeration (Active=1, Inactive=2, Deleted=3) via choices.
- Replace manual timestamp assignments with Django auto fields.
- Consolidate duplicate workstation endpoint (in `job_extras.py` and `workstation.py`).
- Normalize file handling: Map pseudo generated file_ids to actual File model PKs.
- Introduce indexing strategy: `(job_number)`, `(name)` on catalog tables, `(status, created_at)` composite where high selectivity.

---

## 9. Outstanding Uncertainties

- Full list of auth endpoints beyond 400 lines of `auth.py` (password reset, logout, invite flows) — require additional scan for total parity.
- Exact schema of some workflow models (not fully read) — confirm fields before model port.
- Relationship direction for Department ↔ User (FK vs M2M) — inspect user model implementation.

---

## 10. Summary Implementation Timeline (Condensed)

Week 1: Core models & CRUD; auth skeleton.  
Week 2: Roles/permissions matrix + catalogs + tests.  
Week 3: Workflow models normalization + file upload service.  
Week 4: Advanced endpoints (stats, revisions) + performance tuning + full test migration.  
Week 5: Cutover & monitoring.

---

## SUMMARY.md

Biggest Migration Risk: The permission and workflow subsystems combine granular action rights (create/read/update/delete per resource) with multi-step fabrication/templating state transitions encoded in ad-hoc endpoints and comma-separated ID fields. Translating these to Django without losing ordering, historical revision trails, or inadvertently widening access (e.g., endpoints missing auth now) poses the highest risk of logic regressions or security holes.

Recommended First PR: Establish the foundational Django project with core data model parity (Account, User, Role, Permission, ActionMenu, Job, Fab, Stone catalogs, Edge) plus JWT auth and the custom permission class. Include a small initial test suite validating role-permission checks and one representative CRUD flow (Jobs). This creates a stable substrate for subsequent workflow refactors while enabling early performance and authorization validation before migrating the more volatile workflow endpoints.
