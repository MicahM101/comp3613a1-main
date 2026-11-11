# Integration Test Plan — Student Awards

**Project:** Student Awards (COMP 3613 Assignment 1 app, extended for Assignment 2)
**Prepared by:** [name], [student ID]
**Version:** 2.0 — November 2026

## 1. Purpose

Verify that the **real application stack** carries each UAT case end to end:
FastAPI routes, session middleware, service layer and a real SQLite database
working together over HTTP. Nothing is faked — one test per UAT case
(1.1–1.18), so each screenshot maps to a UAT row.

## 2. Approach

- **Framework:** pytest + FastAPI `TestClient` (`python -m pytest tests/integration -q`) — 18 tests.
- **Database:** an isolated temporary SQLite file per test session, created and
  seeded by `tests/conftest.py` — the developer's `database.db` is never touched.
- **Fixtures:** `client` (anonymous TestClient), `student_client` (bob logged
  in), `admin_client` (admin logged in), `seed` (demo data), `query` (direct
  DB lookup for assertions), `uploads_dir`.
- **Style:** each test drives the wireframe workflow over HTTP and asserts the
  response text *and* the resulting database state.

## 3. Entry criteria

- `python manage.py init` has been run at least once (app tables exist).
- Demo users available: `bob/bobpass`, `carol/carolpass`, `admin/adminpass`.
- Command runs green: `python -m pytest tests/integration -q`.

## 4. Integration Testing Plan

Dependencies listed below are the fixtures the test mounts on and the
routes/services the request flows through.

### 4.1 Authentication (UAT 1.1–1.4) — `tests/integration/test_uat_flows.py`

| Test | Dependencies | Description |
|---|---|---|
| `test_uat_1_1_login_lands_on_the_account_page()` | `client`, `seed` → `POST /login`, `GET /` (login router, auth service) | Verifies a correct password lands on the account page with "Welcome, bob", contributions and tracker, and the landing page offers Open app / Sign out |
| `test_uat_1_2_wrong_password_grants_no_session()` | `client`, `seed` → `POST /login`, `GET /app` | Verifies a bad password flashes "Incorrect username or password" and `GET /app` stays 401 |
| `test_uat_1_3_register_then_login_and_duplicate_refused()` | `client`, `seed` → `POST /register` ×2, `POST /login` | Verifies a new account redirects to login and can sign in, while a duplicate username flashes "Username or email already exists" |
| `test_uat_1_4_logout_clears_the_session()` | `student_client` → `GET /logout`, `GET /app` | Verifies logout returns 303 to `/login` and the old account URL is refused (401) |

### 4.2 Workflow 1 — Submit Hours (UAT 1.5–1.8) — `tests/integration/test_uat_flows.py`

| Test | Dependencies | Description |
|---|---|---|
| `test_uat_1_5_submit_form_lists_every_wireframe_field()` | `student_client` → `GET /app/hours/new` (submit router, cause service) | Verifies the form shows the cause dropdown, hours, date, Start Time, file picker and Cancel/Submit |
| `test_uat_1_6_valid_submission_reaches_the_tracker()` | `student_client`, `seed`, `query`, `uploads_dir` → `POST /app/hours/new`, `POST /app/hours/confirm` | Verifies the confirmation screen repeats the details, Confirm stores a pending row with its uploaded document, and the success flash appears on the account page |
| `test_uat_1_7_invalid_input_creates_nothing()` | `student_client`, `seed`, `query`, `uploads_dir` → `POST /app/hours/new` ×3 | Verifies 0 hours, over-budget hours and an `.exe` upload are each refused with their message and no row is stored |
| `test_uat_1_8_cancel_returns_without_creating_a_row()` | `student_client`, `seed`, `query` → `GET /app/hours/new`, `GET /app` | Verifies the Cancel link returns to the account page without creating a submission |

### 4.3 Workflow 2 — Verify Hours (UAT 1.9–1.13) — `tests/integration/test_uat_flows.py`

| Test | Dependencies | Description |
|---|---|---|
| `test_uat_1_9_queue_lists_pending_only_and_searches()` | `admin_client`, `seed` → `GET /admin`, `GET /admin?q=Math` (admin router, review service) | Verifies only pending rows are listed, the search narrows to 1 result, and clearing restores the full queue |
| `test_uat_1_10_review_card_shows_every_detail()` | `admin_client`, `seed` → `GET /admin/submissions/{id}` | Verifies the card shows student ID/name, cause, hours, date, start time, the document link and Reject/Approve buttons |
| `test_uat_1_11_approve_moves_the_row_and_spends_cause_hours()` | `admin_client`, `student_client`, `seed`, `query` → `GET …/decision/approved`, `POST …/decision` | Verifies the confirm screen's go-back, approval flash, the row leaving the queue, the cause dropping 30 → 27, and bob seeing the row as approved |
| `test_uat_1_12_reject_removes_the_row_but_spends_nothing()` | `admin_client`, `client`, `seed`, `query` → `GET …/decision/rejected`, `POST …/decision`, `GET /app` as carol | Verifies rejection flash, the row leaving the queue, the cause balance untouched (35.0), and carol seeing the row as rejected |
| `test_uat_1_13_a_decided_row_cannot_be_decided_again()` | `admin_client`, `seed`, `query` → `POST …/decision` twice | Verifies the second decision flashes "This submission has already been reviewed", the cause is not double-charged (still 27.0), and the original status stands |

### 4.4 Workflow 3 — Redeem Progress (UAT 1.14–1.18) — `tests/integration/test_uat_flows.py`

| Test | Dependencies | Description |
|---|---|---|
| `test_uat_1_14_rewards_grid_marks_what_bob_can_afford()` | `student_client`, `seed` → `GET /rewards` (rewards router, redeem service) | Verifies Total Hours: 6, all four cards, a Select link for affordable rewards and disabled "Needs N hours" buttons for the rest |
| `test_uat_1_15_redeem_spends_hours()` | `student_client`, `seed` → `GET /rewards/{id}/redeem`, `POST /rewards/{id}/redeem` | Verifies the "Are you sure?" screen with go-back, then Confirm flashes success and Total Hours drops 6 → 1 |
| `test_uat_1_16_unaffordable_reward_is_refused()` | `student_client`, `seed` → `GET /rewards/{movie}/redeem` | Verifies Movie Night (12 hrs) flashes "You need 6 more hours" and the total stays 6 |
| `test_uat_1_17_charity_conversion_records_the_donation()` | `student_client`, `seed`, `query` → `GET /rewards/{charity}/redeem`, `GET …/confirm`, `POST …/redeem` | Verifies the charity screen (Max, Red Cross), the confirmation, and that the recorded redemption keeps `charity_id` with Total Hours 6 → 4 |
| `test_uat_1_18_charity_bad_input_is_refused_and_nothing_deducted()` | `student_client`, `seed`, `query` → `GET …/confirm` ×3, `GET /rewards` | Verifies 0 hours, a missing charity and exceeding the balance each flash their message, Total Hours stays 6, and no redemption row exists |

## 5. Exit criteria

- `python -m pytest tests/integration -q` → **18 passed**.
- Every UAT case is covered by exactly one integration test.
- Evidence: one screenshot per test in the Test Reporting section of the
  final report PDF.
