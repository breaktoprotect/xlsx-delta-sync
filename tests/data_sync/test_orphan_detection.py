import pytest
from app.data_sync.orphan_detection import find_orphaned_records
from app.data_sync.orphan_detection import generate_orphan_report_to_log


def test_find_orphaned_records_basic(monkeypatch):
    """
    Basic orphan detection with explicit prefix validation.
    Ensures:
    - Prefix logic is respected
    - One orphan is detected
    - Status does not block detection
    """
    # Force prefix for this test
    monkeypatch.setattr("app.data_sync.orphan_detection.UNIQUE_ID_PREFIX", "TEST-")

    tgt_rows = [
        {"REC ID": "TEST-001", "Description": "desc A", "Status": "Active"},
        {"REC ID": "TEST-002", "Description": "desc B", "Status": "Active"},
        {"REC ID": "TEST-999", "Description": "orphan", "Status": "Active"},
    ]
    sot_ids = {"TEST-001", "TEST-002"}
    unique_id_col = "REC ID"

    orphans = find_orphaned_records(tgt_rows, sot_ids, unique_id_col)

    assert len(orphans) == 1
    assert orphans[0]["REC ID"] == "TEST-999"


def test_orphan_is_ignored_based_on_status(monkeypatch):
    # Force prefix for the test
    monkeypatch.setattr("app.data_sync.orphan_detection.UNIQUE_ID_PREFIX", "TEST-")

    # Monkeypatch ignore-status list: includes an extra status ("Discarded")
    monkeypatch.setattr(
        "app.data_sync.orphan_detection.ORPHANS_DETECTION_IGNORE_STATUS",
        ["Inactive", "Rejected", "Deprecated", "Closed", "Retired", "Discarded"],
    )

    tgt_rows = [
        {"REC ID": "TEST-999", "Status": "Inactive"},  # ignored
        {"REC ID": "TEST-888", "Status": "Rejected"},  # ignored
        {"REC ID": "TEST-777", "Status": "Discarded"},  # ignored because of monkeypatch
        {"REC ID": "TEST-555", "Status": "Active"},  # valid orphan
    ]

    sot_ids = set()
    unique_id_col = "REC ID"

    orphans = find_orphaned_records(tgt_rows, sot_ids, unique_id_col)

    # Only the Active record should remain as a valid orphan
    assert len(orphans) == 1
    assert orphans[0]["REC ID"] == "TEST-555"


def test_orphan_with_empty_status_is_not_ignored(monkeypatch):
    # Ensure prefix is enforced
    monkeypatch.setattr("app.data_sync.orphan_detection.UNIQUE_ID_PREFIX", "TEST-")

    # Monkeypatch ignore-status list (no empty value included)
    monkeypatch.setattr(
        "app.data_sync.orphan_detection.ORPHANS_DETECTION_IGNORE_STATUS",
        ["Inactive", "Rejected", "Deprecated", "Closed", "Retired"],
    )

    tgt_rows = [
        {"REC ID": "TEST-123", "Status": ""},  # empty → must NOT be ignored
        {
            "REC ID": "TEST-456",
            "Status": "   ",
        },  # whitespace → also must NOT be ignored
    ]

    sot_ids = set()
    unique_id_col = "REC ID"

    orphans = find_orphaned_records(tgt_rows, sot_ids, unique_id_col)

    # Both should be considered orphans
    assert {r["REC ID"] for r in orphans} == {"TEST-123", "TEST-456"}


def test_find_orphaned_records_empty_tgt():
    """No TGT rows → no orphans."""
    tgt_rows = []
    sot_ids = {"REC-001"}
    unique_id_col = "REC ID"

    orphans = find_orphaned_records(tgt_rows, sot_ids, unique_id_col)
    assert orphans == []


def test_find_orphaned_records_empty_sot_ids(monkeypatch):
    """
    If SOT has no IDs, all valid TGT IDs are considered orphaned.
    This matches expected behavior: TGT rows are not in SOT.
    """
    monkeypatch.setattr("app.data_sync.orphan_detection.UNIQUE_ID_PREFIX", "TEST-")

    tgt_rows = [
        {"REC ID": "TEST-001"},
        {"REC ID": "TEST-002"},
        {"REC ID": None},  # should be ignored
        {"REC ID": ""},  # ignored
    ]
    sot_ids = set()
    unique_id_col = "REC ID"

    orphans = find_orphaned_records(tgt_rows, sot_ids, unique_id_col)

    assert len(orphans) == 2
    assert {r["REC ID"] for r in orphans} == {"TEST-001", "TEST-002"}


def test_find_orphaned_records_mixed_ids():
    """
    Ensure correct detection when TGT contains missing, None, and valid IDs.
    """
    tgt_rows = [
        {"REC ID": "REC-100"},
        {"REC ID": None},
        {"REC ID": "REC-200"},
        {"REC ID": ""},  # skip
        {},
    ]
    sot_ids = {"REC-100"}
    unique_id_col = "REC ID"

    orphans = find_orphaned_records(tgt_rows, sot_ids, unique_id_col)

    assert len(orphans) == 1
    assert orphans[0]["REC ID"] == "REC-200"


