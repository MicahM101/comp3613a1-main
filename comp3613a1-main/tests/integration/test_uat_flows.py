"""Integration tests — one per UAT case (docs/test-plans/01-...).

Each test walks the full request path (router → service → repository →
template) for a single TPED case, so a screenshot of the passing test
maps 1:1 to a row of the UAT report.

Run:  python -m pytest tests/integration -q
"""

import re

from app.models.reward import HoursRedemption
from app.models.submission import Submission, VolunteerCause
from sqlmodel import select

from tests.conftest import login

VALID_UPLOAD = ("bob-form.pdf", b"%PDF-1.4 signed participation form",
                "application/pdf")


def form_data(seed, **overrides):
    data = {
        "cause_id": str(seed["causes"]["turtles"]),
        "hours": "5",
        "served_on": "2026-10-05",
        "time_hour": "09",
        "time_minute": "30",
        "meridiem": "AM",
    }
    data.update({k: str(v) for k, v in overrides.items()})
    return data


def count_submissions(query):
    return len(query(lambda s: s.exec(select(Submission)).all()))


# --- UAT 1.1 – 1.4: authentication ------------------------------------------


def test_uat_1_1_login_lands_on_the_account_page(client, seed):
    response = client.post(
        "/login", data={"username": "bob", "password": "bobpass"}
    )

    assert response.status_code == 200
    assert "Welcome, bob" in response.text
    assert "Recent Cause Contributions" in response.text
    assert "Hours Earned" in response.text
    # the landing page now offers the signed-in actions
    landing = client.get("/")
    assert "Sign out" in landing.text
    assert "Open app" in landing.text


def test_uat_1_2_wrong_password_grants_no_session(client, seed):
    response = client.post(
        "/login", data={"username": "bob", "password": "nope"}
    )

    assert "Incorrect username or password" in response.text
    assert client.get("/app").status_code == 401   # no session was created


