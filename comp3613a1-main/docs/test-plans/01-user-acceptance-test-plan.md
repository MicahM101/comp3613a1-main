# TPED User Acceptance Test Report — Student Awards

**Project:** Student Awards (COMP 3613 Assignment 1 app, extended for Assignment 2)
**Version:** 2.0 — November 2026

> Tester Name: *[blank]* · Tester Position: *[blank]* · Date of Test (DD/MM/YYYY): *[blank]*
> (Filled in on the Word version: [TPED-User-Acceptance-Test-Report.docx](TPED-User-Acceptance-Test-Report.docx))

## 1. Purpose

Confirm that the Student Awards application behaves the way its users expect
before the project is accepted. Every case below is derived from the three
workflow wireframes in `docs/wireframes/` (Submit Hours, Verify Hours,
Redeem Progress) plus the authentication needed to reach them.

## 2. Entry criteria

- `python manage.py init` has been run (demo data seeded).
- `python manage.py run` is serving the app at `http://127.0.0.1:5000`.
- The tester has the demo credentials and the wireframes open for comparison.

| Role | Username | Password |
|---|---|---|
| Student | `bob` | `bobpass` |
| Student | `carol` | `carolpass` |
| Admin | `admin` | `adminpass` |

> ⚠ `python manage.py init` resets the database — run it once before the UAT
> session so each test case starts from known demo data.

## 3. Test cases

Legend: each Test Steps / Test Criteria item has a checkbox; the tester ticks
criteria as observed and marks **Pass** or **Fail** at the end of the row.

### 1.1 Test Login

| Field | Content |
|---|---|
| **Pre-conditions** | Account exists (`bob` / `bobpass`); logged out |
| **Test Steps** | ☐ Navigate to the login page<br>☐ Fill the form with valid data<br>☐ Press the login button |
| **Test Criteria** | ☐ User is directed to the account page<br>☐ User can see their name in the navbar ("Welcome, bob")<br>☐ Recent Cause Contributions and the submission tracker are shown<br>☐ The landing page now offers **Open app** / **Sign out** |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.2 Test Login Failure

| Field | Content |
|---|---|
| **Pre-conditions** | Account exists (`bob` / `bobpass`); logged out |
| **Test Steps** | ☐ On the login page enter a correct username with a wrong password<br>☐ Press the login button |
| **Test Criteria** | ☐ An error message is flashed ("Incorrect username or password")<br>☐ No session is created — protected pages stay blocked |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.3 Test Register

| Field | Content |
|---|---|
| **Pre-conditions** | None (logged out); a unique username is available |
| **Test Steps** | ☐ Navigate to the Register page<br>☐ Fill the form with a unique username, valid email and password<br>☐ Press the register button<br>☐ Log in with the new account |
| **Test Criteria** | ☐ User is redirected to the login page<br>☐ Logging in with the new account succeeds<br>☐ Registering an existing username shows a clear error |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.4 Test Logout

| Field | Content |
|---|---|
| **Pre-conditions** | Logged in as `bob` |
| **Test Steps** | ☐ Press **Sign out** on the landing page (top right)<br>☐ Try to open the account page again in the same browser |
| **Test Criteria** | ☐ User is sent back to the login page<br>☐ Session cookie is cleared<br>☐ The old account URL no longer grants access |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.5 Test Open Submit Hours Form *(Wireframe: Workflow 1)*

| Field | Content |
|---|---|
| **Pre-conditions** | Logged in as `bob` (student account) |
| **Test Steps** | ☐ On the Account page press the **Submit Hours** button<br>☐ Observe the Service Hours Submission Form |
| **Test Criteria** | ☐ The form opens with a **Choose the cause you served** dropdown listing the available causes<br>☐ An **Enter hours served** field is present<br>☐ A **date** and **Start Time** (hour/minute/AM-PM) picker are present<br>☐ An **Upload Signed Participation Form** file picker is present<br>☐ Cancel and Submit buttons are shown |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.6 Test Submit Hours — valid with document *(Wireframe: Workflow 1)*

