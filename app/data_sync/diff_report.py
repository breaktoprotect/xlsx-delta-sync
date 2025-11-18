import os
from typing import List, Dict, Optional
from config import OUTPUT_DIR, LOG_PATH


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
