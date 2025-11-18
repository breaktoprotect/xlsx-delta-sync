import re
from pathlib import Path
from app.data_sync.diff_report import generate_diff_report


def test_generate_diff_report(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.data_sync.diff_report.LOG_PATH",
        str(tmp_path / "sync_diff_{timestamp}.log"),
    )

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
    timestamp = "TEST1234"
    log_path = generate_diff_report(
        timestamp=timestamp,
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


def test_diff_report_respects_tgt_columns(tmp_path, monkeypatch):
    """
    Ensure diff_report compares old vs new using TGT column names (col_new),
    not SOT column names (col_old). Previously this caused old_val = ''.
    """
    monkeypatch.setattr(
        "app.data_sync.diff_report.LOG_PATH",
        str(tmp_path / "sync_diff_{timestamp}.log"),
    )
    # old TGT row has TGT column names only
    old_rows = [
        {"Record ID": "REC-100", "Record Name": "Original Name"},
    ]

    # new TGT row shows updated value
    new_rows = [
        {"Record ID": "REC-100", "Record Name": "Updated Name"},
    ]

    # column_mapping uses SOT → TGT
    # SOT column "REC Name" does NOT exist in old_rows
    column_mapping = {"REC Name": "Record Name"}

    timestamp = "TEST5678"
    log_path = generate_diff_report(
        timestamp=timestamp,
        old_rows=old_rows,
        new_rows=new_rows,
        unique_id_col="Record ID",
        column_mapping=column_mapping,
        output_dir=tmp_path,
    )

    content = Path(log_path).read_text(encoding="utf-8")

    # --- Assertions ---

    # Must detect an update
    assert "[UPDATED] REC-100" in content

    # MUST show correct old value, not empty ''
    assert (
        "Record Name: 'Original Name' → 'Updated Name'" in content
    ), "Old value was incorrectly shown as '' before the fix"

    # Must NOT show the broken version
    assert "Record Name: '' → 'Updated Name'" not in content
