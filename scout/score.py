import yaml
from pathlib import Path

_criteria_cache = None


def _load_criteria():
    global _criteria_cache
    if _criteria_cache is None:
        base = Path(__file__).resolve().parents[1]
        _criteria_cache = yaml.safe_load((base / "criteria.yml").read_text())
    return _criteria_cache


def _detect_absentee(ctx: str, c: dict) -> str:
    """Scan text for absentee ownership signals."""
    for signal in c["absentee_signals"]["likely"]:
        if signal in ctx:
            return "Likely"
    for signal in c["absentee_signals"]["possible"]:
        if signal in ctx:
            return "Possible"
    return "No"


def score_listing(l: dict) -> dict:
    """
    Score a listing 0-100. Returns dict with score, bucket, reasons, absentee.
    """
    c = _load_criteria()

    title = (l.get("title") or "").lower()
    description = (l.get("description") or "").lower()
    industry = (l.get("industry") or "").lower()
    location = (l.get("location") or "").lower()
    ctx = f"{title} {description} {industry}"

    asking = l.get("asking_price")
    annual_cf = l.get("annual_cash_flow")
    dscr_20 = l.get("dscr_20pct")
    cf_after_20 = l.get("cf_after_debt_20pct")

    # Absentee detection — use structured field first, then text scan
    absentee_field = (l.get("absentee_owner_field") or "").lower().strip()
    if absentee_field == "yes":
        absentee = "Likely"
    else:
        absentee = _detect_absentee(ctx, c)

    # --- AUTO-REJECT checks ---

    # Missing financials
    if asking is None and annual_cf is None:
        return {"score": 0, "bucket": "AUTO-REJECT", "reasons": ["missing financials"], "absentee": absentee}

    # Out of price range
    if asking is not None:
        if asking < c["budget"]["min_asking_price"]:
            return {"score": 0, "bucket": "AUTO-REJECT", "reasons": [f"under min price ${asking:,.0f}"], "absentee": absentee}
        if asking > c["budget"]["max_asking_price"]:
            return {"score": 0, "bucket": "AUTO-REJECT", "reasons": [f"over max price ${asking:,.0f}"], "absentee": absentee}

    # No cash flow data
    if annual_cf is None:
        return {"score": 0, "bucket": "AUTO-REJECT", "reasons": ["no cash flow data"], "absentee": absentee}

    # DSCR too low
    if dscr_20 is not None and dscr_20 < c["targets"]["min_dscr"]:
        return {"score": 0, "bucket": "AUTO-REJECT", "reasons": [f"DSCR {dscr_20:.2f} below {c['targets']['min_dscr']}"], "absentee": absentee}

    # Negative cash flow after debt
    if cf_after_20 is not None and cf_after_20 < 0:
        return {"score": 0, "bucket": "AUTO-REJECT", "reasons": [f"negative CF after debt ${cf_after_20:,.0f}"], "absentee": absentee}

    # Not Minnesota
    if location and "minnesota" not in location:
        return {"score": 0, "bucket": "AUTO-REJECT", "reasons": [f"not Minnesota: {l.get('location', '')}"], "absentee": absentee}

    # Regulated keywords
    for kw in c["no_go"]["regulated_keywords"]:
        if kw in ctx:
            return {"score": 0, "bucket": "AUTO-REJECT", "reasons": [f"regulated: {kw}"], "absentee": absentee}

    # Digital keywords
    for kw in c["no_go"]["digital_keywords"]:
        if kw in ctx:
            return {"score": 0, "bucket": "AUTO-REJECT", "reasons": [f"digital/online: {kw}"], "absentee": absentee}

    # --- SCORING ---
    score = 0
    reasons = []
    w = c["weights"]

    # A. Financial Strength (40 pts max)
    fin_score = 0
    # Cash flow sub-score (20 pts)
    if annual_cf >= 300000:
        fin_score += 20
        reasons.append(f"strong CF ${annual_cf:,.0f}")
    elif annual_cf >= 150000:
        fin_score += 10
        reasons.append(f"decent CF ${annual_cf:,.0f}")
    elif annual_cf >= 75000:
        fin_score += 5
        reasons.append(f"modest CF ${annual_cf:,.0f}")
    else:
        reasons.append(f"low CF ${annual_cf:,.0f}")

    # DSCR sub-score (12 pts)
    if dscr_20 is not None:
        if dscr_20 >= 1.5:
            fin_score += 12
            reasons.append(f"DSCR {dscr_20:.2f}")
        elif dscr_20 >= 1.35:
            fin_score += 7
            reasons.append(f"DSCR {dscr_20:.2f}")
        elif dscr_20 >= 1.25:
            fin_score += 3
            reasons.append(f"DSCR {dscr_20:.2f}")

    # CoC return sub-score (8 pts)
    coc_20 = l.get("coc_return_20pct")
    if coc_20 is not None:
        if coc_20 >= 0.30:
            fin_score += 8
            reasons.append(f"CoC {coc_20:.0%}")
        elif coc_20 >= 0.20:
            fin_score += 5
            reasons.append(f"CoC {coc_20:.0%}")
        elif coc_20 >= 0.15:
            fin_score += 2
            reasons.append(f"CoC {coc_20:.0%}")

    score += min(fin_score, w["financial_strength"])

    # B. Operational Simplicity (15 pts max)
    ops_score = 0
    employees = l.get("employees")
    if employees is not None:
        if employees < 20:
            ops_score += 8
            reasons.append(f"{employees} employees")
        elif employees < 50:
            ops_score += 4
            reasons.append(f"{employees} employees")
        else:
            reasons.append(f"large team: {employees}")

    heavy_words = ["heavy inventory", "warehouse", "large inventory", "extensive inventory"]
    if not any(hw in ctx for hw in heavy_words):
        ops_score += 4
        reasons.append("no heavy inventory")

    simple_words = ["simple", "straightforward", "easy to run", "turnkey", "well-established"]
    if any(sw in ctx for sw in simple_words):
        ops_score += 3
        reasons.append("operationally simple")

    score += min(ops_score, w["operational_simplicity"])

    # C. Tech Deficiency Opportunity (15 pts max)
    tech_score = 0
    for signal in c["tech_deficiency_signals"]:
        if signal in ctx:
            tech_score += 3
    if tech_score > 0:
        reasons.append(f"tech opportunity ({min(tech_score, w['tech_deficiency'])} pts)")
    score += min(tech_score, w["tech_deficiency"])

    # D. Recurring/Contract Revenue (10 pts max)
    recurring_count = sum(1 for s in c["recurring_revenue_signals"] if s in ctx)
    if recurring_count >= 2:
        score += w["recurring_revenue"]
        reasons.append("recurring revenue (strong)")
    elif recurring_count == 1:
        score += 6
        reasons.append("recurring revenue signal")

    # E. Industry Durability (10 pts max)
    industry_match = False
    for ind in c["durable_industries"]:
        if ind in ctx:
            industry_match = True
            break
    if industry_match:
        score += w["industry_durability"]
        reasons.append("durable industry")

    # F. Geographic Fit (10 pts max)
    tc_signals = c["twin_cities_signals"]
    loc_lower = location
    if any(tc in loc_lower or tc in ctx for tc in tc_signals):
        score += w["geographic_fit"]
        reasons.append("Twin Cities area")
    elif "minnesota" in loc_lower:
        score += 5
        reasons.append("Minnesota (not TC)")

    # --- BUCKET ASSIGNMENT ---
    t = c["thresholds"]
    if score >= t["shortlist"]:
        bucket = "SHORTLIST"
    elif score >= t["review"]:
        bucket = "REVIEW"
    else:
        bucket = "REVIEW"

    return {"score": score, "bucket": bucket, "reasons": reasons, "absentee": absentee}
