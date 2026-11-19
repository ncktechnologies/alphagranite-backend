# Odyssey Tracker Mobile App: Implementation Plan

Written 2026-11-17. This plan covers a native mobile app for iOS and Android that gives every role the same capabilities as the web app at `ag.odysseytracker.com`, using the existing backend API.

It builds on three assessments: `BACKEND_ASSESSMENT.md` (this folder), `WEB_ASSESSMENT.md` (web repo, `docs/`) and `INSTALLER_APP_ASSESSMENT.md` (installer app repo, `docs/`). Item IDs such as `BE-SEC-01` refer to those documents.

## 1. Decisions

These are recommendations. Section 12 lists the ones that need a product decision before work starts.

| Decision | Recommendation | Reason |
|---|---|---|
| Framework | Flutter | The team already ships the installer app in Flutter. Its design tokens, widgets, secure session, offline cache, media capture and PDF annotator carry over. The web UI is built on DOM-only libraries (Radix, Tailwind), so React Native would share types but no screens. |
| Number of apps | One app, "Odyssey Tracker", with role-based navigation | The web is one app whose menu is filtered by permission. One mobile app keeps that model, one store listing and one release train. |
| Installer app | Becomes the installer module of the new app. The existing app stays in the stores until the module reaches parity, then is retired. | Avoids maintaining two apps with duplicated login, timer and media code. |
| Devices | Phone and tablet, portrait and landscape | Installers and templaters carry phones; operators and coordinators use tablets. |
| Meaning of "just like the web" | Every web feature is in the app (confirmed as a requirement on 2026-11-17): same data, same actions, same columns, same filters and same permission rules for every role. Layouts are redesigned for touch and small screens. Tables keep every column through a pinned-column table view, a column chooser and a row detail sheet. The shop calendar keeps day, week and month views, the axis swap and all four filters; drag-and-drop is used on tablets and a "pick a slot" sheet on phones. | A 20-column table or drag-and-drop calendar cannot be copied onto a phone unchanged, so the feature is kept and the interaction is adapted. |
| Offline | Read cache everywhere; queued writes for field actions (timers, notes, photos, completion); everything else requires a connection | Job sites and shop floors lose signal. Office workflows do not need offline support. |

## 2. What the web does today

The mobile app must cover these areas. Paths are the web routes; the right-hand column is the API group each one uses.

| Area | Web routes | API |
|---|---|---|
| Sign-in, first-login password change, reset by emailed code, profile | `/auth/*`, `/settings/profile` | `/auth/*` |
| Dashboard | `/` | `/dashboard` |
| Jobs and accounts | `/job`, `/job/details/:id`, `/create-jobs`, `/accounts`, `/need-to-invoice`, `/status-job-report` | `/jobs`, `/accounts`, `/jobs/{id}/notes`, `/jobs/{id}/media` |
| Sales: create and edit FAB IDs | `/sales`, `/sales/new-fab-id`, `/sales/edit/:id` | `/fabs`, lookups (`/stone-types`, `/stone-colors`, `/stone-thickness`, `/edges`, `/fab-types`) |
| Templating: coordinator scheduling and technician work | `/job/templating`, `/job/templating-technician`, `/jobs/:id/templater/timer` | `/templating/*`, `/job-timers/templater/*` |
| Pre-draft review | `/job/predraft` | `/pre-draft-review/*` |
| Drafting, CNC drafting, revisions | `/job/draft`, `/job/cnc`, `/job/revision` | `/drafting/*`, `/CNC/*`, `/revisions/*` |
| Sales check (Sales CT) | `/job/draft-review` | `/sales-ct/*` |
| SlabSmith | `/job/slab-smith` | `/slabsmith/*` |
| Cut list and final programming | `/job/cut-list`, `/job/final-programming` | `/cut-list/*`, `/final-programming/*` |
| Cost of stone | `/job/cost-of-stone` | `/fabs/cost-of-stone` |
| Shop: planning, calendar, auto-schedule, status, revisions, settings | `/shop`, `/shop/calendar`, `/shop/auto-schedule`, `/planning-status`, `/shop/fab/:id`, `/revision`, `/shop/settings` | `/shop/plans/*`, `/shop-revisions/*`, `/workstation`, `/planning-section` |
| Operators: workstation tasks and timers | `/operator/dashboard`, `/operator/task/:id` | `/operators/*` |
| Install scheduling and completion; resurfacing | `/job/install-to-schedule`, `/job/install-scheduled`, `/job/resurfacing`, `/resurfacing-status` | `/install-scheduling/*`, `/install-completion/*`, `/resurface-scheduling/*` |
| Installer schedule and timer | installer pages | `/job-timers/installer/*`, `/fabs?installer_id=` |
| Reports and performance | `/report/*`, `/performance/*` (about 25 reports) | `/reports/*`, `/performance/*` |
| Notifications | `/settings/notifications`, header tray | `/notifications/*` |
| Administration | `/employees`, `/departments`, `/settings/roles`, `/settings/permissions`, `/settings/stone-types`, `/audit` | `/employees`, `/departments`, `/roles`, `/action-menus`, `/permissions`, `/audit-trails` |

