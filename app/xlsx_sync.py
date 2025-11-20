from loguru import logger
import copy
from datetime import datetime

from config import OUTPUT_DIR
from app.data_io.xlsx_io import read_sot_xlsx, read_tgt_xlsx, write_tgt_xlsx
from app.data_sync.sync_engine import sync_sot_to_tgt
from app.data_sync.diff_report import generate_diff_report
from app.data_sync.orphan_detection import generate_orphan_report_to_log
from app.validation.mapping_validation import (
    validate_column_mapping,
    ensure_consistent_headers,
)
from app.validation.duplicate_detection import ensure_no_duplicate_ids


def run_sync(
    sot_path: str,
    tgt_path: str,
    sot_sheet_name: str,
    tgt_sheet_name: str,
    unique_id_sot: str,
    unique_id_tgt: str,
    column_mapping: dict,
    output_dir: str = OUTPUT_DIR,
):
    """
    End-to-end synchronization between SOT and TGT XLSX files.
    Keeps main.py minimal by handling all orchestration logic here.
    """
    logger.info("=== XLSX Delta Sync Starting ===")

    # Step 1: Read SOT (data only)
    sot_headers, sot_rows = read_sot_xlsx(sot_path, sot_sheet_name)
    logger.info(
        f"SOT loaded with {len(sot_rows)} records and {len(sot_headers)} columns"
    )

    # Step 2: Read TGT (with formatting)
    wb, ws = read_tgt_xlsx(tgt_path, tgt_sheet_name)
    tgt_headers = [
        c for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
    ]
    tgt_rows = [
        dict(zip(tgt_headers, row)) for row in ws.iter_rows(min_row=2, values_only=True)
    ]
    logger.info(
        f"TGT loaded with {len(tgt_rows)} records and {len(tgt_headers)} columns"
    )

    # Validation: Headers in config.py must exist in SOT and TGT
    try:
        # Headers consistency check (optional)
        ensure_consistent_headers(sot_rows, "SOT")
        ensure_consistent_headers(tgt_rows, "TGT")

        # Column mapping validation - mapped columns on both left and right hand side must exist in the XLSX files
        mapping_errors = validate_column_mapping(sot_rows, tgt_rows, column_mapping)
        if mapping_errors:
            raise ValueError(
                "Column mapping validation failed:\n"
                + "\n".join(f"- {err}" for err in mapping_errors)
            )

        # Check for duplicate unique IDs in SOT and TGT
        ensure_no_duplicate_ids(sot_rows, unique_id_sot, "SOT")
        ensure_no_duplicate_ids(tgt_rows, unique_id_tgt, "TGT")

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise

    original_tgt_rows = copy.deepcopy(tgt_rows)

    # Step 3: Perform sync logic
    updated_rows = sync_sot_to_tgt(
        sot_rows, tgt_rows, unique_id_sot, unique_id_tgt, column_mapping
    )

    # Step 4: Write updated TGT preserving format
    output_file = write_tgt_xlsx(wb, ws, updated_rows, tgt_path, output_dir)
    logger.success(f"Updated TGT written to: {output_file}")

    # Step 5: Generate diff report comparing SOT vs updated TGT
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    try:
        generate_diff_report(
            timestamp=timestamp,
            old_rows=original_tgt_rows,
            new_rows=updated_rows,
            unique_id_col=unique_id_tgt,
            column_mapping=column_mapping,
            output_dir=output_dir,
        )
    except Exception as e:
        logger.warning(f"Diff report generation failed: {e}")

    # Step 6: Orphaned records appended to same diff log
    generate_orphan_report_to_log(
        timestamp=timestamp,
        sot_rows=sot_rows,
        tgt_rows=updated_rows,
        unique_id_sot=unique_id_sot,
        unique_id_tgt=unique_id_tgt,
        column_mapping=column_mapping,
    )

    logger.info("=== Sync Complete ===")
    return output_file
