import pytest
from app.validation.duplicate_detection import ensure_no_duplicate_ids


def test_no_duplicates_passes():
    rows = [
        {"REC ID": "A1", "Description": "x"},
        {"REC ID": "A2", "Description": "y"},
        {"REC ID": "A3", "Description": "z"},
    ]

    # Should not raise
    ensure_no_duplicate_ids(rows, "REC ID", "SOT")


def test_duplicate_ids_raises_error():
    rows = [
        {"REC ID": "A1", "Description": "x"},
        {"REC ID": "A2", "Description": "y"},
        {"REC ID": "A1", "Description": "duplicate"},
    ]

    with pytest.raises(ValueError) as exc:
        ensure_no_duplicate_ids(rows, "REC ID", "SOT")

    assert "SOT: duplicate IDs found in 'REC ID'" in str(exc.value)
    assert "A1" in str(exc.value)


def test_duplicate_ids_multiple():
    rows = [
        {"REC ID": "A1"},
        {"REC ID": "A2"},
        {"REC ID": "A1"},
        {"REC ID": "A2"},
    ]

    with pytest.raises(ValueError) as exc:
        ensure_no_duplicate_ids(rows, "REC ID", "TGT")

    msg = str(exc.value)
    assert "TGT: duplicate IDs found in 'REC ID'" in msg
    assert "A1" in msg
    assert "A2" in msg


def test_missing_unique_id_key_treated_as_None():
    rows = [
        {"REC ID": "A1"},
        {},  # uid = None
        {"REC ID": "A1"},  # duplicate
        {},  # another None
    ]

    # Expect:
    # - duplicates detected for A1 only
    # - None values grouped separately but still detected as duplicate
    with pytest.raises(ValueError) as exc:
        ensure_no_duplicate_ids(rows, "REC ID", "SOT")

    msg = str(exc.value)
    assert "A1" in msg
    assert "None" in msg
