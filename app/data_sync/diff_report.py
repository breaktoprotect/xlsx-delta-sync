import os
from typing import List, Dict, Optional
from config import OUTPUT_DIR, LOG_PATH, UNIQUE_ID_PREFIX


def generate_diff_report(
    timestamp: str,
    old_rows: List[Dict[str, str]],
    new_rows: List[Dict[str, str]],
    unique_id_col: str,
    column_mapping: Dict[str, str],
    output_dir: str = OUTPUT_DIR,
    valid_ids: Optional[set] = None,
) -> str:
    """
    Generate a human-readable text diff report comparing OLD vs NEW dataset
    (typically TGT before vs TGT after sync).

    - Skips unchanged records (no diffs)
    - Skips any record containing the text 'Record Should Not be Touched'
    - Shows only real field-level differences in mapped columns
    - Detects and logs new records (ADDED)

    Args:
        old_rows: original dataset (TGT before sync)
        new_rows: updated dataset (TGT after sync)
        unique_id_col: unique record ID column (same for both)
        column_mapping: mapping of columns to compare
        output_dir: directory where the .log file should be written
        valid_ids: optional set of IDs known from SOT (to ignore others)

    Returns:
        Path to the generated diff log file
    """
    new_index = {r.get(unique_id_col): r for r in new_rows if r.get(unique_id_col)}

    log_path = LOG_PATH.format(timestamp=timestamp)
    os.makedirs(output_dir, exist_ok=True)

    lines = []

    # === UPDATED RECORDS ===
    for old in old_rows:
        record_id = old.get(unique_id_col)
        if not record_id:
            continue

        if not record_id.startswith(UNIQUE_ID_PREFIX):
            continue

        if valid_ids and record_id not in valid_ids:
            continue

        new = new_index.get(record_id)
        if not new:
            continue  # skip deletions (sync never deletes)

        # skip sentinel/safeguard records
        if "Record Should Not be Touched" in str(new.values()):
            continue

        diffs = []
        for col_old, col_new in column_mapping.items():
            # Compare TGT→TGT (old vs new) using TGT column names only
            old_val = str(old.get(col_new, "") or "").strip()
            new_val = str(new.get(col_new, "") or "").strip()
            if old_val != new_val:
                diffs.append((col_new, old_val, new_val))

        if diffs:
            lines.append(f"[UPDATED] {record_id}")
            for col, old_v, new_v in diffs:
                lines.append(f"    {col}: '{old_v}' → '{new_v}'")
            lines.append("")

    # === NEW RECORDS ===
    old_ids = {r.get(unique_id_col) for r in old_rows if r.get(unique_id_col)}
    for new in new_rows:
        rec_id = new.get(unique_id_col)
        if not rec_id:
            continue
        if not rec_id.startswith(UNIQUE_ID_PREFIX):
            continue
        if valid_ids and rec_id not in valid_ids:
            continue
        if rec_id in old_ids:
            continue

        # skip sentinel/safeguard records
        if "Record Should Not be Touched" in str(new.values()):
            continue

        lines.append(f"[ADDED] {rec_id}")
        for c in column_mapping.values():
            val = str(new.get(c, "") or "").strip()
            if val:
                lines.append(f"    {c}: '{val}'")
        lines.append("")

    # === NO CHANGES CASE ===
    if not lines:
        lines = ["No differences found."]

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"\n===== SYNC DIFF REPORT =====\n")
    print("\n".join(lines))
    print(f"\n✅ Diff report saved to: {log_path}\n")

    return log_path


def test_diff_report_skips_non_sot_records_in_updated(tmp_path, monkeypatch):
    """
    A TGT record that is NOT in SOT (valid_ids) and whose ID does NOT
    start with the required UNIQUE_ID_PREFIX ('TEST-') must NOT be logged
    under [UPDATED], even if its values changed.
    """

    # Patch log path
    monkeypatch.setattr(
        "app.data_sync.diff_report.LOG_PATH",
        str(tmp_path / "sync_diff_{timestamp}.log"),
    )

    # IMPORTANT:
    # Patch UNIQUE_ID_PREFIX *inside diff_report module*, not the config module.
    monkeypatch.setattr(
        "app.data_sync.diff_report.UNIQUE_ID_PREFIX",
        "TEST-",
    )

    # --- Arrange ---
    old_rows = [
        {"Record ID": "TEST-001", "Description": "A"},  # valid SOT ID
        {"Record ID": "NOT_VALID", "Description": "Old"},  # MUST be ignored
    ]

    new_rows = [
        {"Record ID": "TEST-001", "Description": "A"},  # unchanged
        {"Record ID": "NOT_VALID", "Description": "New"},  # changed but invalid
    ]

    # Only TEST-001 is a valid SOT ID
    valid_ids = {"TEST-001"}

    column_mapping = {"Description": "Description"}

    timestamp = "TEST_PREFIX_FILTER"

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
    # MUST NOT appear in UPDATED
    assert (
        "[UPDATED] NOT_VALID" not in content
    ), "Record IDs not matching SOT and prefix 'TEST-' must not appear in UPDATED."

    # MUST NOT include its diff
    assert (
        "Old" not in content and "New" not in content
    ), "Diff lines for NOT_VALID must not appear at all."

    # Only TEST-001 exists and has no differences
    assert "No differences found" in content
