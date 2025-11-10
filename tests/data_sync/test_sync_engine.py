import pytest
from loguru import logger

from app.data_sync.sync_engine import sync_sot_to_tgt
from app.data_sync.sync_engine import find_unmapped_sot_columns


@pytest.fixture
def sample_data():
    sot_rows = [
        {
            "REC ID": "REC-001",
            "Description": "Updated desc",
            "Owner": "Alice",
            "Unused": "X",
        },
        {
            "REC ID": "REC-002",
            "Description": "New record",
            "Owner": "Bob",
            "Unused": "Y",
        },
    ]
    tgt_rows = [
        {
            "REC ID": "REC-001",
            "Description": "Old desc",
            "Owner": "Alice",
            "SomeOtherField": "Value",
        },
        {
            "REC ID": "REC-999",
            "Description": "Existing record",
            "Owner": "Charlie",
            "SomeOtherField": "Value",
        },
    ]
    mapping = {"Description": "Description", "Owner": "Owner"}
    return sot_rows, tgt_rows, mapping


def test_sync_updates_and_adds(sample_data, caplog):
    sot_rows, tgt_rows, mapping = sample_data
    logger.add(caplog.handler)

    updated = sync_sot_to_tgt(
        sot_rows=sot_rows,
        tgt_rows=tgt_rows,
        unique_id_col_sot="REC ID",
        unique_id_col_tgt="REC ID",
        column_mapping=mapping,
    )

    # IDs that should now exist
    ids = {r["REC ID"] for r in updated}
    assert {"REC-001", "REC-002", "REC-999"} == ids

    # REC-001 updated
    rec1 = next(r for r in updated if r["REC ID"] == "REC-001")
    assert rec1["Description"] == "Updated desc"

    # REC-002 added
    rec2 = next(r for r in updated if r["REC ID"] == "REC-002")
    assert rec2["Owner"] == "Bob"

    # REC-999 unchanged
    rec999 = next(r for r in updated if r["REC ID"] == "REC-999")
    assert rec999["Owner"] == "Charlie"
    assert rec999["Description"] == "Existing record"

    # Verify logs for both update and add
    log_text = " ".join(caplog.messages)
    assert "updated" in log_text
    assert "added" in log_text


def test_sync_skips_missing_id(caplog):
    sot_rows = [{"Description": "No ID"}]
    tgt_rows = []
    mapping = {"Description": "Description"}

    logger.add(caplog.handler)

    result = sync_sot_to_tgt(sot_rows, tgt_rows, "REC ID", "REC ID", mapping)
    assert result == []
    assert any("missing unique ID" in m for m in caplog.messages)


# ---------------- Tests for find_unmapped_sot_columns ----------------
def test_find_unmapped_standard_case():
    # Extras must exist in the header (row 1) for XLSX; keep columns consistent across rows
    sot_rows = [
        {
            "REC ID": "REC-001",
            "Description": "abc",
            "Owner": "x",
            "Extra1": "ignored",
            "Extra2": "",
        },
        {
            "REC ID": "REC-002",
            "Description": "def",
            "Owner": "y",
            "Extra1": "ignored",
            "Extra2": "ignored",
        },
    ]
    mapping = {"Description": "Description", "Owner": "Owner"}
    result = find_unmapped_sot_columns(sot_rows, mapping, "REC ID")

    assert set(result) == {"Extra1", "Extra2"}


def test_find_unmapped_no_unmapped_columns():
    sot_rows = [
        {"REC ID": "REC-001", "Description": "abc", "Owner": "x"},
    ]
    mapping = {"Description": "Description", "Owner": "Owner"}
    result = find_unmapped_sot_columns(sot_rows, mapping, "REC ID")

    assert result == []


def test_find_unmapped_empty_sot():
    sot_rows = []
    mapping = {"Description": "Description", "Owner": "Owner"}
    result = find_unmapped_sot_columns(sot_rows, mapping, "REC ID")

    assert result == []
