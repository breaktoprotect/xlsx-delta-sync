# Description

This tool allows users to synchronize data between a main “source of truth” (SOT) spreadsheet and one or more target (TGT) spreadsheets. Instead of manually editing multiple copies whenever changes are made, users can simply update the SOT and run this tool to propagate those updates to the target files.

# Initial set-up required

- Source of Truth (SOT): The primary spreadsheet containing the authoritative data.
- Unique ID: A column in both the SOT and TGT that uniquely identifies each record, serving as the key. This ID is used to match and update corresponding records in the TGT. This is case-sensitive and mandatory. For example, a record may have a unique ID that is "REC-1234" or UUID format or just a running number.

# Mechanics

- Load both SOT and TGT spreadsheets
- Initial validations/checks:
  - Scan SOT list of records to ensure no duplicates. Raise fatal error if found any.
  - Scan SOT and TGT columns to ensure that the mapped columns exist. Raise fatal error if found any mismatched columns based on mappings.
- Comparison logic: Even if there is any slight changes whether an extra space character or caps difference in TGT, SOT will update that cell.
- Loop SOT records. Create new TGT list of records.
  - If record (based on unique ID) exist in TGT, compare each mapped columns.
- Finally, export new TGT spreadsheet as output with datetime. Output filename should be: `<initial*tgt_filename>_updated*<YYYMMDD_HHMM>.xlsx`

# Format preservation of TGT

- For XLSX, the TGT Excel should be preserved such as:
  -- Cell fill colors

# Rules & Assumptions

- SOT values are always the truth. If TGT contain values that differ from SOT, SOT will update those values.
- Values comparison and update is anchored by specified unique ID.
- All values are assumed to be String
- Column names can differ thus SOT columns must be mapped to TGT columns through config file (or in future, a GUI).
- If a record exist in SOT but not in TGT, it will be added to new TGT.
- Unmapped columns in TGT should never be updated.
- It is ok if TGT have more or less columns (fields) compared to SOT. SOT will update only if the column is mapped. Unmapped columns will be ignored.
- This is date dependent. SOT as by its name, will always be the 'Source of Truth'.
- Total records in SOT or TGT, don't exceed 10000 records each. Can still work in larger XLSX but may be slower or run of memory in older machines.

# Guardrails & Observability

- Never overwrite any existing input files be it SOT or TGT - a new output i.e. updated TGT is to be created as a new file.
- Any updates must be logged into a log file. Logging to use `loguru`
  (.e.g REC-123 "column_x", "column_z" have been updated.) OR
  (e.g. REC-421 has been added.)
- (future) Produce a summary of diff between the SOT and TGT in a easily readable fashion (e.g. similar to code diff) after all the operations have been completed.
- Raise error in SOT a record is missing unique ID
-

# Features, UI & Support

- Python 3
- Local app
- Encoding: UTF-8
- Supports command-line via invocation of the script (i.e. running main script)
- Supports XLSX
- (future) To support CSV
- (future) To have Flet GUI

# FAQ

Q: Any plans to expand to multiple TGT spreadsheets?
A: No, this is meant to be a simple and straight forward tool. While we will eventually support multiple config per SOT-TGT pair, the tool will update one TGT at a time.

Q: Why no dry mode?
A: Existing input files are not touched. Logs will already provide what's being updated alongside the new output file. Dry mode doesn't seem very useful.

# Bugs to fix:

(DONE) Provide 'input_files' for SOT and TGT. Set .gitignore to ignore this folder
(DONE) config.py should include sheet as well.
(DONE) read_sot_xlsx() and read_tgt_xlsx() in xlsx_io.py should not allow optional and must define "sheet_name"
(Done) Logging is not reflected the fields correctly, resulting in '' empty previous string
(Done) Orphaned records to ignore "Retired" status. Generate diff report to ignore records without a valid record (based on config.py). Orphaned records to not display any contents - just ID.
(Done) Add a check for config.py. If a mapping is done, column on either side must exist in SOT or TGT else fatal error and exit program.
(Done) Improvement: diff report generation to ignore records without proper unique ID prefix
(Done) Bug: Records untouched are displayed in the logs. This is due to duplicates

# Features to add

(Done) Feature to detect TGT orphaned records (i.e. SOT don't have those records thus unable to update the TGT).
(Done) Feature: Duplicate detection as duplicates can cause alot of issues.

- Dry run mode (?)
