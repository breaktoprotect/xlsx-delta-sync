# XLSX Delta Sync

A small Python utility that syncs a **Source of Truth (SOT)** spreadsheet into a **single Target (TGT)** spreadsheet.  
It updates only mapped columns, adds missing records, never deletes, and never overwrites your input files.

---

## Features

- **Single TGT per run** (simple, deterministic flow).
- **Strict SOT-overwrites**: if anything differs in TGT (extra spaces, casing, etc.), SOT value replaces it.
- **Mapped columns only**: unmapped TGT columns are never touched.
- **Add-only for new records**: missing TGT rows (by unique ID) are appended.
- **Fatal validations**:
  - Duplicate SOT IDs
  - Missing mapped columns (SOT/TGT)
  - Missing unique ID in any SOT row
- **Logging with Loguru**: `sync_diff_<YYYYMMDD_HHMM>.log` (updates + additions).
- **Safe output**: writes a new XLSX file, does not modify inputs.
- **Format preservation** (XLSX): preserves TGT cell fill colors.

---

## Status / Scope

- **Supported**: XLSX
- **Planned**: CSV, Flet GUI, multiple config sets (still one TGT per run)

---

## Usage

1. Prepare files (XLSX):
   - SOT file (authoritative data)
   - TGT file (to update)
2. Set IDs and mapping (e.g., in `config.py`):
   ```python
   SOT_UNIQUE_ID = "REC ID"
   TGT_UNIQUE_ID = "Record ID"
   SOT_TO_TGT_COLUMN_MAPPING = {
       "REC Name": "Record Name",
       "Description": "Description",
       "Owner": "Owner",
       "Status": "Status",
       "Test Method": "Test Method",
       "Test Procedure": "Test Procedure",
       "Manual Procedure": "Manual Procedure",
       "Automated Procedure": "Automated Procedure",
       "Severity": "Severity",
   }
   ```