def test_orphans_when_sot_has_none_ids():
    tgt_rows = [
        {"REC ID": "REC-100"},
        {"REC ID": "REC-200"},
    ]
    sot_ids = {None, ""}  # invalid IDs present in SOT
    unique_id_col = "REC ID"

    orphans = find_orphaned_records(tgt_rows, sot_ids, unique_id_col)

    # Both must be considered orphans
    assert {r["REC ID"] for r in orphans} == {"REC-100", "REC-200"}


def test_missing_unique_id_key_is_ignored():
    tgt_rows = [
        {"REC ID": "REC-001"},
        {"No ID": "REC-XXX"},  # missing unique_id_col completely
    ]
    sot_ids = {"REC-001"}
    unique_id_col = "REC ID"

    orphans = find_orphaned_records(tgt_rows, sot_ids, unique_id_col)

    assert len(orphans) == 0  # the missing-ID row should not break logic


# === Test for generate_orphan_report_to_log ===
def test_generate_orphan_report_appends_to_log(tmp_path, monkeypatch):
    # Redirect LOG_PATH to tmp_path for the test
    monkeypatch.setattr(
        "app.data_sync.orphan_detection.LOG_PATH",
        str(tmp_path / "sync_diff_{timestamp}.log"),
    )

    log_path = tmp_path / "sync_diff_TEST.log"
    log_path.write_text("[UPDATED] REC-001\n")

    sot_rows = [{"REC ID": "REC-001"}]
    tgt_rows = [
        {"REC ID": "REC-001"},
        {"REC ID": "REC-999", "Description": "legacy"},
    ]

    generate_orphan_report_to_log(
        timestamp="TEST",
        sot_rows=sot_rows,
        tgt_rows=tgt_rows,
        unique_id_sot="REC ID",
        unique_id_tgt="REC ID",
        column_mapping={"Description": "Description"},
    )

    content = log_path.read_text()
    assert "=== ORPHANED RECORDS" in content
    assert "[ORPHANED] REC-999" in content


def test_no_orphans_produces_no_output(tmp_path):
    log_path = tmp_path / "sync_diff_TEST.log"
    log_path.write_text("PREVIOUS\n")

    sot_rows = [{"ID": "A"}]
    tgt_rows = [{"ID": "A"}]

    generate_orphan_report_to_log(
        timestamp="TEST",
        sot_rows=sot_rows,
        tgt_rows=tgt_rows,
        unique_id_sot="ID",
        unique_id_tgt="ID",
        column_mapping={},
    )

    content = log_path.read_text()
    assert "ORPHANED" not in content


def test_orphan_report_outputs_only_id(tmp_path, monkeypatch):
    # Ensure the orphan feature uses strict prefix detection
    monkeypatch.setattr("app.data_sync.orphan_detection.UNIQUE_ID_PREFIX", "REC-")

    # Redirect LOG_PATH to tmp_path
    monkeypatch.setattr(
        "app.data_sync.orphan_detection.LOG_PATH",
        str(tmp_path / "sync_diff_{timestamp}.log"),
    )

    log_path = tmp_path / "sync_diff_TEST.log"
    log_path.write_text("HEADER\n")

    sot_rows = [{"REC ID": "REC-001"}]
    tgt_rows = [
        {"REC ID": "REC-999", "Description": "orphan desc", "Owner": "Ghost"},
    ]

    generate_orphan_report_to_log(
        timestamp="TEST",
        sot_rows=sot_rows,
        tgt_rows=tgt_rows,
        unique_id_sot="REC ID",
        unique_id_tgt="REC ID",
        column_mapping={"Description": "Description", "Owner": "Owner"},
    )

    content = log_path.read_text()

    # --- Assertions ---
    # 1. Orphan section header must exist
    assert "=== ORPHANED RECORDS" in content

    # 2. Only the orphan ID should appear
    assert "[ORPHANED] REC-999" in content

    # 3. Absolutely no mapped columns should appear
    assert "Description" not in content
    assert "Owner" not in content
    assert "'" not in content  # avoids " 'orphan desc' "


def test_orphan_log_path_respects_timestamp(tmp_path, monkeypatch):
    # Enforce consistent prefix for test validity
    monkeypatch.setattr("app.data_sync.orphan_detection.UNIQUE_ID_PREFIX", "TEST-")

    # Redirect LOG_PATH to tmp_path
    monkeypatch.setattr(
        "app.data_sync.orphan_detection.LOG_PATH",
        str(tmp_path / "sync_diff_{timestamp}.log"),
    )

    timestamp = "ABC123"
    expected_path = tmp_path / "sync_diff_ABC123.log"

    generate_orphan_report_to_log(
        timestamp=timestamp,
        sot_rows=[{"ID": "TEST-001"}],
        tgt_rows=[{"ID": "TEST-999"}],  # valid orphan under TEST- prefix
        unique_id_sot="ID",
        unique_id_tgt="ID",
        column_mapping={},
    )

    assert expected_path.exists(), "Report must be written to the LOG_PATH template"


def test_case_sensitivity_in_ids(monkeypatch):
    monkeypatch.setattr("app.data_sync.orphan_detection.UNIQUE_ID_PREFIX", "TEST-")

    tgt_rows = [{"REC ID": "TEST-001"}]
    sot_ids = {"test-001"}  # different case

    orphans = find_orphaned_records(tgt_rows, sot_ids, "REC ID")

    # current expected behavior (strict match → orphan)
    assert len(orphans) == 1
