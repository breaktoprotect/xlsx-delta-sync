import os
import re
from pathlib import Path
from app.data_sync.diff_report import generate_diff_report


def test_generate_diff_report(tmp_path):
    # --- Arrange ---
    old_rows = [
        {"Record ID": "REC-001", "Description": "A", "Owner": "Alice"},
        {"Record ID": "REC-002", "Description": "B", "Owner": "Bob"},
        {"Record ID": "REC-003", "Description": "C", "Owner": "Chris"},
    ]

    new_rows = [
        {"Record ID": "REC-001", "Description": "A", "Owner": "Alice"},  # unchanged
        {"Record ID": "REC-002", "Description": "Updated", "Owner": "Bob"},  # updated
        {"Record ID": "REC-004", "Description": "New entry", "Owner": "Dan"},  # added
    ]

    column_mapping = {
        "Description": "Description",
        "Owner": "Owner",
    }

    # --- Act ---
    log_path = generate_diff_report(
        old_rows=old_rows,
        new_rows=new_rows,
        unique_id_col="Record ID",
        column_mapping=column_mapping,
        output_dir=tmp_path,
    )

    # --- Assert ---
    assert Path(log_path).exists(), "Log file should be created"
    content = Path(log_path).read_text(encoding="utf-8")

    # Verify updated record diff direction
    assert "[UPDATED] REC-002" in content
    assert "Description: 'B' → 'Updated'" in content  # old → new

    # Verify added record detected
    assert "[ADDED] REC-004" in content
    assert "Description: 'New entry'" in content

    # Ensure file format readability (indented and arrow present)
    assert re.search(r"\s{4}.+→.+", content), "Should contain indented diff lines"

    print("\n--- DIFF REPORT CONTENT ---\n")
    print(content)
