import json
import csv
from pathlib import Path
from datetime import datetime

FIELDNAMES = [
    "id", "title", "url", "industry", "location",
    "asking_price", "asking_price_text",
    "annual_cash_flow", "annual_revenue", "employees",
    "down_10", "sba_monthly_10pct", "annual_debt_service_10pct",
    "cf_after_debt_10pct", "coc_return_10pct", "dscr_10pct", "payoff_years_10pct",
    "down_20", "sba_monthly_20pct", "annual_debt_service_20pct",
    "cf_after_debt_20pct", "coc_return_20pct", "dscr_20pct", "payoff_years_20pct",
    "seller_note_amount", "seller_note_monthly", "seller_note_annual",
    "cf_during_standby", "cf_after_seller_financing", "dscr_seller_financed",
    "score", "bucket", "absentee", "reasons", "is_trades",
    "years_in_business", "is_franchise", "reason_for_selling",
    "sba_available", "listing_agent", "narrative",
    "dim_ai_proof", "dim_fun", "dim_weather", "dim_labor",
    "dim_recurring", "dim_absentee", "dim_capital_light", "dim_scalable",
    "last_seen", "is_active",
]


def _base():
    return Path(__file__).resolve().parents[1]


def load_state():
    p = _base() / "data" / "state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        return json.loads(p.read_text())
    return {"seen_ids": []}


def save_state(state: dict):
    p = _base() / "data" / "state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2))


def _num(val):
    if val is None:
        return ""
    return str(val)


def upsert_rows(rows: list[dict], active_ids=None):
    out = _base() / "output"
    out.mkdir(parents=True, exist_ok=True)
    p = out / "candidates.csv"

    existing = {}
    if p.exists():
        with p.open("r", newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                existing[r["id"]] = r

    for r in rows:
        existing[r["id"]] = {
            "id": r.get("id", ""),
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "industry": r.get("industry", ""),
            "location": r.get("location", ""),
            "asking_price": _num(r.get("asking_price")),
            "asking_price_text": r.get("asking_price_text", ""),
            "annual_cash_flow": _num(r.get("annual_cash_flow")),
            "annual_revenue": _num(r.get("annual_revenue")),
            "employees": _num(r.get("employees")),
            "down_10": _num(r.get("down_10")),
            "sba_monthly_10pct": _num(r.get("sba_monthly_10pct")),
            "annual_debt_service_10pct": _num(r.get("annual_debt_service_10pct")),
            "cf_after_debt_10pct": _num(r.get("cf_after_debt_10pct")),
            "coc_return_10pct": _num(r.get("coc_return_10pct")),
            "dscr_10pct": _num(r.get("dscr_10pct")),
            "payoff_years_10pct": _num(r.get("payoff_years_10pct")),
            "down_20": _num(r.get("down_20")),
            "sba_monthly_20pct": _num(r.get("sba_monthly_20pct")),
            "annual_debt_service_20pct": _num(r.get("annual_debt_service_20pct")),
            "cf_after_debt_20pct": _num(r.get("cf_after_debt_20pct")),
            "coc_return_20pct": _num(r.get("coc_return_20pct")),
            "dscr_20pct": _num(r.get("dscr_20pct")),
            "payoff_years_20pct": _num(r.get("payoff_years_20pct")),
            "seller_note_amount": _num(r.get("seller_note_amount")),
            "seller_note_monthly": _num(r.get("seller_note_monthly")),
            "seller_note_annual": _num(r.get("seller_note_annual")),
            "cf_during_standby": _num(r.get("cf_during_standby")),
            "cf_after_seller_financing": _num(r.get("cf_after_seller_financing")),
            "dscr_seller_financed": _num(r.get("dscr_seller_financed")),
            "score": str(r.get("score", "")),
            "bucket": r.get("bucket", ""),
            "absentee": r.get("absentee", ""),
            "reasons": "; ".join(r.get("reasons", [])),
            "is_trades": str(r.get("is_trades", False)),
            "years_in_business": r.get("years_in_business", ""),
            "is_franchise": r.get("is_franchise", ""),
            "reason_for_selling": r.get("reason_for_selling", ""),
            "sba_available": r.get("sba_available", ""),
            "listing_agent": r.get("listing_agent", ""),
            "narrative": r.get("narrative", ""),
            "dim_ai_proof":      _num(r.get("dim_ai_proof")),
            "dim_fun":           _num(r.get("dim_fun")),
            "dim_weather":       _num(r.get("dim_weather")),
            "dim_labor":         _num(r.get("dim_labor")),
            "dim_recurring":     _num(r.get("dim_recurring")),
            "dim_absentee":      _num(r.get("dim_absentee")),
            "dim_capital_light": _num(r.get("dim_capital_light")),
            "dim_scalable":      _num(r.get("dim_scalable")),
            "last_seen": datetime.utcnow().isoformat(),
            "is_active": "True",
        }

    # Mark rows no longer in the current scrape as inactive
    if active_ids is not None:
        for rid, row in existing.items():
            if rid not in active_ids:
                row["is_active"] = "False"

    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        w.writeheader()
        for row in existing.values():
            w.writerow(row)