def test_uat_1_3_register_then_login_and_duplicate_refused(client, seed):
    response = client.post(
        "/register",
        data={"username": "dave", "email": "dave@example.com",
              "password": "davepass"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].endswith("/login")
    assert "Registration completed!" in client.get("/login").text

    duplicate = client.post(
        "/register",
        data={"username": "bob", "email": "other@example.com",
              "password": "x"},
        follow_redirects=False,
    )
    assert duplicate.status_code == 303
    assert "Username or email already exists" in client.get("/register").text

    ok = client.post(
        "/login", data={"username": "dave", "password": "davepass"}
    )
    assert "Welcome, dave" in ok.text


def test_uat_1_4_logout_clears_the_session(student_client):
    out = student_client.get("/logout", follow_redirects=False)

    assert out.status_code == 303
    assert out.headers["location"].endswith("/login")
    assert student_client.get("/app").status_code == 401   # cookie is gone


# --- UAT 1.5 – 1.8: Workflow 1 — Submit Hours -------------------------------


def test_uat_1_5_submit_form_lists_every_wireframe_field(student_client):
    response = student_client.get("/app/hours/new")

    assert response.status_code == 200
    assert "Service Hours Submission Form" in response.text
    assert "Choose the cause you served" in response.text
    assert "Save the Turtles!" in response.text
    assert "Math Help Center" in response.text
    assert 'name="hours"' in response.text
    assert 'name="served_on"' in response.text
    assert "Start Time" in response.text
    assert 'type="file"' in response.text
    assert '/app">Cancel' in response.text            # absolute url_for
    assert 'type="submit">Submit' in response.text


def test_uat_1_6_valid_submission_reaches_the_tracker(
    student_client, seed, query, uploads_dir
):
    preview = student_client.post(
        "/app/hours/new", data=form_data(seed), files={"document": VALID_UPLOAD}
    )

    assert preview.status_code == 200
    assert "Are you sure you want to submit?" in preview.text
    assert "Save the Turtles!" in preview.text
    assert "2026-10-05" in preview.text
    assert "09:30 AM" in preview.text
    assert "bob-form.pdf" in preview.text

    document_path = re.search(
        r'name="document_path" value="([^"]+)"', preview.text
    ).group(1)
    confirm = student_client.post("/app/hours/confirm", data={
        "cause_id": str(seed["causes"]["turtles"]),
        "hours": "5",
        "date_completed": "2026-10-05",
        "start_time": "09:30 AM",
        "document_path": document_path,
        "document_name": "bob-form.pdf",
    })

    assert confirm.status_code == 200                  # followed to /app
    assert "Your volunteer hours have been submitted successfully." in confirm.text
    assert "state-pending" in confirm.text
    # the document was stored under the test uploads folder
    assert (uploads_dir / document_path.rsplit("/", 1)[-1]).is_file()
    # the row is in the database, waiting on an admin
    row = query(
        lambda s: s.exec(
            select(Submission).where(Submission.document_path == document_path)
        ).one()
    )
    assert row.state == "pending"
    assert row.original_document_name == "bob-form.pdf"


def test_uat_1_7_invalid_input_creates_nothing(
    student_client, seed, query, uploads_dir
):
    before = count_submissions(query)

    zero = student_client.post(
        "/app/hours/new", data=form_data(seed, hours="0"),
        files={"document": VALID_UPLOAD},
    )
    assert "Hours served must be more than zero." in zero.text

    too_many = student_client.post(
        "/app/hours/new", data=form_data(seed, hours="999"),
        files={"document": VALID_UPLOAD},
    )
    assert "exceed the total available" in too_many.text

    bad_file = student_client.post(
        "/app/hours/new", data=form_data(seed),
        files={"document": ("malware.exe", b"MZ\x90", "application/octet-stream")},
    )
    assert "Unsupported file type" in bad_file.text

    assert count_submissions(query) == before


def test_uat_1_8_cancel_returns_without_creating_a_row(
    student_client, seed, query
):
    before = count_submissions(query)

    form = student_client.get("/app/hours/new")
    assert '/app">Cancel' in form.text                # absolute url_for

    account = student_client.get("/app")
    assert account.status_code == 200
    assert count_submissions(query) == before


# --- UAT 1.9 – 1.13: Workflow 2 — Verify Hours ------------------------------


def test_uat_1_9_queue_lists_pending_only_and_searches(admin_client, seed):
    queue = admin_client.get("/admin")

    assert queue.status_code == 200
    assert "Recent Submission Requests" in queue.text
    assert "Search by Student ID, Submission ID or Cause" in queue.text
    assert f'{seed["submissions"]["pending_bob"]:04d}' in queue.text
    assert f'{seed["submissions"]["pending_carol"]:04d}' in queue.text
    # approved / rejected rows never appear
    assert f'{seed["submissions"]["approved"]:04d}' not in queue.text
    assert f'{seed["submissions"]["rejected_carol"]:04d}' not in queue.text

    found = admin_client.get("/admin", params={"q": "Math"})
    assert "Math Help Center" in found.text
    assert "Save the Turtles!" not in found.text
    assert "1 result" in found.text

    cleared = admin_client.get("/admin")
    assert "Math Help Center" in cleared.text
    assert "Save the Turtles!" in cleared.text


def test_uat_1_10_review_card_shows_every_detail(admin_client, seed):
    sid = seed["submissions"]["pending_bob"]
    response = admin_client.get(f"/admin/submissions/{sid}")

    assert response.status_code == 200
    assert "ID: 1" in response.text                   # bob's student id
    assert ">bob<" in response.text
    assert "Math Help Center" in response.text
    assert "Hours Served:" in response.text
    assert "2026-10-05" in response.text
    assert "02:30 PM" in response.text
    assert "bob-pending.pdf" in response.text         # document link
    assert f'/admin/submissions/{sid}/decision/rejected"' in response.text
    assert f'/admin/submissions/{sid}/decision/approved"' in response.text


def test_uat_1_11_approve_moves_the_row_and_spends_cause_hours(
    admin_client, student_client, seed, query
):
    sid = seed["submissions"]["pending_bob"]

    confirm = admin_client.get(f"/admin/submissions/{sid}/decision/approved")
    assert "Approve student's Hours?" in confirm.text
    assert f'/admin/submissions/{sid}"' in confirm.text   # go back

    done = admin_client.post(
        f"/admin/submissions/{sid}/decision", data={"state": "approved"}
    )
    assert "Submission approved successfully." in done.text

    queue = admin_client.get("/admin")
    assert f"{sid:04d}" not in queue.text             # left the queue

    cause = query(lambda s: s.get(VolunteerCause, seed["causes"]["math_help"]))
    assert cause.hours_available == 27.0              # 30 - 3 approved hours

    page = student_client.get("/app")                 # bob sees it approved
    assert "state-badge state-approved" in page.text
    assert "state-badge state-pending" not in page.text  # his only pending row


def test_uat_1_12_reject_removes_the_row_but_spends_nothing(
    admin_client, client, seed, query
):
    sid = seed["submissions"]["pending_carol"]

    confirm = admin_client.get(f"/admin/submissions/{sid}/decision/rejected")
    assert "Reject student's Hours?" in confirm.text

    done = admin_client.post(
        f"/admin/submissions/{sid}/decision", data={"state": "rejected"}
    )
    assert "Submission rejected successfully." in done.text

    queue = admin_client.get("/admin")
    assert f"{sid:04d}" not in queue.text

    cause = query(lambda s: s.get(VolunteerCause, seed["causes"]["turtles"]))
    assert cause.hours_available == 35.0              # untouched by a rejection

    login(client, "carol")                            # carol sees it rejected
    page = client.get("/app")
    assert "state-badge state-rejected" in page.text
    assert "state-badge state-pending" not in page.text  # her only pending row


def test_uat_1_13_a_decided_row_cannot_be_decided_again(
    admin_client, seed, query
):
    sid = seed["submissions"]["pending_bob"]
    admin_client.post(
        f"/admin/submissions/{sid}/decision", data={"state": "approved"}
    )

    again = admin_client.post(
        f"/admin/submissions/{sid}/decision", data={"state": "rejected"}
    )
    assert "This submission has already been reviewed." in again.text

    cause = query(lambda s: s.get(VolunteerCause, seed["causes"]["math_help"]))
    assert cause.hours_available == 27.0              # not double-counted
    row = query(lambda s: s.get(Submission, sid))
    assert row.state == "approved"                    # original status kept


# --- UAT 1.14 – 1.18: Workflow 3 — Redeem Progress --------------------------


def test_uat_1_14_rewards_grid_marks_what_bob_can_afford(student_client, seed):
    response = student_client.get("/rewards")

    assert response.status_code == 200
    assert "Total Hours: 6" in response.text
    for name in ("Library Late-Fee Waiver", "Gym Day Pass",
                 "Movie Night Ticket", "Charity Conversion"):
        assert name in response.text
    # affordable: a Select link
    assert f'/rewards/{seed["rewards"]["waiver"]}/redeem">Select' \
        in response.text
    # unaffordable: visibly marked and disabled
    assert "Needs 8 hours" in response.text           # Gym Day Pass
    assert "Needs 12 hours" in response.text          # Movie Night Ticket
    assert "btn-select-disabled" in response.text


def test_uat_1_15_redeem_spends_hours(student_client, seed):
    wid = seed["rewards"]["waiver"]

    confirm = student_client.get(f"/rewards/{wid}/redeem")
    assert confirm.status_code == 200
    assert "Are you sure?" in confirm.text
    assert "Library Late-Fee Waiver" in confirm.text
    assert "Hours spent" in confirm.text
    assert "Hours left after" in confirm.text
    assert '/rewards">' in confirm.text              # go back to the grid

    done = student_client.post(f"/rewards/{wid}/redeem")
    assert "Redemption successful!" in done.text
    assert "Total Hours: 1" in done.text              # 6 - 5


def test_uat_1_16_unaffordable_reward_is_refused(student_client, seed):
    response = student_client.get(
        f"/rewards/{seed['rewards']['movie']}/redeem"
    )

    assert "You need 6 more hours for Movie Night Ticket." in response.text
    assert "Total Hours: 6" in response.text          # unchanged


def test_uat_1_17_charity_conversion_records_the_donation(
    student_client, seed, query
):
    cid = seed["rewards"]["charity_conversion"]
    red_cross = seed["charities"]["red_cross"]

    screen = student_client.get(f"/rewards/{cid}/redeem")
    assert "How many hours would you like to convert" in screen.text
    assert "Max: 6 hours" in screen.text
    assert "Red Cross" in screen.text

    quote = student_client.get(
        f"/rewards/{cid}/confirm", params={"hours": "2", "charity_id": red_cross}
    )
    assert "Are you sure?" in quote.text
    assert "Red Cross" in quote.text
    assert "Hours spent" in quote.text

    done = student_client.post(
        f"/rewards/{cid}/redeem",
        data={"hours": "2", "charity_id": red_cross},
    )
    assert "Redemption successful!" in done.text
    assert "Total Hours: 4" in done.text              # 6 - 2

    rows = query(lambda s: s.exec(select(HoursRedemption)).all())
    assert len(rows) == 1
    assert rows[0].charity_id == red_cross
    assert rows[0].hours_spent == 2.0


def test_uat_1_18_charity_bad_input_is_refused_and_nothing_deducted(
    student_client, seed, query
):
    cid = seed["rewards"]["charity_conversion"]
    red_cross = seed["charities"]["red_cross"]

    zero = student_client.get(
        f"/rewards/{cid}/confirm", params={"hours": "0", "charity_id": red_cross}
    )
    assert "Choose more than zero hours." in zero.text

    no_charity = student_client.get(
        f"/rewards/{cid}/confirm", params={"hours": "2"}
    )
    assert "Choose a partner charity." in no_charity.text

    over = student_client.get(
        f"/rewards/{cid}/confirm", params={"hours": "10", "charity_id": red_cross}
    )
    assert "You only have 6 hours available." in over.text

    grid = student_client.get("/rewards")
    assert "Total Hours: 6" in grid.text              # nothing deducted

    rows = query(lambda s: s.exec(select(HoursRedemption)).all())
    assert rows == []
