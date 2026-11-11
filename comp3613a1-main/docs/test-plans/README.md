# Test Plans — Student Awards (Assignment 2)

This folder holds the three test plans required by the assignment, plus the
guide for running everything and capturing the screenshots your report needs.

| Plan | File |
|---|---|
| User Acceptance Test (UAT) report — TPED format | [01-user-acceptance-test-plan.md](01-user-acceptance-test-plan.md) · Word: [TPED-User-Acceptance-Test-Report.docx](TPED-User-Acceptance-Test-Report.docx) |
| Unit test plan (Unit Test / Input / Expected Output) | [02-unit-test-plan.md](02-unit-test-plan.md) · Word: [Unit-Test-Plan.docx](Unit-Test-Plan.docx) |
| Integration test plan (Test / Dependencies / Description) | [03-integration-test-plan.md](03-integration-test-plan.md) · Word: [Integration-Test-Plan.docx](Integration-Test-Plan.docx) |

The `.docx` files are generated from the markdown tables:

```bash
python scripts/generate_uat_docx.py        # TPED UAT report
python scripts/generate_test_plan_docx.py  # unit + integration plans
```

Re-run them after editing the markdown. The UAT docx's Tester Name / Position /
Date header and all Pass/Fail boxes are intentionally blank for you to fill in
Word.

## Entry criteria (before any test run)

```bash
# from the project root, venv activated
python manage.py init     # ⚠ drops and re-seeds the database — run once before testing
python manage.py run      # serves http://127.0.0.1:5000
```

Demo credentials: `bob/bobpass` (student), `carol/carolpass` (student),
`admin/adminpass` (admin).

## Running the automated tests

```bash
python -m pytest tests/unit -q           # unit suite — isolated, no database
python -m pytest tests/integration -q    # integration suite — TestClient + temp DB
python -m pytest -q                      # everything (33 tests)
```

Pytest creates its own temporary database (`tests/conftest.py` sets
`DATABASE_URI` before the app is imported), so these commands **never** touch
your `database.db`. Green at time of writing: **15 unit + 18 integration = 33 passed**.

Both suites are derived from the UAT plan: every test is named
`test_uat_1_…` after the UAT case it covers (one screenshot each).

## Running the Postman collection

The server must be running (`python manage.py run`) and the database freshly
seeded (`python manage.py init`) — the collection submits and reviews real
data, so a second run against a dirty database may show different totals.

```bash
cd postman
npx newman run StudentAwards.postman_collection.json
```

Expected tail (verified):

```text
┌─────────────────────────┬───────────────────┬──────────────────┐
│                         │     executed      │       failed     │
│              requests   │                29 │                0 │
│           assertions    │                95 │                0 │
└─────────────────────────┴───────────────────┴──────────────────┘
```

Newman is invoked through `npx` (Node.js required); the collection file is
`postman/StudentAwards.postman_collection.json` and its upload fixture is
`postman/fixtures/participation-form.pdf`.

## Screenshots to capture for the Test Reporting section

1. **UAT:** one screenshot per test case in the TPED report — 18 cases
   (paste into `TPED-User-Acceptance-Test-Report.docx` next to its Pass/Fail box).
2. **Unit:** terminal with `python -m pytest tests/unit -q` → `15 passed`,
   then one screenshot per test (15) — each is named after its UAT case.
3. **Integration:** terminal with `python -m pytest tests/integration -q` →
   `18 passed`, then one screenshot per test (18).
4. **Full suite:** terminal with `python -m pytest -q` → `33 passed`.
5. **Postman/Newman:** the summary table above (29 requests, 95 assertions, 0 failed).
6. **Postman runner (optional):** the collection run inside the Postman app.

## Notes

- The UAT plan references the Assignment 1 wireframes in `docs/report.md` /
  `docs/wireframes/` — keep it open while testing.
- If a test fails, record it in the plan's defect log, fix, then re-run and
  re-screenshot. Do not edit the expected results to match a bug.
- `python manage.py init` is destructive (drops tables). Never run it against
  a database you need to keep.
