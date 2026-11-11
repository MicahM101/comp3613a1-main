"""Generate the TPED User Acceptance Test Report (.docx) for Assignment 2.

Layout mirrors the TPED template: title, tester header table, then one
table per test case with Pre-conditions / Test Steps / Test Criteria /
Success (Pass|Fail) columns. Steps and criteria are pre-filled; the tester
header and Pass/Fail boxes are left blank.

Run from the repo root:  python scripts/generate_uat_docx.py
"""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

OUT = Path(__file__).resolve().parents[1] / "docs" / "test-plans" / "TPED-User-Acceptance-Test-Report.docx"

# (case, preconditions, steps[], criteria[]) — mirrors
# docs/test-plans/01-user-acceptance-test-plan.md (v2.0, 18 cases)
CASES = [
    ("1.1 Test Login",
     ["Account exists (bob / bobpass); logged out"],
     ["Navigate to the login page",
      "Fill the form with valid data",
      "Press the login button"],
     ["User is directed to the account page",
      'User can see their name in the navbar ("Welcome, bob")',
      "Recent Cause Contributions and the submission tracker are shown",
      "The landing page now offers Open app / Sign out"]),

    ("1.2 Test Login Failure",
     ["Account exists (bob / bobpass); logged out"],
     ["On the login page enter a correct username with a wrong password",
      "Press the login button"],
     ['An error message is flashed ("Incorrect username or password")',
      "No session is created - protected pages stay blocked"]),

    ("1.3 Test Register",
     ["None (logged out); a unique username is available"],
     ["Navigate to the Register page",
      "Fill the form with a unique username, valid email and password",
      "Press the register button",
      "Log in with the new account"],
     ["User is redirected to the login page",
      "Logging in with the new account succeeds",
      "Registering an existing username shows a clear error"]),

    ("1.4 Test Logout",
     ["Logged in as bob"],
     ["Press Sign out on the landing page (top right)",
      "Try to open the account page again in the same browser"],
     ["User is sent back to the login page",
      "Session cookie is cleared",
      "The old account URL no longer grants access"]),

    ("1.5 Test Open Submit Hours Form (Wireframe: Workflow 1)",
     ["Logged in as bob (student account)"],
     ["On the Account page press the Submit Hours button",
      "Observe the Service Hours Submission Form"],
     ["The form opens with a Choose the cause you served dropdown listing the available causes",
      "An Enter hours served field is present",
      "A date and Start Time (hour/minute/AM-PM) picker are present",
      "An Upload Signed Participation Form file picker is present",
      "Cancel and Submit buttons are shown"]),

    ("1.6 Test Submit Hours - valid with document (Wireframe: Workflow 1)",
     ["Logged in as bob; at least one cause has hours available; a PDF is ready to upload"],
     ["Choose a cause, enter hours served, date and start time",
      "Upload the signed participation form (PDF)",
      "Press Submit",
      'On the "Are you sure you want to submit?" screen check the details',
      "Press Confirm"],
     ["The confirmation screen repeats the cause, hours, date, start time and file name",
      "After Confirm the user returns to the Account page with a success message",
      "The new row appears in the tracker with status Pending",
      "The uploaded document is linked to the submission"]),

    ("1.7 Test Submit Hours - invalid input (Wireframe: Workflow 1)",
     ["Logged in as bob"],
     ["Submit the form with 0 hours",
      "Submit the form with more hours than the cause has available",
      "Submit the form with an unsupported file type (e.g. .exe)"],
     ['0 hours is refused with the message "Hours served must be more than zero."',
      "Exceeding the cause's balance is refused with a message naming the available hours",
      'An unsupported file type is refused with "Unsupported file type"',
      "Nothing is stored in any of the three cases"]),

    ("1.8 Test Cancel Submission (Wireframe: Workflow 1)",
     ["Logged in as bob; the Submit Hours form is open"],
     ["Fill in some of the form",
      "Press Cancel"],
     ["The user returns to the Account page",
      "No submission row was created"]),

    ("1.9 Test Admin Queue and Search (Wireframe: Workflow 2)",
     ["Pending submissions exist; logged in as admin / adminpass"],
     ["Log in as admin and open Submissions",
      "Observe the queue",
      'Type a cause name (e.g. "Math") into Search by Student ID, Submission ID, or Cause',
      "Clear the search"],
     ['"Recent Submission Requests" lists every pending row (Submission ID, Cause, Student ID, Hours, Review button)',
      "Approved/rejected rows are not listed",
      "The search narrows the list to matching rows with a result count",
      "Clearing the search restores the full queue"]),

    ("1.10 Test Review Submission Detail (Wireframe: Workflow 2)",
     ["Logged in as admin; a pending row exists"],
     ["Press Review on a queue row",
      "Observe the review card",
      "Click the participation document link"],
     ["The card shows the student (ID, name), Cause Served, Hours Served, Date and Start Time",
      "The uploaded participation form link is shown and opens/downloads the file",
      "Reject and Approve buttons are present"]),

    ("1.11 Test Approve Hours (Wireframe: Workflow 2)",
     ["Logged in as admin; a pending row exists"],
     ["Press Approve on the review card",
      'On "Approve student\'s Hours?" press go back, then Approve again',
      "Confirm with Approve"],
     ['"go back" returns to the review card without changing anything',
      "After approval a success message appears",
      "The row leaves the pending queue",
      "The cause's available hours decrease by the approved hours",
      "The student sees the row as Approved on their Account page"]),

    ("1.12 Test Reject Hours (Wireframe: Workflow 2)",
     ["Logged in as admin; a pending row exists"],
     ["Press Reject on the review card",
      'On "Reject student\'s Hours?" confirm with Reject'],
     ["A success message appears",
      "The row leaves the pending queue",
      "The cause's available hours are unchanged by a rejection",
      "The student sees the row as Rejected on their Account page"]),

    ("1.13 Test Re-review Refused (Wireframe: Workflow 2)",
     ["Logged in as admin; a row has already been approved or rejected"],
     ["Attempt to approve (or reject) the same row again"],
     ['The app refuses with "This submission has already been reviewed."',
      "The original status and the cause's balance are unchanged (no double counting)"]),

    ("1.14 Test Rewards Grid (Wireframe: Workflow 3)",
     ["Logged in as bob with a known approved-hours balance"],
     ["Open Rewards in the navbar",
      "Compare each card's Select button and hours with the total"],
     ["Every reward card is shown with its name and hours cost",
      "Total Hours matches the student's approved balance",
      "Rewards costing more than the total are visibly marked / unselectable in effect",
      "The total stays visible on the page"]),

    ("1.15 Test Redeem Reward (Wireframe: Workflow 3)",
     ["Logged in as bob; a reward costs <= his total (e.g. Library Waiver = 5, total = 6)"],
     ['Press Select on an affordable reward',
      'On the "Are you sure?" screen press go back, then Select again',
      "Confirm with Confirm"],
     ["The confirmation shows the reward and the hours to be spent",
      '"go back" returns to the grid without spending hours',
      "After Confirm a success message appears",
      "Total Hours drops by the reward's cost",
      "The redemption is recorded in the student's history"]),

    ("1.16 Test Redeem Unaffordable Reward (Wireframe: Workflow 3)",
     ["Logged in as bob; at least one reward costs more than his total (e.g. Movie Night = 12 > 6)"],
     ["Attempt to Select/redeem the unaffordable reward"],
     ["The app refuses with a message naming the hours still needed",
      "The user stays on / returns to the grid",
      "Total Hours is unchanged"]),

    ("1.17 Test Charity Conversion (Wireframe: Workflow 3, middle screen)",
     ["Logged in as bob; the Charity Conversion reward exists with partner charities"],
     ["Press Select on Charity Conversion",
      "Enter the hours to convert (within Max)",
      "Choose a partner charity from the dropdown",
      'Press Confirm, then confirm the "Are you sure?" screen'],
     ['The screen asks "How many hours would you like to convert…" and shows Max = the student\'s balance',
      "The partner charity list is shown (Red Cross, Habits for Humanity, ...)",
      "The final confirmation shows hours spent and the chosen charity",
      "Total Hours drops by the converted hours and the donation is recorded with its partner"]),

    ("1.18 Test Charity Conversion - invalid input (Wireframe: Workflow 3, middle screen)",
     ["Logged in as bob; Charity Conversion screen open"],
     ["Confirm with 0 hours",
      "Confirm with hours but no partner charity",
      "Confirm with more hours than the Max"],
     ['0 hours is refused with "Choose more than zero hours."',
      'A missing partner charity is refused with "Choose a partner charity."',
      "Exceeding the balance is refused with a message naming the available hours",
      "Nothing is deducted in any of the three cases"]),
]

