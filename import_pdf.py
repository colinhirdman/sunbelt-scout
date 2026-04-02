"""
import_pdf.py  —  Extract deal data from a broker PDF and update Scout.

Usage:
    python3 import_pdf.py ~/Downloads/deal.pdf
    python3 import_pdf.py ~/Downloads/deal.pdf --id calhoun_some-slug   # force match
    python3 import_pdf.py ~/Downloads/deal.pdf --dry-run                 # preview only

Requires:
    ANTHROPIC_API_KEY environment variable
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path

try:
    from pdfminer.high_level import extract_text
except ImportError:
    print("Missing pdfminer.six — run: pip install pdfminer.six")
    sys.exit(1)

try:
    import anthropic
except ImportError:
    print("Missing anthropic — run: pip install anthropic")
    sys.exit(1)

SUNBELT_CSV = Path(__file__).parent / "output" / "sunbelt.csv"
CALHOUN_CSV = Path(__file__).parent / "output" / "calhoun.csv"

EXTRACT_PROMPT = """You are extracting structured business listing data from a broker PDF.

Return ONLY a valid JSON object with these fields (use null for anything not found):

{
  "business_name":       string or null,   // actual business name, not broker title
  "asking_price":        number or null,   // numeric only, no $ or commas
  "annual_cash_flow":    number or null,   // SDE / adjusted net income, numeric only
  "annual_revenue":      number or null,   // gross sales / revenue, numeric only
  "employees":           number or null,   // total headcount (FT + PT)
  "years_in_business":   string or null,
  "reason_for_selling":  string or null,
  "location":            string or null,   // city, state preferred
  "industry":            string or null,
  "listing_agent":       string or null,
  "is_franchise":        string or null,   // "Yes" or "No"
  "sba_available":       string or null,   // "Yes" or "No"
  "description":         string or null,   // 2-3 sentence summary of the business
  "broker_listing_id":   string or null,   // any ID number from the broker (e.g. "11937")
  "source_broker":       string or null    // broker company name
}

PDF text:
"""


def extract_pdf_text(pdf_path: str) -> str:
    text = extract_text(pdf_path)
    # Trim to ~12k chars to keep token cost low
    return text[:12000]


def call_claude(pdf_text: str) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("Error: ANTHROPIC_API_KEY environment variable not set.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": EXTRACT_PROMPT + pdf_text}],
    )
    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    return json.loads(raw)


def load_all_rows() -> list[dict]:
    rows = []
    for path in [SUNBELT_CSV, CALHOUN_CSV]:
        if path.exists():
            with path.open("r", newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    r["_csv_path"] = str(path)
                    rows.append(r)
    return rows


def find_match(rows: list[dict], extracted: dict, force_id: str = None):
    if force_id:
        match = next((r for r in rows if r["id"] == force_id), None)
        if not match:
            print(f"No listing found with id: {force_id}")
        return match

    # Match by broker listing ID — require it to be a standalone token, not a substring
    broker_id = extracted.get("broker_listing_id")
    if broker_id:
        import re
        pattern = re.compile(rf'(?<![0-9]){re.escape(broker_id)}(?![0-9])')
        for r in rows:
            if pattern.search(r.get("title", "")):
                return r

    # Match by price + cash flow (within 1%)
    price = extracted.get("asking_price")
    cf    = extracted.get("annual_cash_flow")
    if price and cf:
        for r in rows:
            try:
                rp = float(r.get("asking_price") or 0)
                rc = float(r.get("annual_cash_flow") or 0)
                if abs(rp - price) / price < 0.01 and abs(rc - cf) / cf < 0.01:
                    return r
            except (ValueError, ZeroDivisionError):
                continue

    # Match by business name substring
    name = (extracted.get("business_name") or "").lower()
    if name:
        for r in rows:
            if name in r.get("title", "").lower() or r.get("title", "").lower() in name:
                return r

    return None


def build_updates(row: dict, extracted: dict) -> dict:
    """Return only the fields that would change."""
    FIELD_MAP = {
        "business_name":      "title",
        "asking_price":       "asking_price",
        "annual_cash_flow":   "annual_cash_flow",
        "annual_revenue":     "annual_revenue",
        "employees":          "employees",
        "years_in_business":  "years_in_business",
        "reason_for_selling": "reason_for_selling",
        "location":           "location",
        "industry":           "industry",
        "listing_agent":      "listing_agent",
        "is_franchise":       "is_franchise",
        "sba_available":      "sba_available",
        "description":        "description",
    }
    updates = {}
    for ext_key, csv_key in FIELD_MAP.items():
        new_val = extracted.get(ext_key)
        if new_val is None:
            continue
        old_val = row.get(csv_key, "")
        new_str = str(new_val) if not isinstance(new_val, str) else new_val
        if new_str and new_str != str(old_val):
            updates[csv_key] = {"old": old_val, "new": new_str}
    return updates


def apply_updates(row: dict, updates: dict, csv_path: str):
    path = Path(csv_path)
    all_rows = []
    fieldnames = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            all_rows.append(r)

    for r in all_rows:
        if r["id"] == row["id"]:
            for field, change in updates.items():
                if field in r:
                    r[field] = change["new"]
            if "has_pdf" in r:
                r["has_pdf"] = "True"
            break

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in all_rows:
            writer.writerow(r)


def main():
    parser = argparse.ArgumentParser(description="Import broker PDF into Scout")
    parser.add_argument("pdf", help="Path to the broker PDF")
    parser.add_argument("--id", dest="force_id", help="Force match to this listing ID")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without saving")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser()
    if not pdf_path.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    print(f"Reading {pdf_path.name}...")
    pdf_text = extract_pdf_text(str(pdf_path))

    print("Extracting fields with Claude...")
    extracted = call_claude(pdf_text)

    print("\n── Extracted ──────────────────────────────")
    for k, v in extracted.items():
        if v is not None:
            print(f"  {k}: {v}")

    rows = load_all_rows()
    match = find_match(rows, extracted, force_id=args.force_id)

    if not match:
        print("\nNo matching listing found in Scout.")
        print("Use --id <listing_id> to force a match.")
        sys.exit(1)

    print(f"\n── Matched: {match['id']} ─────────────────────")
    print(f"  Title:  {match.get('title')}")
    print(f"  Source: {match.get('source')} | CSV: {Path(match['_csv_path']).name}")

    updates = build_updates(match, extracted)

    if not updates:
        print("\nNo changes — Scout already has this data.")
        sys.exit(0)

    print("\n── Proposed changes ────────────────────────")
    for field, change in updates.items():
        old = change["old"] or "(empty)"
        new = change["new"]
        print(f"  {field}:")
        print(f"    before: {old}")
        print(f"    after:  {new}")

    if args.dry_run:
        print("\nDry run — no changes saved.")
        sys.exit(0)

    confirm = input("\nApply changes? [y/N] ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        sys.exit(0)

    apply_updates(match, updates, match["_csv_path"])
    print(f"\nUpdated {match['id']} in {Path(match['_csv_path']).name}")


if __name__ == "__main__":
    main()
