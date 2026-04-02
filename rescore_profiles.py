"""
Retroactively adds 8 operator-fit dimension scores to all existing
listings in candidates.csv without re-scraping or re-scoring financials.
"""
import csv
from pathlib import Path
from datetime import datetime
from scout.score import profile_score
from scout.storage import FIELDNAMES

CSV_PATH = Path(__file__).parent / "output" / "sunbelt.csv"


def main():
    if not CSV_PATH.exists():
        print("No candidates.csv found.")
        return

    with CSV_PATH.open("r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Scoring {len(rows)} listings...")

    for i, row in enumerate(rows):
        scores = profile_score(row)
        row.update({k: str(v) for k, v in scores.items()})

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    print(f"Done. Profile scores written to {CSV_PATH}")


if __name__ == "__main__":
    main()
