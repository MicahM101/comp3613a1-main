"""Generate Word documents for the unit and integration test plans.

Reads the markdown plans in docs/test-plans/ and renders their tables as
.docx files, so edits to the markdown only need a re-run of this script.

Run from the repo root:
    python scripts/generate_test_plan_docx.py
"""

import re
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

DIR = Path(__file__).resolve().parents[1] / "docs" / "test-plans"

JOBS = [
    {
        "src": "02-unit-test-plan.md",
        "out": "Unit-Test-Plan.docx",
        "title": "Unit Test Plan — Student Awards",
        "headers": ("Unit Test", "Input", "Expected Output"),
    },
    {
        "src": "03-integration-test-plan.md",
        "out": "Integration-Test-Plan.docx",
        "title": "Integration Test Plan — Student Awards",
        "headers": ("Test", "Dependencies", "Description"),
    },
]


def split_row(line: str) -> list[str]:
    """Split a markdown table row into cells (leading/trailing pipes dropped)."""
    return [c.strip() for c in line.strip().strip("|").split("|")]


def is_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\s*\|?[\s:|-]+\|?\s*", line)) and "-" in line


def clean(text: str) -> str:
    """Turn markdown inline code/bold into plain text."""
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    return text


def parse_sections(path: Path, expected_headers: tuple[str, str, str]):
    """Yield (section_heading, rows) for each level-3 heading with one table."""
    lines = path.read_text(encoding="utf-8").splitlines()
    section = None
    rows: list[list[str]] = []
    in_table = False

    def flush():
        nonlocal rows
        if section and rows:
            yield section, rows
        rows = []

    for line in lines:
        if line.startswith("### "):
            yield from flush()
            section = clean(line[4:].strip())
            in_table = False
        elif line.startswith("## ") or line.startswith("# "):
            # leaving the table area entirely (next top-level section)
            if line.startswith("## "):
                yield from flush()
                section = None
        elif line.startswith("|") and section:
            if not in_table:
                # header row — confirm it matches the expected shape
                header = tuple(split_row(line))
                if header[:3] == expected_headers:
                    in_table = True
                continue
            if is_separator(line):
                continue
            cells = split_row(line)
            if len(cells) >= 3:
                rows.append([clean(c) for c in cells[:3]])
    yield from flush()


def write_docx(job: dict):
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    heading = doc.add_heading(job["title"], level=0)
    heading.alignment = WD_ALIGN_PARAGRAPH.LEFT

    src = DIR / job["src"]
    sections = list(parse_sections(src, job["headers"]))
    if not sections:
        raise SystemExit(f"No tables found in {src}")

    count = 0
    for section_title, rows in sections:
        # strip the " — file path" tail so the heading reads cleanly
        section_title = re.sub(r"\s+—\s+`?[^`]*`?$", "", section_title)
        h = doc.add_heading(section_title, level=1)
        for run in h.runs:
            run.font.size = Pt(13)

        table = doc.add_table(rows=1, cols=3)
        table.style = "Table Grid"
        for i, label in enumerate(job["headers"]):
            cell = table.rows[0].cells[i]
            run = cell.paragraphs[0].add_run(label)
            run.bold = True
            run.font.size = Pt(9)

        for row_data in rows:
            row = table.add_row()
            for i, value in enumerate(row_data):
                p = row.cells[i].paragraphs[0]
                p.paragraph_format.space_after = Pt(2)
                run = p.add_run(value)
                run.font.size = Pt(9)
                if i == 0:
                    run.bold = True
            count += 1

        doc.add_paragraph()

    out = DIR / job["out"]
    doc.save(out)
    print(f"Wrote {out} ({count} tests across {len(sections)} sections)")


def main():
    for job in JOBS:
        write_docx(job)


if __name__ == "__main__":
    main()
