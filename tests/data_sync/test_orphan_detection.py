import pytest
from app.data_sync.orphan_detection import find_orphaned_records
from app.data_sync.orphan_detection import generate_orphan_report_to_log


def test_find_orphaned_records_basic():
    """
    Basic test:
    - TGT has 3 rows
    - SOT has 2 IDs
    - 1 orphan should be detected
    """
    tgt_rows = [
        {"REC ID": "REC-001", "Description": "desc A"},
        {"REC ID": "REC-002", "Description": "desc B"},
        {"REC ID": "REC-999", "Description": "orphan"},
    ]
    sot_ids = {"REC-001", "REC-002"}
    unique_id_col = "REC ID"

    orphans = find_orphaned_records(tgt_rows, sot_ids, unique_id_col)

    assert len(orphans) == 1
    assert orphans[0]["REC ID"] == "REC-999"


def test_find_orphaned_records_empty_tgt():
    """No TGT rows → no orphans."""
    tgt_rows = []
    sot_ids = {"REC-001"}
    unique_id_col = "REC ID"

    orphans = find_orphaned_records(tgt_rows, sot_ids, unique_id_col)
    assert orphans == []


def test_find_orphaned_records_empty_sot_ids():
    """
    If SOT has no IDs, all valid TGT IDs are considered orphaned.
    This matches expected behavior: TGT rows are not in SOT.
    """
    tgt_rows = [
        {"REC ID": "A"},
        {"REC ID": "B"},
        {"REC ID": None},  # should be ignored
        {"REC ID": ""},  # ignored
    ]
    sot_ids = set()
    unique_id_col = "REC ID"

    orphans = find_orphaned_records(tgt_rows, sot_ids, unique_id_col)

    assert len(orphans) == 2
    assert {r["REC ID"] for r in orphans} == {"A", "B"}


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


def test_numeric_ids_are_supported():
    tgt_rows = [
        {"ID": 1},
        {"ID": 2},
        {"ID": 999},
    ]
    sot_ids = {1, 2}
    unique_id_col = "ID"

    orphans = find_orphaned_records(tgt_rows, sot_ids, unique_id_col)

    assert len(orphans) == 1
    assert orphans[0]["ID"] == 999


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


def test_orphan_report_includes_mapped_columns(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.data_sync.orphan_detection.LOG_PATH",
        str(tmp_path / "sync_diff_{timestamp}.log"),
    )

    log_path = tmp_path / "sync_diff_TEST.log"
    log_path.write_text("HEADER\n")

    sot_rows = [{"REC ID": "REC-001"}]
    tgt_rows = [{"REC ID": "REC-999", "Description": "orphan desc", "Owner": "Ghost"}]

    generate_orphan_report_to_log(
        timestamp="TEST",
        sot_rows=sot_rows,
        tgt_rows=tgt_rows,
        unique_id_sot="REC ID",
        unique_id_tgt="REC ID",
        column_mapping={"Description": "Description", "Owner": "Owner"},
    )

    content = log_path.read_text()
    assert "Description: 'orphan desc'" in content
    assert "Owner: 'Ghost'" in content


def test_orphan_log_path_respects_timestamp(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "app.data_sync.orphan_detection.LOG_PATH",
        str(tmp_path / "sync_diff_{timestamp}.log"),
    )

    timestamp = "ABC123"
    expected_path = tmp_path / "sync_diff_ABC123.log"

    generate_orphan_report_to_log(
        timestamp=timestamp,
        sot_rows=[{"ID": "A"}],
        tgt_rows=[{"ID": "B"}],
        unique_id_sot="ID",
        unique_id_tgt="ID",
        column_mapping={},
    )

    assert expected_path.exists(), "Report must be written to the LOG_PATH template"
