# Unit Test Plan — Student Awards

**Project:** Student Awards (COMP 3613 Assignment 1 app, extended for Assignment 2)
**Prepared by:** [name], [student ID]
**Version:** 2.0 — November 2026

## 1. Purpose

Verify the **actions taken in the UAT cases** (see
[01-user-acceptance-test-plan.md](01-user-acceptance-test-plan.md), itself
derived from the three workflow wireframes) one service at a time, with all
dependencies (database, HTTP, file storage) replaced by in-memory fakes. Every
test names the UAT case it covers, so each screenshot maps to a UAT row.

## 2. Approach

- **Framework:** pytest (`python -m pytest tests/unit -q`) — 15 tests.
- **Isolation technique:** each test constructs the service under test with
  fake repositories from `tests/unit/fakes.py` — in-memory dictionaries
  implementing the same repository interface. No unit test touches SQLite or
  starts the web server.
- **Derivation rule:** only actions that appear in the UAT are tested
  (login, register, submit, review, redeem, charity conversion).

## 3. Entry criteria

- All production modules under test are importable.
- `tests/unit/fakes.py` provides fakes for user, cause, submission, review,
  reward, charity and redemption repositories.
- Command runs green: `python -m pytest tests/unit -q`.

## 4. Unit Test Plan

### 4.1 Authentication actions (UAT 1.1–1.3) — `tests/unit/test_uat_actions.py`

| Unit Test | Input | Expected Output |
|---|---|---|
| `test_uat_1_3_register_stores_a_hash_and_refuses_duplicates()` | `register_user("bob", "bob@example.com", "bobpass")` twice | First call stores a hash (`password != "bobpass"`); second raises `Exception("UNIQUE …")` |
| `test_uat_1_1_login_returns_a_token_with_id_and_role()` | `authenticate_user("bob", "bobpass")` | JWT decodes with `sub == "1"`, `role == "regular_user"`, `exp` present |
| `test_uat_1_2_login_rejects_a_wrong_password()` | `authenticate_user("bob", "wrongpass")`, `authenticate_user("nobody", "bobpass")` | Both return `None` (no session token) |

### 4.2 Submit-hours actions (UAT 1.5–1.8) — `tests/unit/test_uat_actions.py`

| Unit Test | Input | Expected Output |
|---|---|---|
| `test_uat_1_5_the_form_lists_the_causes_a_student_can_serve()` | `CauseService.list_causes()` over `[Math Help Center, Save the Turtles!]` | `["Math Help Center", "Save the Turtles!"]` — every cause, name order |
| `test_uat_1_7_hours_beyond_the_cause_are_refused()` | `check_hours_fit(cause_id=1, hours=10.0)` then `hours=999.0` (cause has 35.0) | First returns the cause; second raises `ValueError("…exceed the total available")` |
| `test_uat_1_6_7_only_allowed_document_types_are_stored(uploads_dir)` | Upload `forms/bob-form.pdf`, then `malware.exe` | PDF: path starts `/static/uploads/`, original name kept, file written; `.exe` raises `ValueError("Unsupported file type")` |
| `test_uat_1_6_a_confirmed_submission_is_recorded_as_pending()` | `record_submission(user=bob, cause 1, 5.0 hrs, 2026-10-05, 09:30 AM, doc)` | Row has `state == "pending"`, `admin_id is None`, correct document link; appears in `my_submissions(3)`; `total_hours_earned(3) == 0.0` (pending never counts) |

### 4.3 Admin review actions (UAT 1.9–1.13) — `tests/unit/test_uat_actions.py`

| Unit Test | Input | Expected Output |
|---|---|---|
| `test_uat_1_9_the_queue_lists_only_pending_requests_and_searches()` | `queue()` over pending/approved/rejected rows; `queue(search=…)` with `"math"`, `"turtles"`, `"1"` | Only the pending id is listed with cause + student; search matches by cause name and by ID |
| `test_uat_1_10_review_detail_carries_the_student_and_the_document()` | `review_detail(1)` (pending 5 hrs + approved 6 hrs) | Detail has student name, cause name, document path/name, `total_hours == 6.0` (approved only) |
| `test_uat_1_11_approving_records_the_admin_and_spends_cause_hours()` | `decide(state="approved")` on a 5-hr row, cause has 35.0 | `state == "approved"`, `admin_id` set, cause drops to 30.0, admin profile created |
| `test_uat_1_12_rejecting_leaves_the_cause_balance_alone()` | `decide(state="rejected")` on a 5-hr row, cause has 35.0 | `state == "rejected"`, cause still 35.0 |
| `test_uat_1_13_a_decided_submission_cannot_be_decided_again()` | `decide(state="rejected")` on an already-approved row | `ValueError("…already been reviewed")`; row state and `admin_id` unchanged (no double counting) |

### 4.4 Redeem / charity actions (UAT 1.14–1.18) — `tests/unit/test_uat_actions.py`

| Unit Test | Input | Expected Output |
|---|---|---|
| `test_uat_1_14_the_grid_flags_affordable_and_unaffordable_rewards()` | `grid(bob)` with Waiver 5 hrs / Gym 8 hrs, total 6.0 | `total == 6.0`; Waiver `affordable is True, needs == 0.0`; Gym `affordable is False, needs == 2.0` |
| `test_uat_1_15_16_redeeming_spends_hours_and_unaffordable_is_refused()` | `redeem(reward_id=1)` (5 hrs), then `start(reward_id=2)` (8 hrs with 1 left) | Redemption recorded with `hours_spent == 5.0`, balance drops to 1.0; second call raises `ValueError("…need 7 more hours")` |
| `test_uat_1_17_18_charity_conversion_records_hours_and_refuses_bad_input()` | `confirm/redeem` with `hours=None`, `0`, no charity, `10.0` (balance 6), then valid `hours=2, charity_id=1` | Each invalid input raises (`how many hours`, `more than zero`, `partner charity`, `only have 6 hours`) and writes nothing; valid call records `hours_spent == 2.0`, `charity_id == 1`, balance 4.0 |

## 5. Exit criteria

- `python -m pytest tests/unit -q` → **15 passed**.
- Every UAT case with a service-level action has at least one unit test.
- Evidence: one screenshot per test in the Test Reporting section of the
  final report PDF.
