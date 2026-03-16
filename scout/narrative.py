def generate_narrative(listing: dict) -> str:
    """
    Generate a plain-English deal narrative from scored listing data.
    Returns a 3-paragraph string: strengths, concerns, bottom line.
    """
    title    = listing.get("title", "This business")
    industry = listing.get("industry", "")
    location = listing.get("location", "")
    asking   = listing.get("asking_price")
    cf       = listing.get("annual_cash_flow")
    rev      = listing.get("annual_revenue")
    score    = listing.get("score", 0)
    bucket   = listing.get("bucket", "")
    absentee = listing.get("absentee", "No")
    employees = listing.get("employees")
    dscr20   = listing.get("dscr_20pct")
    coc20    = listing.get("coc_return_20pct")
    cf20     = listing.get("cf_after_debt_20pct")
    reasons  = listing.get("reasons", [])
    if isinstance(reasons, str):
        reasons = [r.strip() for r in reasons.split(";") if r.strip()]
    yib      = listing.get("years_in_business", "")
    is_franchise = str(listing.get("is_franchise", "")).lower()
    sba      = str(listing.get("sba_available", "")).lower()
    reason_selling = listing.get("reason_for_selling", "")

    # ── Intro ──────────────────────────────────────────────────────────────────
    parts = []

    loc_str  = f" in {location}" if location else ""
    ind_str  = f" ({industry})" if industry else ""
    age_str  = f", {yib} years in operation" if yib else ""
    price_str = f"${asking:,.0f}" if asking else "an undisclosed price"
    cf_str   = f"${cf:,.0f}" if cf else "undisclosed"
    rev_str  = f"${rev:,.0f}" if rev else None

    intro = f"{title}{ind_str}{loc_str} is listed at {price_str}"
    if cf:
        intro += f" with {cf_str} in annual cash flow (SDE)"
    if rev_str:
        intro += f" and {rev_str} in gross revenue"
    intro += f"{age_str}."
    parts.append(intro)

    # ── Strengths ──────────────────────────────────────────────────────────────
    strengths = []

    if cf and cf >= 300000:
        strengths.append(f"cash flow of {cf_str} is strong and well above our preferred threshold")
    elif cf and cf >= 150000:
        strengths.append(f"cash flow of {cf_str} is solid")
    elif cf and cf >= 75000:
        strengths.append(f"cash flow of {cf_str} meets our minimum threshold")

    if dscr20 and dscr20 >= 1.5:
        strengths.append(f"DSCR of {dscr20:.2f}x at 20% down is comfortable — well above the SBA minimum")
    elif dscr20 and dscr20 >= 1.25:
        strengths.append(f"DSCR of {dscr20:.2f}x at 20% down clears the SBA minimum")

    if coc20 and coc20 >= 0.30:
        strengths.append(f"cash-on-cash return of {coc20:.0%} at 20% down is excellent")
    elif coc20 and coc20 >= 0.20:
        strengths.append(f"cash-on-cash return of {coc20:.0%} at 20% down is attractive")
    elif coc20 and coc20 >= 0.15:
        strengths.append(f"cash-on-cash return of {coc20:.0%} at 20% down is acceptable")

    if absentee == "Likely":
        strengths.append("current owner is absentee — well-suited for a new owner-operator or passive investor")
    elif absentee == "Possible":
        strengths.append("owner involvement appears minimal, which may make the transition easier")

    if any("recurring revenue" in r.lower() for r in reasons):
        strengths.append("recurring or contract revenue provides predictable cash flow")

    if any("durable industry" in r.lower() for r in reasons):
        strengths.append(f"the {industry.lower() or 'industry'} is considered recession-resistant")

    if any("tech opportunity" in r.lower() for r in reasons):
        strengths.append("the business shows signs of operational tech gaps — a potential value-add opportunity post-acquisition")

    if employees and employees < 10:
        strengths.append(f"small team of {employees} keeps operations lean and manageable")

    if sba in ("yes", "true"):
        strengths.append("SBA financing is available, lowering the capital barrier to entry")

    if strengths:
        parts.append("What's attractive: " + "; ".join(strengths) + ".")
    else:
        parts.append("No standout strengths were identified from the available data.")

    # ── Concerns ───────────────────────────────────────────────────────────────
    concerns = []

    if dscr20 and dscr20 < 1.35:
        concerns.append(f"DSCR of {dscr20:.2f}x at 20% down is thin — leaves little cushion if revenue dips")

    if coc20 is not None and coc20 < 0.15:
        concerns.append(f"cash-on-cash return of {coc20:.0%} is below our 15% target")

    if cf20 is not None and cf20 < 50000:
        concerns.append(f"only ${cf20:,.0f} remains after SBA debt at 20% down — limited owner salary buffer")

    if employees and employees >= 50:
        concerns.append(f"large team of {employees} adds operational complexity and payroll risk")
    elif employees and employees >= 20:
        concerns.append(f"team of {employees} is mid-sized — management overhead to consider")

    if absentee == "No" and not any("absentee" in r.lower() for r in reasons):
        concerns.append("no absentee signals — likely owner-operated and may be dependent on the current owner")

    if "yes" in is_franchise or "franchise" in is_franchise:
        concerns.append("franchise resale means ongoing royalties and franchisor approval — adds friction and cost")

    if not cf:
        concerns.append("cash flow data is missing — cannot model returns without seller verification")

    if not asking:
        concerns.append("asking price is not disclosed — makes valuation comparison difficult")

    if reason_selling and any(w in reason_selling.lower() for w in ["health", "illness", "sick"]):
        concerns.append(f"reason for selling ({reason_selling}) may indicate urgency — worth verifying business condition")
    elif reason_selling and "retirement" in reason_selling.lower():
        concerns.append("seller is retiring — transition plan and key-person risk should be investigated")

    if concerns:
        parts.append("Watch-outs: " + "; ".join(concerns) + ".")
    else:
        parts.append("No significant concerns identified from the available data.")

    # ── Bottom line ────────────────────────────────────────────────────────────
    if bucket == "SHORTLIST":
        verdict = f"Bottom line: Strong candidate (score {score}/100). Worth requesting financials and scheduling a broker call."
    elif bucket == "REVIEW":
        if score >= 50:
            verdict = f"Bottom line: Decent opportunity (score {score}/100) but not a clear standout. Dig into the financials before committing time."
        else:
            verdict = f"Bottom line: Marginal fit (score {score}/100). Proceed only if something specific about this deal appeals beyond the numbers."
    elif bucket == "AUTO-REJECT":
        verdict = "Bottom line: Auto-rejected — does not meet baseline criteria."
    else:
        verdict = f"Bottom line: Score of {score}/100 — below review threshold. Pass unless there is a specific strategic reason to look closer."

    parts.append(verdict)

    return " ".join(parts)
