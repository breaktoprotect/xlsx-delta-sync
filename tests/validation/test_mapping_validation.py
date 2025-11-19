import pytest
from app.validation.mapping_validation import (
    validate_column_mapping,
    ensure_consistent_headers,
)


@pytest.fixture
def sample_data():
    sot_rows = [
        {"REC ID": "REC-001", "Description": "desc", "Owner": "Alice"},
        {"REC ID": "REC-002", "Description": "desc", "Owner": "Bob"},
    ]
    tgt_rows = [
        {
            "REC ID": "REC-001",
            "Description": "old",
            "Owner": "Charlie",
            "Status": "Active",
        }
    ]
    return sot_rows, tgt_rows


@pytest.fixture
def bad_data():
    sot_rows = [
        {"REC ID": "REC-001", "Description": "desc", "Owner": "Alice"},
        {"REC ID": "REC-002", "Description": "desc", "Owner": "Bob"},
        {"REC ID": "REC-003", "Description": "desc", "Owner": "Bob", "Extra": "X"},
    ]
    tgt_rows = [
        {
            "REC ID": "REC-001",
            "Description": "old",
            "Owner": "Charlie",
            "Status": "Active",
        }
    ]
    return sot_rows, tgt_rows


def test_validate_mapping_valid(sample_data):
    sot_rows, tgt_rows = sample_data
    mapping = {"Description": "Description", "Owner": "Owner"}

    errors = validate_column_mapping(sot_rows, tgt_rows, mapping)
    assert errors == []


def test_validate_mapping_missing_sot_column(sample_data):
    sot_rows, tgt_rows = sample_data
    mapping = {"Nonexistent": "Description"}

    errors = validate_column_mapping(sot_rows, tgt_rows, mapping)
    assert "SOT column 'Nonexistent' not found" in errors[0]


def test_validate_mapping_missing_tgt_column(sample_data):
    sot_rows, tgt_rows = sample_data
    mapping = {"Description": "MissingColumn"}

    errors = validate_column_mapping(sot_rows, tgt_rows, mapping)
    assert "TGT column 'MissingColumn' not found" in errors[0]


def test_validate_mapping_empty_sot():
    sot_rows = []
    tgt_rows = [{"REC ID": "R1"}]
    mapping = {"Description": "Description"}

    errors = validate_column_mapping(sot_rows, tgt_rows, mapping)
    assert any("SOT is empty" in e for e in errors)


def test_validate_mapping_empty_tgt():
    sot_rows = [{"REC ID": "R1", "Description": "X"}]
    tgt_rows = []
    mapping = {"Description": "Description"}

    errors = validate_column_mapping(sot_rows, tgt_rows, mapping)
    assert any("TGT is empty" in e for e in errors)


def test_mapping_allows_tgt_extra_columns():
    sot_rows = [
        {"REC ID": "1", "Description": "A", "Owner": "Alice"},
    ]
    tgt_rows = [
        {"REC ID": "1", "Description": "A", "Owner": "Alice", "Status": "Active"},
    ]

    mapping = {"Description": "Description", "Owner": "Owner"}

    errors = validate_column_mapping(sot_rows, tgt_rows, mapping)
    assert errors == []  # extra columns in TGT are allowed


# ------------------------ Test Header Consistency ------------------------ #
def test_consistent_headers_valid():
    rows = [
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob"},
    ]
    # Should not raise
    ensure_consistent_headers(rows, "SOT")


def test_inconsistent_headers_raises():
    rows = [
        {"id": "1", "name": "Alice"},
        {"id": "2", "name": "Bob", "extra": "X"},  # inconsistent keys
    ]

    with pytest.raises(ValueError) as excinfo:
        ensure_consistent_headers(rows, "SOT")

    assert "inconsistent columns" in str(excinfo.value)
    assert "extra" in str(excinfo.value).lower()