## 3. Backend work required first

The mobile app cannot ship safely on the backend as it is. These items come from the backend assessment and block the phases shown.

| Blocks | Item | Why the mobile app needs it |
|---|---|---|
| Phase 0 | BE-SEC-01, BE-SEC-07, BE-BUG-01, BE-SEC-09 | Expiring access tokens with working refresh, token types enforced, server-side sessions and logout. Mobile sessions last weeks, so refresh must be right from the first build. |
| Phase 0 | BE-SEC-04 | Server-side permission checks on every route. A mobile app is easy to inspect; hiding buttons protects nothing. |
| Phase 0 | BE-SEC-03 | Signed or authenticated file URLs. |
| Phase 0 | BE-ARCH-04 | One error shape, consistent pagination, `/api/v1` everywhere and an accurate OpenAPI document, so the Dart client can be generated. |
| Phase 1 | New: idempotent writes | Timer actions, notes, uploads and completion must accept `client_action_id` and `occurred_at`, so queued offline actions can be replayed without duplicates. |
| Phase 1 | New: device registration and push | `POST /api/v1/devices` (token, platform, app version), `DELETE /api/v1/devices/{id}`, and a Celery task that sends each `notifications` row to FCM/APNs. |
| Phase 1 | New: app version check | `GET /api/v1/app/version` returning minimum and latest supported versions per platform. |
| Phase 1 | New: role-aware dashboard | `GET /api/v1/dashboard/me` returning the caller's queue counts, overdue items and today's schedule. Only a general `GET /api/v1/dashboard` exists today. |
| Phase 2 | BE-PERF-05 | Slim, searchable lookup endpoints. A phone cannot download 1,000 FABs to fill a picker. |
| Phase 2 | BE-ARCH-02 | One server-side stage state machine, so web and mobile cannot disagree about allowed transitions. |
| Phase 3 | BE-PERF-04 | Cached report responses and server-generated PDFs for every report. |
| Any | BE-PERF-07 | Real-time event channel. Optional at launch (push plus pull-to-refresh is enough), but it removes polling. |
| Any | BE-BUG-09 | Timestamps with explicit offsets. Until then the app treats naive values as America/Chicago (section 5.6). |

Add `GET /api/v1/me/bootstrap`: one call that returns the profile, roles, action permissions, unread notification count and reference-data versions. The app calls it at launch and on resume.

## 4. Repository layout

Create a monorepo `odyssey-mobile` managed with Melos:

```
odyssey-mobile/
  apps/
    odyssey/              # the new app (phone and tablet)
    installer/            # existing ag-installer-app, moved in, until retired
  packages/
    odyssey_api/          # generated Dart client and models from OpenAPI
    odyssey_core/         # auth/session, HTTP, offline store and outbox, time, permissions, logging
    odyssey_ui/           # design tokens, theme, shared widgets (from lib/app/ of the installer app)
    odyssey_media/        # camera, gallery, compression, photo and PDF annotation, upload queue
    feature_*/            # one package per module in section 6
```

