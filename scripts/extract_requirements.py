"""Extract only N06/E2 and applicable shared rules from the course workbook."""
import argparse
import hashlib
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
GROUP, TOPIC = "N06", "E2"


def extract(path):
    workbook = openpyxl.load_workbook(path, data_only=False)
    sheets = {sheet.title: list(sheet.iter_rows(values_only=True)) for sheet in workbook.worksheets}
    required = {"HuongDan", "DeTai", "LinhKien", "MaTran_Chuong", "MocNopBai", "Rubric", "DangKy"}
    if not required.issubset(sheets):
        raise ValueError("Workbook is missing an expected course sheet")
    topic_row = next(index for index, row in enumerate(sheets["DeTai"], 1) if row[0] == TOPIC)
    registration_row = next(index for index, row in enumerate(sheets["DangKy"], 1) if row[0] == GROUP)
    registration = workbook["DangKy"]
    if registration.cell(registration_row, 2).value != TOPIC:
        raise ValueError("N06 is not registered for E2")
    member_rows = []
    for row in range(registration_row, registration.max_row + 1):
        if row > registration_row and registration.cell(row, 1).value:
            break
        if registration.cell(row, 5).value:
            member_rows.append(row)
    if len(member_rows) != 3:
        raise ValueError("Expected exactly three N06 members")
    lines = ["# CE339 — N06 / E2 requirements", "",
             f"Source: `{path.name}`; all {len(sheets)} sheets inspected.",
             f"Workbook SHA-256: `{hashlib.sha256(path.read_bytes()).hexdigest()}`.", "",
             "This file preserves the relevant workbook text. Suggested roles are not assignments.", "",
             "## Course component", "", "Source: HuongDan!A1:A2.", "",
             str(workbook["HuongDan"]["A1"].value), "", str(workbook["HuongDan"]["A2"].value), "",
             "## Group registration", "",
             f"Source: DangKy!A{registration_row}:I{member_rows[-1]}.", "",
             "| Member | Student ID | Email | Assigned role |", "| --- | --- | --- | --- |"]
    for row in member_rows:
        values = [registration.cell(row, column).value for column in (5, 4, 7, 6)]
        name, student, email, role = values
        student = str(int(student)) if isinstance(student, (float, int)) else str(student)
        lines.append(f"| {name} | {student} | {email or 'Not entered'} | {role or 'Not assigned'} |")
    lines += ["", f"Registered context: {registration.cell(registration_row, 3).value}."]
    for column, label in ((8, "Git repository"), (9, "Wokwi link")):
        links = sorted({str(registration.cell(row, column).value) for row in member_rows if registration.cell(row, column).value})
        lines += [f"{label}: {', '.join(links) if links else 'not entered'}."]
    lines += ["", "## Topic E2", ""]
    topic = workbook["DeTai"]
    for column in range(2, 15):
        label, text = topic.cell(4, column).value, topic.cell(topic_row, column).value
        if text is not None:
            coordinate = topic.cell(topic_row, column).coordinate
            lines += [f"### {label}", "", f"Source: DeTai!{coordinate}.", "", str(text), ""]
    component = workbook["LinhKien"]
    topic_column = next(c.column for c in component[4] if c.value == TOPIC)
    lines += ["## E2 component list", "", "Source: LinhKien, E2 column.", "",
              "| Component | Wokwi part | Requirement |", "| --- | --- | --- |"]
    for row in range(5, 21):
        marker = component.cell(row, topic_column).value
        if marker in ("X", "(x)"):
            lines.append(f"| {component.cell(row, 1).value} | `{component.cell(row, 2).value}` | {'Required' if marker == 'X' else 'Optional'} |")
    lines += ["", "## Applicable course rules", "", "Source: HuongDan!A5:B16.", ""]
    for row in range(5, 17):
        label, value = workbook["HuongDan"].cell(row, 1).value, workbook["HuongDan"].cell(row, 2).value
        lines += [f"### {label}", "", str(value), ""]
    lines += ["## Submission milestones", "", "Source: MocNopBai!A5:F8.", ""]
    for row in range(5, 9):
        values = [workbook["MocNopBai"].cell(row, c).value for c in range(1, 7)]
        label, when, weight, requirement, deliverable, assessment = values
        lines += [f"### {label} — {when} ({weight:.0%})", "", str(requirement), "",
                  f"Submission: {deliverable}", "", f"Assessment: {assessment}", ""]
    rubric = workbook["Rubric"]
    lines += ["## Grading", "", "Source: Rubric!A5:D14; D18/F18 contain the score formulas.", ""]
    for row in range(5, 9):
        lines.append(f"- {rubric.cell(row, 1).value}: maximum {rubric.cell(row, 3).value:g}. {rubric.cell(row, 2).value}. {rubric.cell(row, 4).value or ''}".rstrip())
    lines += ["", "Individual score = (M1 × 0.30 + M2 × 0.30 + M3 × 0.40) × oral-assessment factor.", ""]
    lines += ["The workbook rounds the weighted group score and then the individual score to two decimal places.", ""]
    for row in range(11, 15):
        lines.append(f"- {rubric.cell(row, 1).value:g}: {rubric.cell(row, 2).value}")
    matrix = workbook["MaTran_Chuong"]
    row = next(index for index, values in enumerate(sheets["MaTran_Chuong"], 1) if values[0] == TOPIC)
    lines += ["", "## E2 chapter matrix", "", f"Source: MaTran_Chuong!A{row}:Q{row}.", ""]
    for column in range(3, 16):
        marker = matrix.cell(row, column).value
        if marker in ("●", "○"):
            lines.append(f"- {matrix.cell(4, column).value}: {'core' if marker == '●' else 'also used'}.")
    workbook.close()
    return "\n".join(lines).rstrip() + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, default=ROOT / "DeTai_BTL_CE339_2026.xlsx")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "requirements.md")
    args = parser.parse_args()
    text = extract(args.workbook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(f"Saved N06/E2 requirements to {args.output}")


if __name__ == "__main__":
    main()
