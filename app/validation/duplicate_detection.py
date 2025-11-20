from typing import List, Dict


def ensure_no_duplicate_ids(rows: List[Dict[str, str]], unique_id_col: str, label: str):
    """
    Fatal validation: Ensure no duplicate Unique IDs in SOT/TGT.
    """
    seen = set()
    duplicates = []

    for r in rows:
        uid = r.get(unique_id_col)
        if uid in seen:
            duplicates.append(uid)
        else:
            seen.add(uid)

    if duplicates:
        raise ValueError(
            f"{label}: duplicate IDs found in '{unique_id_col}': "
            + ", ".join(str(d) for d in duplicates)
        )