Moving the installer app in first, and extracting `odyssey_core`, `odyssey_ui` and `odyssey_media` from it, proves the shared packages against a real app before the new one depends on them. The fixes in the installer assessment (APP-BUG-01 to 04, APP-QUAL-01) are done once, inside those packages.

## 5. Architecture

### 5.1 Stack

| Concern | Choice |
|---|---|
| Language and SDK | Dart 3, Flutter stable |
| State management and DI | Riverpod with code generation |
| Navigation | `go_router` with typed routes, deep links and redirect guards |
| HTTP | `dio` with a generated client (`openapi-generator` dart-dio, or `retrofit`) |
| Models | `freezed` and `json_serializable` |
| Local database | `drift` (SQLite) for the read cache and the outbox |
| Secure storage | `flutter_secure_storage` for tokens; `local_auth` for biometric unlock |
| Push | `firebase_messaging` (FCM, with APNs on iOS) and `flutter_local_notifications` |
| Background work | `workmanager` for upload and outbox drain |
| Charts | `fl_chart` |
| PDF | `pdfx` or `syncfusion_flutter_pdfviewer` for viewing; the installer app's annotator for mark-up |
| Localisation | `flutter_localizations` with ARB files, English and Spanish |
| Time | `timezone` package, fixed to America/Chicago for display |
| Monitoring | `sentry_flutter` |
| Tests | `flutter_test`, `mocktail`, `integration_test`, `patrol` for native dialogs |

### 5.2 Layers

Each feature package has three layers:
- **data**: API calls through `odyssey_api`, DTO-to-domain mapping, drift tables for cached copies;
- **domain**: plain models and use cases, with no Flutter imports;
- **presentation**: Riverpod notifiers and widgets.

Widgets never call the HTTP client or the database directly.

### 5.3 Authentication and session

1. Login posts to `/auth/login` and stores the access and refresh tokens in secure storage. Roles and action permissions come from the bootstrap call.
2. A `QueuedInterceptor` refreshes on 401 once, retries the request, and signs the user out only when the refresh is rejected. Network errors never sign the user out.
3. First login forces the change-password screen. Password reset uses the emailed six-digit code, as on the web.
4. After five minutes in the background the app asks for biometrics or the device passcode before showing data. This is on by default and a user setting.
5. Sign-out revokes the refresh token on the server, unregisters the push token, and clears the cache, the media cache and the outbox after warning about unsent items.
6. Every local table row carries the owning user ID, so two people sharing a device never see each other's data.

### 5.4 Permissions and navigation

The backend returns `action_permissions` as a list of `{menu_code, can_create, can_read, can_update, can_delete}`. The app keeps one route table in which each destination declares its `menu_code`, mirroring the web's `permissionKey`. Navigation, route guards and action buttons all read that table. A destination the user cannot read is not shown; a 403 from the API shows "You don't have access to this" and refreshes the permission set. Permissions are refreshed at launch, on resume, and whenever a 403 arrives.

Layout:
- **Phone**: bottom bar with Home, My Work, Search, Notifications and More. "More" lists the remaining modules the user can read.
- **Tablet**: navigation rail with the same destinations and a two-pane list and detail layout.

Home is role-aware: an installer sees today's installs, an operator sees the workstation queue, a drafter sees assigned FABs, a coordinator sees items waiting to be scheduled, and an owner sees KPIs.

### 5.5 Offline and sync

| Kind of data | Behaviour |
|---|---|
| Lists and details the user has opened | Cached in drift. Shown immediately, then refreshed. A banner shows "Offline: last updated 10:42" when the copy is stale. |
| Reference data (stone types, colours, thickness, edges, FAB types, employees, workstations) | Synced at login and when the bootstrap call reports a new version. Available offline in pickers. |
| Field actions: timer start, pause, resume and stop; notes; photo and file uploads; install and templating completion | Written to the outbox with a client UUID and device timestamp, applied to the screen optimistically, and sent in order when online. The server deduplicates on the UUID. |
| Everything else: creating FABs, scheduling, approvals, settings, administration | Requires a connection. Buttons are disabled offline with an explanation. |

