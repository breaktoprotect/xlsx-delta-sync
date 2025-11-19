from typing import List, Dict

from config import LOG_PATH, ORPHANS_DETECTION_IGNORE_STATUS, UNIQUE_ID_PREFIX


def find_orphaned_records(
    tgt_rows: List[Dict[str, str]],
    sot_ids: set,
    unique_id_col: str,
) -> List[Dict[str, str]]:
    """
    Return TGT rows whose unique IDs do NOT exist in SOT.
    These rows are never updated by sync_engine and are effectively orphaned.
    """
    orphans = []
    for row in tgt_rows:
        rec_id = row.get(unique_id_col)
        if not rec_id:
            continue

        if _should_ignore_orphan(row, unique_id_col):
            continue

        if rec_id not in sot_ids:
            orphans.append(row)
    return orphans


def generate_orphan_report_to_log(
    timestamp: str,
    sot_rows: List[Dict[str, str]],
    tgt_rows: List[Dict[str, str]],
    unique_id_sot: str,
    unique_id_tgt: str,
    column_mapping: Dict[str, str],
) -> None:
    """
    Append orphaned record details to the SAME diff log created by generate_diff_report().
    Uses config.LOG_PATH and shared timestamp.
    """
    log_path = LOG_PATH.format(timestamp=timestamp)

    sot_ids = {row.get(unique_id_sot) for row in sot_rows if row.get(unique_id_sot)}

    orphaned_rows = find_orphaned_records(
        tgt_rows=tgt_rows,
        sot_ids=sot_ids,
        unique_id_col=unique_id_tgt,
    )

    if not orphaned_rows:
        return

    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n\n=== ORPHANED RECORDS (Present in TGT but not in SOT) ===\n")
        for row in orphaned_rows:
            rid = row.get(unique_id_tgt)
            f.write(f"\n[ORPHANED] {rid}\n")


def _should_ignore_orphan(row: Dict[str, str], unique_id_col: str) -> bool:
    rec_id = (row.get(unique_id_col) or "").strip()

    # 1. Reject if not starting with required prefix
    if not rec_id.startswith(UNIQUE_ID_PREFIX):
        return True

    # 2. Ignore specific statuses
    status = (row.get("Status") or "").strip()
    if status in ORPHANS_DETECTION_IGNORE_STATUS:
        return True

    return False
