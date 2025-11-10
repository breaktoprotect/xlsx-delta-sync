from typing import Dict, List


def validate_column_mapping(
    sot_rows: List[Dict[str, str]],
    tgt_rows: List[Dict[str, str]],
    column_mapping: Dict[str, str],
) -> List[str]:
    """
    Validate that all mapped SOT and TGT columns exist in their respective datasets.

    Returns a list of error messages (empty list means mapping is valid).
    Designed for early pre-sync validation.
    """
    errors = []

    if not sot_rows:
        errors.append("SOT is empty — cannot validate mapping.")
        return errors
    if not tgt_rows:
        errors.append("TGT is empty — cannot validate mapping.")
        return errors

    sot_columns = set(sot_rows[0].keys())
    tgt_columns = set(tgt_rows[0].keys())

    for sot_col, tgt_col in column_mapping.items():
        if sot_col not in sot_columns:
            errors.append(f"SOT column '{sot_col}' not found in SOT headers.")
        if tgt_col not in tgt_columns:
            errors.append(f"TGT column '{tgt_col}' not found in TGT headers.")

    return errors


def ensure_consistent_headers(rows: list[dict], dataset_name: str = "SOT") -> None:
    """
    Ensure all rows in a dataset (SOT/TGT) have consistent column headers.
    Raises ValueError if inconsistencies are detected.
    """
    if not rows:
        return

    expected_keys = set(rows[0].keys())
    for i, row in enumerate(rows[1:], start=2):
        current_keys = set(row.keys())
        if current_keys != expected_keys:
            raise ValueError(
                f"{dataset_name} row {i} has inconsistent columns.\n"
                f"Expected: {sorted(expected_keys)}\n"
                f"Found: {sorted(current_keys)}"
            )
