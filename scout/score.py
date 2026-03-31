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
        bucket = "SKIP"

    return {"score": score, "bucket": bucket, "reasons": reasons, "absentee": absentee}


# ── Profile scoring (8 operator-fit dimensions, 1–3 scale) ─────────────────────

def profile_score(l: dict) -> dict:
    """
    Score a listing on 8 operator-fit dimensions, each 1–3.
    1 = low / unfavorable, 2 = moderate, 3 = high / favorable.
    """
    title    = (l.get("title")       or "").lower()
    desc     = (l.get("description") or "").lower()
    industry = (l.get("industry")    or "").lower()
    ctx = f"{title} {desc} {industry}"

    absentee = l.get("absentee", "No")

    # ── AI-Proof ───────────────────────────────────────────────────────────────
    # 3 = physical/hands-on (very hard to automate)
    # 2 = mixed
    # 1 = knowledge/digital (automatable)
    _ai_proof_high = [
        "plumb", "electrical", "electrician", "hvac", "heating", "cooling",
        "roofing", "roofer", "concrete", "masonry", "welding", "welder",
        "auto repair", "auto body", "collision", "mechanic", "tire",
        "landscaping", "lawn care", "snow removal", "excavat",
        "pest control", "restoration", "physical therapy", "chiropractic",
        "dental", "veterinar", "home health", "senior care", "elder care",
        "construction", "flooring", "painting contractor", "insulation",
        "septic", "drain", "refrigeration", "towing",
    ]
    _ai_proof_low = [
        "accounting", "bookkeeping", "tax preparation", "financial planning",
        "insurance agency", "staffing", "consulting", "digital", "software",
        "it service", "managed service", "web design", "marketing agency",
        "payroll", "mortgage", "lending",
    ]
    if any(kw in ctx for kw in _ai_proof_high):
        dim_ai_proof = 3
    elif any(kw in ctx for kw in _ai_proof_low):
        dim_ai_proof = 1
    else:
        dim_ai_proof = 2

    # ── Fun ────────────────────────────────────────────────────────────────────
    # 3 = consumer-facing, entertaining, hospitality, retail
    # 2 = some customer interaction
    # 1 = back-office, industrial, B2B only
    _fun_high = [
        "restaurant", "bar ", "brewery", "brewpub", "cafe", "coffee",
        "retail", "boutique", "gift shop", "clothing", "pet store",
        "salon", "spa", "fitness", "gym", "yoga", "crossfit",
        "hotel", "motel", "resort", "lodge", "bed and breakfast",
        "entertainment", "recreation", "arcade", "bowling",
        "bakery", "donut", "food truck", "catering",
        "florist", "flower", "toy store", "book store",
        "childcare", "daycare", "dance studio", "martial arts",
        "veterinar", "animal hospital",
    ]
    _fun_low = [
        "manufacturing", "fabrication", "machining", "industrial",
        "distribution", "warehouse", "trucking", "freight", "wholesale",
        "staffing", "payroll", "accounting", "bookkeeping", "tax",
        "b2b", "commercial only", "government contract",
    ]
    if any(kw in ctx for kw in _fun_high):
        dim_fun = 3
    elif any(kw in ctx for kw in _fun_low):
        dim_fun = 1
    else:
        dim_fun = 2

    # ── Weather Dependent ──────────────────────────────────────────────────────
    # 3 = year-round (good), 2 = some seasonality, 1 = highly seasonal (risky)
    _weather_high = [
        "lawn care", "lawn service", "landscaping", "landscape",
        "snow removal", "snow plow", "irrigation", "sprinkler",
        "outdoor construction", "excavat", "outdoor",
        "tree service", "tree removal", "leaf removal",
        "pressure wash", "deck", "fence install",
        "swimming pool", "seasonal",
    ]
    _weather_low = [
        "hvac", "plumbing", "electrical", "healthcare", "medical",
        "dental", "retail", "restaurant", "cleaning", "janitorial",
        "accounting", "manufacturing", "distribution", "trucking",
        "auto repair", "home health", "senior care",
    ]
    if any(kw in ctx for kw in _weather_high):
        dim_weather = 1
    elif any(kw in ctx for kw in _weather_low):
        dim_weather = 3
    else:
        dim_weather = 2

    # ── Manual Labor ───────────────────────────────────────────────────────────
    # 3 = heavy physical workforce, 2 = mixed, 1 = knowledge/light
    _labor_high = [
        "plumb", "electrical", "hvac", "roofing", "concrete", "masonry",
        "landscaping", "excavat", "construction", "manufacturing",
        "fabrication", "welding", "moving", "trucking", "distribution",
        "warehouse", "janitorial", "cleaning service", "pest control",
        "auto repair", "auto body", "towing", "insulation", "painting contractor",
    ]
    _labor_low = [
        "accounting", "bookkeeping", "financial", "insurance", "consulting",
        "staffing", "software", "it service", "managed service",
        "real estate", "mortgage", "tax preparation",
    ]
    if any(kw in ctx for kw in _labor_high):
        dim_labor = 3
    elif any(kw in ctx for kw in _labor_low):
        dim_labor = 1
    else:
        dim_labor = 2

    # ── Recurring Revenue ──────────────────────────────────────────────────────
    # 3 = strong recurring, 2 = some, 1 = transactional
    _recurring_strong = [
        "service contract", "maintenance agreement", "recurring revenue",
        "annual contract", "subscription", "retainer", "route based",
        "route-based", "service route", "maintenance plan",
        "managed service", "membership",
    ]
    _recurring_some = [
        "repeat customer", "loyal customer", "repeat business",
        "established clientele", "long-term client", "regular customer",
    ]
    count_strong = sum(1 for kw in _recurring_strong if kw in ctx)
    count_some   = sum(1 for kw in _recurring_some   if kw in ctx)
    if count_strong >= 1:
        dim_recurring = 3
    elif count_some >= 1:
        dim_recurring = 2
    else:
        dim_recurring = 1

    # ── Absentee-Friendly ──────────────────────────────────────────────────────
    # 3 = likely absentee, 2 = possible, 1 = owner-operated
    if absentee == "Likely":
        dim_absentee = 3
    elif absentee == "Possible":
        dim_absentee = 2
    else:
        dim_absentee = 1

    # ── Capital Light ──────────────────────────────────────────────────────────
    # 3 = minimal assets/inventory, 2 = moderate, 1 = heavy assets
    _capital_heavy = [
        "manufacturing", "fabrication", "machining", "equipment intensive",
        "heavy equipment", "fleet", "trucking", "warehouse", "distribution",
        "real estate included", "building included", "inventory",
        "restaurant", "food service",  # high equipment + leasehold
    ]
    _capital_light = [
        "service-based", "no inventory", "home-based", "home based",
        "cleaning", "janitorial", "staffing", "consulting", "accounting",
        "bookkeeping", "lawn care", "pest control", "home health",
        "elder care", "senior care", "tutoring", "coaching",
    ]
    if any(kw in ctx for kw in _capital_light):
        dim_capital_light = 3
    elif any(kw in ctx for kw in _capital_heavy):
        dim_capital_light = 1
    else:
        dim_capital_light = 2

    # ── Scalable ───────────────────────────────────────────────────────────────
    # 3 = easy to add locations/routes/units, 2 = some potential, 1 = owner-capped
    _scalable_high = [
        "multiple location", "multi-location", "additional location",
        "scalable", "franchise", "route", "territory",
        "cleaning", "janitorial", "lawn care", "pest control",
        "staffing", "home health", "elder care", "tutoring",
        "systems in place", "process driven", "documented process",
        "turnkey", "replicable",
    ]
    _scalable_low = [
        "owner operator", "sole proprietor", "owner-operated",
        "boutique", "bespoke", "custom", "artisan",
        "single location", "one location",
    ]
    if any(kw in ctx for kw in _scalable_high):
        dim_scalable = 3
    elif any(kw in ctx for kw in _scalable_low):
        dim_scalable = 1
    else:
        dim_scalable = 2

    return {
        "dim_ai_proof":      dim_ai_proof,
        "dim_fun":           dim_fun,
        "dim_weather":       dim_weather,
        "dim_labor":         dim_labor,
        "dim_recurring":     dim_recurring,
        "dim_absentee":      dim_absentee,
        "dim_capital_light": dim_capital_light,
        "dim_scalable":      dim_scalable,
    }