| Field | Content |
|---|---|
| **Pre-conditions** | Logged in as `bob`; at least one cause has hours available; a PDF is ready to upload |
| **Test Steps** | ☐ Choose a cause, enter hours served, date and start time<br>☐ Upload the signed participation form (PDF)<br>☐ Press **Submit**<br>☐ On the "Are you sure you want to submit?" screen check the details<br>☐ Press **Confirm** |
| **Test Criteria** | ☐ The confirmation screen repeats the cause, hours, date, start time and file name<br>☐ After Confirm the user returns to the Account page with a success message<br>☐ The new row appears in the tracker with status *Pending*<br>☐ The uploaded document is linked to the submission |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.7 Test Submit Hours — invalid input *(Wireframe: Workflow 1)*

| Field | Content |
|---|---|
| **Pre-conditions** | Logged in as `bob` |
| **Test Steps** | ☐ Submit the form with `0` hours<br>☐ Submit the form with more hours than the cause has available<br>☐ Submit the form with an unsupported file type (e.g. `.exe`) |
| **Test Criteria** | ☐ `0` hours is refused with the message "Hours served must be more than zero."<br>☐ Exceeding the cause's balance is refused with a message naming the available hours<br>☐ An unsupported file type is refused with "Unsupported file type"<br>☐ Nothing is stored in any of the three cases |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.8 Test Cancel Submission *(Wireframe: Workflow 1)*

| Field | Content |
|---|---|
| **Pre-conditions** | Logged in as `bob`; the Submit Hours form is open |
| **Test Steps** | ☐ Fill in some of the form<br>☐ Press **Cancel** |
| **Test Criteria** | ☐ The user returns to the Account page<br>☐ No submission row was created |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.9 Test Admin Queue and Search *(Wireframe: Workflow 2)*

| Field | Content |
|---|---|
| **Pre-conditions** | Pending submissions exist; logged in as `admin` / `adminpass` |
| **Test Steps** | ☐ Log in as admin and open **Submissions**<br>☐ Observe the queue<br>☐ Type a cause name (e.g. "Math") into **Search by Student ID, Submission ID, or Cause**<br>☐ Clear the search |
| **Test Criteria** | ☐ "Recent Submission Requests" lists every pending row (Submission ID, Cause, Student ID, Hours, Review button)<br>☐ Approved/rejected rows are not listed<br>☐ The search narrows the list to matching rows with a result count<br>☐ Clearing the search restores the full queue |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.10 Test Review Submission Detail *(Wireframe: Workflow 2)*

| Field | Content |
|---|---|
| **Pre-conditions** | Logged in as `admin`; a pending row exists |
| **Test Steps** | ☐ Press **Review** on a queue row<br>☐ Observe the review card<br>☐ Click the participation document link |
| **Test Criteria** | ☐ The card shows the student (ID, name), Cause Served, Hours Served, Date and Start Time<br>☐ The uploaded participation form link is shown and opens/downloads the file<br>☐ **Reject** and **Approve** buttons are present |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.11 Test Approve Hours *(Wireframe: Workflow 2)*

| Field | Content |
|---|---|
| **Pre-conditions** | Logged in as `admin`; a pending row exists |
| **Test Steps** | ☐ Press **Approve** on the review card<br>☐ On "Approve student's Hours?" press **go back**, then **Approve** again<br>☐ Confirm with **Approve** |
| **Test Criteria** | ☐ "go back" returns to the review card without changing anything<br>☐ After approval a success message appears<br>☐ The row leaves the pending queue<br>☐ The cause's available hours decrease by the approved hours<br>☐ The student sees the row as *Approved* on their Account page |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.12 Test Reject Hours *(Wireframe: Workflow 2)*

| Field | Content |
|---|---|
| **Pre-conditions** | Logged in as `admin`; a pending row exists |
| **Test Steps** | ☐ Press **Reject** on the review card<br>☐ On "Reject student's Hours?" confirm with **Reject** |
| **Test Criteria** | ☐ A success message appears<br>☐ The row leaves the pending queue<br>☐ The cause's available hours are **unchanged** by a rejection<br>☐ The student sees the row as *Rejected* on their Account page |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.13 Test Re-review Refused *(Wireframe: Workflow 2)*