BOX = "\u2610 "  # ballot box


def add_bullets(cell, items, first=True):
    """Write checkbox lines into a cell, one paragraph per item."""
    for i, item in enumerate(items):
        p = cell.paragraphs[0] if (first and i == 0) else cell.add_paragraph()
        p.paragraph_format.space_after = Pt(2)
        run = p.add_run(f"{BOX}{item}")
        run.font.size = Pt(9)


def set_cell_text(cell, text, bold=False, size=9):
    p = cell.paragraphs[0]
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)


def build():
    doc = Document()

    # Base style
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    title = doc.add_heading("TPED User Acceptance Test Report", level=0)
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT

    doc.add_paragraph("Project: Student Awards — COMP 3613 Assignment 2 (Test Reporting)")

    # --- Tester header table (left blank) ---
    hdr = doc.add_table(rows=2, cols=3)
    hdr.style = "Table Grid"
    for i, label in enumerate(
        ["Tester Name", "Tester Position", "Date of Test (DD/MM/YYYY)"]
    ):
        cell = hdr.rows[0].cells[i]
        set_cell_text(cell, label, bold=True, size=10)
        # blank answer cell below
        hdr.rows[1].cells[i].paragraphs[0].add_run(" ")

    doc.add_paragraph()

    # --- One table per test case ---
    for case, pre, steps, criteria in CASES:
        p = doc.add_paragraph()
        run = p.add_run(case)
        run.bold = True
        run.font.size = Pt(11)

        table = doc.add_table(rows=1, cols=4)
        table.style = "Table Grid"

        headers = ["Pre-conditions", "Test Steps", "Test Criteria",
                   "Success (indicate with a \u2713)"]
        for i, h in enumerate(headers):
            set_cell_text(table.rows[0].cells[i], h, bold=True, size=9)

        row = table.add_row()
        add_bullets(row.cells[0], pre)
        add_bullets(row.cells[1], steps)
        add_bullets(row.cells[2], criteria)

        # Success cell: nested Pass | Fail table with blank checkboxes
        succ = row.cells[3]
        succ.paragraphs[0].add_run(" ").font.size = Pt(9)
        nested = succ.add_table(rows=2, cols=2)
        nested.style = "Table Grid"
        set_cell_text(nested.rows[0].cells[0], "Pass", bold=True, size=9)
        set_cell_text(nested.rows[0].cells[1], "Fail", bold=True, size=9)
        for c in nested.rows[1].cells:
            c.paragraphs[0].add_run(BOX).font.size = Pt(9)

        doc.add_paragraph()  # spacer

    doc.save(OUT)
    print(f"Wrote {OUT} ({len(CASES)} test cases)")


if __name__ == "__main__":
    build()
