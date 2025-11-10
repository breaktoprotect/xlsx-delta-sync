from typing import Dict, List
from loguru import logger


def sync_sot_to_tgt(
    sot_rows: List[Dict[str, str]],
    tgt_rows: List[Dict[str, str]],
    unique_id_col_sot: str,
    unique_id_col_tgt: str,
    column_mapping: Dict[str, str],
) -> List[Dict[str, str]]:
    """
    Synchronize SOT → TGT.
    - Updates mapped fields where IDs match.
    - Adds new rows from SOT if missing in TGT.
    - Logs all operations.

    Args:
        sot_rows: list of dicts from SOT
        tgt_rows: list of dicts from TGT
        unique_id_col_sot: SOT unique ID column
        unique_id_col_tgt: TGT unique ID column
        column_mapping: mapping of SOT→TGT column names
    """
    tgt_index = {r[unique_id_col_tgt]: r for r in tgt_rows if r.get(unique_id_col_tgt)}

    # Detect and log unmapped SOT columns once
    unmapped = find_unmapped_sot_columns(sot_rows, column_mapping, unique_id_col_sot)
    if unmapped:
        logger.warning(
            f"Unmapped SOT columns ignored ({len(unmapped)}): {', '.join(unmapped)}"
        )

    for sot_row in sot_rows:
        sot_id = sot_row.get(unique_id_col_sot)
        if not sot_id:
            logger.error(f"SOT record missing unique ID — skipped: {sot_row}")
            continue

        if sot_id in tgt_index:
            tgt_row = tgt_index[sot_id]
            changed = []
            for sot_col, tgt_col in column_mapping.items():
                sot_val = str(sot_row.get(sot_col, "") or "").strip()
                tgt_val = str(tgt_row.get(tgt_col, "") or "").strip()
                if sot_val != tgt_val:
                    tgt_row[tgt_col] = sot_val
                    changed.append(tgt_col)
            if changed:
                logger.info(f"{sot_id}: updated {changed}")
        else:
            new_row = {
                tgt_col: sot_row.get(sot_col, "")
                for sot_col, tgt_col in column_mapping.items()
            }
            new_row[unique_id_col_tgt] = sot_id
            tgt_rows.append(new_row)
            logger.info(f"{sot_id}: added new record")

    return tgt_rows


def find_unmapped_sot_columns(
    sot_rows: List[Dict[str, str]],
    column_mapping: Dict[str, str],
    unique_id_col_sot: str,
) -> List[str]:
    """
    Identify SOT columns that are not mapped to any TGT column.
    Returns a sorted list of unmapped SOT column names.
    """
    if not sot_rows:
        return []

    all_sot_columns = set(sot_rows[0].keys())
    mapped_columns = set(column_mapping.keys()) | {unique_id_col_sot}
    unmapped = sorted(all_sot_columns - mapped_columns)
    return unmapped
