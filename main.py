from config import SOT_TO_TGT_COLUMN_MAPPING, SOT_SHEETNAME, TGT_SHEETNAME
from app.xlsx_sync import run_sync

if __name__ == "__main__":
    SOT_PATH = "tests/sample_input_files/SOT_sample.xlsx"
    TGT_PATH = "tests/sample_input_files/TGT_sample.xlsx"
    UNIQUE_ID_SOT = "REC ID"
    UNIQUE_ID_TGT = "Record ID"
    COLUMN_MAPPING = SOT_TO_TGT_COLUMN_MAPPING

    run_sync(
        sot_path=SOT_PATH,
        tgt_path=TGT_PATH,
        sot_sheet_name=SOT_SHEETNAME,
        tgt_sheet_name=TGT_SHEETNAME,
        unique_id_sot=UNIQUE_ID_SOT,
        unique_id_tgt=UNIQUE_ID_TGT,
        column_mapping=COLUMN_MAPPING,
    )

    run_sync(
        SOT_PATH,
        TGT_PATH,
        SOT_SHEETNAME,
        TGT_SHEETNAME,
        UNIQUE_ID_SOT,
        UNIQUE_ID_TGT,
        COLUMN_MAPPING,
    )
