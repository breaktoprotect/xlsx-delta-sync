from config import SOT_TO_TGT_COLUMN_MAPPING
from app.xlsx_sync import run_sync

if __name__ == "__main__":
    SOT_PATH = "tests/sample_input_files/SOT_sample.xlsx"
    TGT_PATH = "tests/sample_input_files/TGT_sample.xlsx"
    UNIQUE_ID_SOT = "REC ID"
    UNIQUE_ID_TGT = "Record ID"
    COLUMN_MAPPING = SOT_TO_TGT_COLUMN_MAPPING

    run_sync(SOT_PATH, TGT_PATH, UNIQUE_ID_SOT, UNIQUE_ID_TGT, COLUMN_MAPPING)