Outbox rules:
- one ordered queue per entity (for example per FAB timer), so a pause is never sent before its start;
- exponential backoff on network errors;
- a 4xx marks the item "needs attention" with the server's message, and the user chooses to edit or discard it;
- a 409 (for example, the timer was stopped by a supervisor on the web) reloads the server state and tells the user what changed;
- the queue drains on connectivity change, on resume and in a background task;
- a badge shows the number of unsent items, and the list is reachable from Home.

### 5.6 Time

All times are shown in America/Chicago, whatever the device timezone is, because the business runs on shop time. The app does this with the `timezone` package when formatting. It does not shift the device clock, which is what the web does today (WEB-BUG-05). Until the API returns explicit offsets (BE-BUG-09), one parsing function in `odyssey_core` treats naive timestamps as America/Chicago and converts them to UTC instants. Durations are computed from UTC instants.

### 5.7 Files and media

- Capture from camera or gallery with several photos per session; compress to about 2,000 px on the long edge before queuing.
- Annotate photos and PDFs with the existing annotator from the installer app.
- View PDFs, images and GLB 3D models in-app, as the web does. Open DXF and other formats the web cannot preview in an external app through the share sheet.
- Uploads go through the background queue with progress, retry and an idempotency key per file.
- Downloads use signed URLs, cached on disk with a size cap and least-recently-used eviction.

### 5.8 Notifications

Every row written to the `notifications` table is also sent as a push message with `event`, `fab_id` and `job_id`. Tapping a push deep-links to that FAB or job. The Notifications tab shows the same list as the web tray, with read state synced through `/notifications/{id}/read`. Users choose which events they receive on the settings screen.

## 6. Feature modules and screens

Each module lists the mobile screens and how they differ from the web. "Table → cards" means the web's data table becomes a searchable, filterable card list on phones and a compact table on tablets.

| Module | Screens | Notes for mobile |
|---|---|---|
| `feature_auth` | Sign in; change password; reset password; biometric unlock; profile | Reuse the installer app's login. |
| `feature_home` | Role-aware dashboard; pending-sync list | Needs the new role-aware dashboard endpoint (section 3). |
| `feature_search` | Global search by job number, FAB ID, job name or account; scan a FAB label | Barcode or QR scanning depends on labels being printed (section 12). |
| `feature_jobs` | Job list; job detail with FABs, notes, media and stage timeline; create and edit job; accounts list and detail; need-to-invoice | Table → cards. The stage timeline is the centrepiece of job detail. |
| `feature_sales` | FAB list by stage; new FAB ID; edit FAB ID; Sales CT review with approve, request revision and send to drafting | The 1,800-line web form becomes a stepped form (job, stone, pieces, process steps, review) with draft saving. |
| `feature_templating` | Coordinator: schedule, assign and reschedule. Technician: today's templates, timer, completion, photos | Technician screens work offline. |
| `feature_drafting` | Pre-draft review; drafter queue and detail with session timer; CNC drafting; revisions; file upload | Drafting itself happens on a workstation. Mobile covers review, status, session control, notes and files. |
| `feature_slabsmith` | Queue; detail; session timer; files; complete | |
| `feature_production` | Cut list and its scheduling; final programming queue and detail; cost of stone | The cut-list calculation table is tablet-first; phones get a per-FAB summary with edit sheets. |
| `feature_shop` | Plans by workstation; calendar; create and reschedule plan; auto-schedule; status table; FAB shop detail; shop revisions; shop settings | The calendar is a day or agenda view on phones and a week grid on tablets. Rescheduling uses a "move to" sheet in place of drag-and-drop on phones. |
| `feature_operator` | Workstation picker; task queue; task detail with timer, percentage complete, files and notes | Large touch targets; works offline. |
| `feature_install` | Coordinator: to schedule, scheduled, assign crew, completion review, resurfacing. Installer: today, job detail, timer with square-feet entry, photos, completion, optional customer signature | The installer side is the existing installer app's code. |
| `feature_reports` | Report list; each report as a KPI header, a chart, and a table with pinned first column; filters; export and share | Section 7. |
| `feature_notifications` | List; mark read; preferences | |
| `feature_admin` | Employees (list, create, edit, activate); departments; roles and permissions; stone types and colours; workstations and planning sections; SLA settings; installer rates; performance static data; audit log | The permission matrix becomes one screen per role with a toggle list per resource. |

