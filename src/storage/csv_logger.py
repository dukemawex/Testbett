import csv
import os
from typing import List, Dict


def append_run_log(filepath: str, records: List[Dict]) -> None:
    """Append bet records to CSV log file. Creates file with header if not exists."""
    if not records:
        return

    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

    fieldnames = list(records[0].keys())
    file_exists = os.path.isfile(filepath)

    with open(filepath, "a", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerows(records)
