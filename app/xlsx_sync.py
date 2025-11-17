from loguru import logger
import copy

from config import OUTPUT_DIR
from app.data_io.xlsx_io import read_sot_xlsx, read_tgt_xlsx, write_tgt_xlsx
from app.data_sync.sync_engine import sync_sot_to_tgt
from app.data_sync.diff_report import generate_diff_report


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

    original_tgt_rows = copy.deepcopy(tgt_rows)

    # Step 3: Perform sync logic
    updated_rows = sync_sot_to_tgt(
        sot_rows, tgt_rows, unique_id_sot, unique_id_tgt, column_mapping
    )

    # Step 4: Write updated TGT preserving format
    output_file = write_tgt_xlsx(wb, ws, updated_rows, tgt_path, output_dir)
    logger.success(f"Updated TGT written to: {output_file}")

    # Step 5: Generate diff report comparing SOT vs updated TGT
    try:
        generate_diff_report(
            old_rows=original_tgt_rows,
            new_rows=updated_rows,  # ← use in-memory data
            unique_id_col=unique_id_tgt,
            column_mapping=column_mapping,
            output_dir=output_dir,
        )
    except Exception as e:
        logger.warning(f"Diff report generation failed: {e}")

    logger.info("=== Sync Complete ===")
    return output_file