## 7. Reports on mobile

The web has about 25 reports with wide tables. For each report:
1. a summary header with the three or four numbers that matter;
2. a chart where the web has one;
3. the table with a pinned first column and horizontal scroll, and on phones a list of row cards that expand;
4. the same filters as the web in a bottom sheet, remembered per report;
5. "Export" downloads the server-generated PDF or XLSX and opens the share sheet.

Financial reports (weekly labour cost, installer rates, the owner overview) need their own permission code (BE-SEC-04 item 3) and biometric confirmation before opening.

## 8. Design

- Start from the installer app's tokens in `lib/app/design_tokens.dart` (brand olive `#7A9705`, the neutral scale, spacing and radius scales) and the `ag_*` widgets, and align with the web's 2026 redesign so both feel like one product.
- Produce a Figma library first: colour, type, spacing, buttons, inputs, cards, list rows, status pills for every stage, the timer control, sheets, empty and error states.
- Rules: 48 dp minimum touch target; primary action fixed at the bottom of the screen; one primary action per screen; status always shown with text and colour together; text scaling supported to 1.3×; contrast at WCAG AA, checked in daylight for the field screens.
- Dark theme for shop-floor tablets if users want it (section 12).
- Design the stage timeline, the timer control and the card list first, because every module reuses them.

## 9. Phases

Durations assume two Flutter engineers, one backend engineer, a part-time designer and a part-time QA engineer. They are estimates to be revised after Phase 0.

| Phase | Duration | Scope | Exit criteria |
|---|---|---|---|
| **0. Foundations** | 3 weeks | Backend prerequisites for Phase 0 (section 3). Monorepo; installer app moved in; `odyssey_core`, `odyssey_ui` and `odyssey_media` extracted; generated API client; auth with refresh and biometrics; permission-driven shell; offline cache and outbox; CI, flavours, Sentry; Figma library. | A tester signs in on iOS and Android, sees a role-correct empty shell, and survives token expiry and airplane mode. The installer app runs on the shared packages. |
| **1. Field and floor** | 6 weeks | `feature_home`, `feature_install` (installer side, moved over), `feature_templating` (technician side), `feature_operator`, `feature_notifications` with push, `feature_search`, job detail (read), notes and media. | Installers, templaters and operators do a full day's work on the app, including offline. Pilot with one crew and one workstation. |
| **2. Coordination** | 7 weeks | `feature_jobs` (create and edit), `feature_sales`, templating and install coordinator screens, `feature_drafting`, `feature_slabsmith`, `feature_production`, `feature_shop`. | A FAB can be taken from creation to install completion using only the app. |
| **3. Management** | 4 weeks | `feature_reports` and the performance screens. | Every web report is available with the same numbers for the same filters. |
| **4. Administration** | 3 weeks | `feature_admin`. | Every web settings and administration screen has a mobile equivalent. |
| **5. Hardening and launch** | 3 weeks | Accessibility and performance passes; Spanish review; security test; store listings; staged rollout; retire the old installer app. | Crash-free sessions above 99.5%; cold start under 2.5 seconds on a mid-range Android device; the parity checklist in section 10 is fully ticked. |

That is about 26 weeks. If a shorter first release is wanted, Phases 0 and 1 give a useful app in about 9 weeks, since field and floor roles gain the most from mobile.