| Field | Content |
|---|---|
| **Pre-conditions** | Logged in as `admin`; a row has already been approved or rejected |
| **Test Steps** | ☐ Attempt to approve (or reject) the same row again |
| **Test Criteria** | ☐ The app refuses with "This submission has already been reviewed."<br>☐ The original status and the cause's balance are unchanged (no double counting) |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.14 Test Rewards Grid *(Wireframe: Workflow 3)*

| Field | Content |
|---|---|
| **Pre-conditions** | Logged in as `bob` with a known approved-hours balance |
| **Test Steps** | ☐ Open **Rewards** in the navbar<br>☐ Compare each card's Select button and hours with the total |
| **Test Criteria** | ☐ Every reward card is shown with its name and hours cost<br>☐ **Total Hours** matches the student's approved balance<br>☐ Rewards costing more than the total are visibly marked / unselectable in effect<br>☐ The total stays visible on the page |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.15 Test Redeem Reward *(Wireframe: Workflow 3)*

| Field | Content |
|---|---|
| **Pre-conditions** | Logged in as `bob`; a reward costs ≤ his total (e.g. Library Waiver = 5, total = 6) |
| **Test Steps** | ☐ Press **Select** on an affordable reward<br>☐ On the "Are you sure?" screen press **go back**, then Select again<br>☐ Confirm with **Confirm** |
| **Test Criteria** | ☐ The confirmation shows the reward and the hours to be spent<br>☐ "go back" returns to the grid without spending hours<br>☐ After Confirm a success message appears<br>☐ Total Hours drops by the reward's cost<br>☐ The redemption is recorded in the student's history |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.16 Test Redeem Unaffordable Reward *(Wireframe: Workflow 3)*

| Field | Content |
|---|---|
| **Pre-conditions** | Logged in as `bob`; at least one reward costs more than his total (e.g. Movie Night = 12 > 6) |
| **Test Steps** | ☐ Attempt to Select/redeem the unaffordable reward |
| **Test Criteria** | ☐ The app refuses with a message naming the hours still needed<br>☐ The user stays on / returns to the grid<br>☐ Total Hours is unchanged |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.17 Test Charity Conversion *(Wireframe: Workflow 3, middle screen)*

| Field | Content |
|---|---|
| **Pre-conditions** | Logged in as `bob`; the Charity Conversion reward exists with partner charities |
| **Test Steps** | ☐ Press **Select** on Charity Conversion<br>☐ Enter the hours to convert (within Max)<br>☐ Choose a partner charity from the dropdown<br>☐ Press **Confirm**, then confirm the "Are you sure?" screen |
| **Test Criteria** | ☐ The screen asks "How many hours would you like to convert…" and shows **Max** = the student's balance<br>☐ The partner charity list is shown (Red Cross, Habits for Humanity, …)<br>☐ The final confirmation shows hours spent and the chosen charity<br>☐ Total Hours drops by the converted hours and the donation is recorded with its partner |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

### 1.18 Test Charity Conversion — invalid input *(Wireframe: Workflow 3, middle screen)*

| Field | Content |
|---|---|
| **Pre-conditions** | Logged in as `bob`; Charity Conversion screen open |
| **Test Steps** | ☐ Confirm with `0` hours<br>☐ Confirm with hours but **no** partner charity<br>☐ Confirm with more hours than the Max |
| **Test Criteria** | ☐ `0` hours is refused with "Choose more than zero hours."<br>☐ A missing partner charity is refused with "Choose a partner charity."<br>☐ Exceeding the balance is refused with a message naming the available hours<br>☐ Nothing is deducted in any of the three cases |
| **Success** | ☐ Pass &nbsp;&nbsp; ☐ Fail |

## 4. Exit criteria

- All 18 test cases executed; every case marked Pass (or re-run and passed).
- Evidence: one screenshot per case, pasted into the Test Reporting section of
  the final report PDF.
- Defects found: [none / list with severity].

## 5. Sign-off

| Role | Name | Date | Signature |
|---|---|---|---|
| Tester |  |  |  |
| Reviewer |  |  |  |
