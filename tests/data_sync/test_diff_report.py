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


def test_diff_report_does_not_log_unchanged_records(tmp_path, monkeypatch):
    """
    Ensure that records which have NOT changed between old_rows and new_rows
    are NOT logged as [UPDATED].
    """

    # Patch log path
    monkeypatch.setattr(
        "app.data_sync.diff_report.LOG_PATH",
        str(tmp_path / "sync_diff_{timestamp}.log"),
    )

    # Use TEST- prefix (required)
    monkeypatch.setattr(
        "app.data_sync.diff_report.UNIQUE_ID_PREFIX",
        "TEST-",
    )

    # --- Arrange ---
    old_rows = [
        {"Record ID": "TEST-001", "Description": "abc", "Owner": "Alice"},
        {"Record ID": "TEST-002", "Description": "def", "Owner": "Bob"},
    ]

    # new_rows has **no changes at all**
    new_rows = [
        {"Record ID": "TEST-001", "Description": "abc", "Owner": "Alice"},
        {"Record ID": "TEST-002", "Description": "def", "Owner": "Bob"},
    ]

    column_mapping = {
        "Description": "Description",
        "Owner": "Owner",
    }

    timestamp = "UNCHANGED_TEST"

    log_path = generate_diff_report(
        timestamp=timestamp,
        old_rows=old_rows,
        new_rows=new_rows,
        unique_id_col="Record ID",
        column_mapping=column_mapping,
        output_dir=tmp_path,
        valid_ids={"TEST-001", "TEST-002"},  # all valid
    )

    content = Path(log_path).read_text(encoding="utf-8")

    # --- Assert ---
    # Should NOT log updates for unchanged rows
    assert "[UPDATED] TEST-001" not in content
    assert "[UPDATED] TEST-002" not in content

    # Should output no differences
    assert "No differences found" in content


def test_diff_report_skips_ids_not_matching_prefix(tmp_path, monkeypatch):
    """
    Ensure that diff_report completely ignores rows whose Record ID does NOT
    start with UNIQUE_ID_PREFIX. They must NOT appear in UPDATED or ADDED.
    """

    # Patch log path
    monkeypatch.setattr(
        "app.data_sync.diff_report.LOG_PATH",
        str(tmp_path / "sync_diff_{timestamp}.log"),
    )

    # Enforce TEST- prefix
    monkeypatch.setattr(
        "app.data_sync.diff_report.UNIQUE_ID_PREFIX",
        "TEST-",
    )

    # --- Arrange ---
    old_rows = [
        {"Record ID": "TEST-001", "Description": "A"},  # valid
        {
            "Record ID": "BAD-111",
            "Description": "Old",
        },  # invalid prefix → MUST be ignored
    ]

    new_rows = [
        {"Record ID": "TEST-001", "Description": "Updated"},  # valid → should update
        {
            "Record ID": "BAD-111",
            "Description": "New",
        },  # invalid prefix → MUST be ignored
        {
            "Record ID": "BAD-222",
            "Description": "NewRow",
        },  # invalid prefix → MUST be ignored even in NEW block
    ]

    # Only TEST-001 is valid according to SOT
    valid_ids = {"TEST-001"}

    column_mapping = {"Description": "Description"}

    timestamp = "PREFIX_FILTER_TEST"

    # --- Act ---
    log_path = generate_diff_report(
        timestamp=timestamp,
        old_rows=old_rows,
        new_rows=new_rows,
        unique_id_col="Record ID",
        column_mapping=column_mapping,
        output_dir=tmp_path,
        valid_ids=valid_ids,
    )

    content = Path(log_path).read_text(encoding="utf-8")

    # --- Assert ---

    # UPDATED must contain only TEST-001
    assert "[UPDATED] TEST-001" in content
    assert "Description: 'A' → 'Updated'" in content

    # MUST NOT show UPDATED for invalid IDs
    assert "[UPDATED] BAD-111" not in content
    assert "Old" not in content  # its diff must not appear

    # MUST NOT show ADDED for invalid IDs
    assert "[ADDED] BAD-222" not in content
    assert "NewRow" not in content  # its fields must not appear

    # MUST NOT include any mention of invalid IDs at all
    assert "BAD-111" not in content
    assert "BAD-222" not in content