## 10. Testing and parity

- **Parity checklist.** Create a sheet with one row per web route and one per web API operation (about 100 routes and 230 queries and mutations in `src/store/api`). Each row records the mobile screen, the API call, the permission code, offline behaviour and test status. A phase is complete when its rows are ticked.
- **Unit tests** for mappers, use cases, the outbox, timer maths and time conversion, including both daylight-saving transitions.
- **Widget tests** for each screen's loading, empty, error, offline and permission-denied states.
- **Integration tests** on real devices for sign-in, token refresh, an offline timer with later sync, photo upload with the app killed part-way, and a push deep link.
- **Contract tests** in backend CI that fail when an API change breaks the generated client.
- **Role tests.** For each seeded role, check that navigation shows exactly what the web shows and that a hidden route returns 403 from the server.
- **Device matrix.** iOS 16 and later on iPhone and iPad; Android 9 and later on a small phone, a large phone and a 10-inch tablet. Include the tablets already in the shop.

## 11. Release and operations

- **Flavours**: dev, staging and production, each with its own bundle ID, API URL, Firebase project and icon badge.
- **CI/CD**: on pull requests run analyse, test and build for both platforms. Merges to `main` ship to TestFlight and the Play internal track through Fastlane or Codemagic. Production releases are staged at 10%, 50% and 100%.
- **Distribution**: the public stores are simplest. If the app should not be public, use Apple Business Manager custom apps and managed Google Play.
- **Versioning**: the app checks `/api/v1/app/version` at launch and shows a forced-update screen when it is below the minimum.
- **Monitoring**: Sentry for crashes and slow frames, with user ID, role and app version attached; backend dashboards for outbox failures and push delivery.
- **Store requirements**: a privacy policy, data-safety forms, a demo account for App Review, and an in-app way to request account deletion (deactivation by an admin is acceptable for an employee-only app, but the path must be described).
- **Support**: an in-app "Report a problem" action that attaches the app version, user ID and the last 200 log lines, with secrets removed.

## 12. Decisions needed before Phase 0

1. **One app or two.** This plan assumes one app that absorbs the installer app. Keeping two apps on shared packages is possible if the installer app should stay minimal for subcontractors.
2. **Subcontractor installers.** Do subcontractors get accounts? If so they need a restricted role and possibly a separate distribution channel.
3. **Depth of drafting and SlabSmith on mobile.** Decided 2026-11-17: the app must have every feature of the web. The web's drafting and SlabSmith screens cover review, status, timers, notes and files, and the app covers the same. CAD work stays in the desktop tools, as it does today.
4. **3D model viewing.** Decided 2026-11-17 by the same requirement: GLB models are viewed in-app.
5. **FAB labels.** Are labels with a barcode or QR code printed, or can they be? Scanning would replace most searching on the shop floor.
6. **Customer signature at install completion.** Wanted or not, and what document should it produce?
7. **Dark theme.** Wanted for shop-floor tablets or not.
8. **Device ownership.** Company tablets under device management, personal phones, or both. This sets the biometric and remote-wipe policy.
9. **Distribution.** Public store listing or private distribution.
10. **Languages at launch.** English and Spanish for all modules, or Spanish only for the field and floor modules first.

## 13. Risks

| Risk | Mitigation |
|---|---|
| Backend security work slips and blocks the app | Phase 0 is mostly backend. Start it now; it is needed whether or not the app is built. |
| Full parity is large (about 100 screens) | Deliver by role in the phase order above, and track the parity checklist weekly. |
| Offline conflicts corrupt timer data | Idempotent, ordered server endpoints; conflicts are shown to the user, never resolved silently; pilot with one crew first. |
| Web and mobile drift apart | Generated API client, one server-side state machine, and permission codes defined once on the server. |
| Time handling errors around daylight saving | One conversion module with tests; move the API to explicit offsets. |
| Old tablets in the shop perform poorly | Test on the actual devices in Phase 0 and set a minimum supported device. |
