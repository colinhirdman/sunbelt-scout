import re


def parse_listings(raw_listings: list[dict]) -> list[dict]:
    """Normalize raw scraped dicts into scored-ready format with SBA financials."""
    out = {}

    for item in raw_listings:
        lid = item.get("id_number", "")
        if not lid:
            continue

        asking = _parse_dollar(item.get("asking_price_text"))
        annual_cf = _parse_dollar(item.get("cash_flow_text"))
        annual_rev = _parse_dollar(item.get("revenue_text"))
        employees_ft = _to_int(item.get("employees_ft"))
        employees_pt = _to_int(item.get("employees_pt"))
        employees = None
        if employees_ft is not None:
            employees = employees_ft + (employees_pt or 0)

        # Derive SBA financials for both 10% and 20% down scenarios
        financials = _derive_financials(asking, annual_cf)

        out[lid] = {
            "id": lid,
            "title": (item.get("title") or "")[:200],
            "url": item.get("detail_url", ""),
            "industry": item.get("industry", ""),
            "location": item.get("location", ""),
            "asking_price": asking,
            "asking_price_text": _format_price(asking),
            "annual_cash_flow": annual_cf,
            "annual_revenue": annual_rev,
            "employees": employees,
            "description": (item.get("description") or "")[:2000],
            "years_in_business": item.get("years_in_business", ""),
            "is_franchise": item.get("is_franchise", ""),
            "reason_for_selling": item.get("reason_for_selling", ""),
            "sba_available": item.get("sba_available", ""),
            "real_estate": item.get("real_estate", ""),
            "listing_agent": item.get("listing_agent", ""),
            "absentee_owner_field": item.get("absentee_owner_field", ""),
            **financials,
        }

    return list(out.values())


def _derive_financials(asking, annual_cf):
    """Derive all SBA modeling fields for 10% and 20% down scenarios."""
    result = {
        "down_10": None, "down_20": None,
        "sba_loan_90": None, "sba_loan_80": None,
        "sba_monthly_10pct": None, "sba_monthly_20pct": None,
        "annual_debt_service_10pct": None, "annual_debt_service_20pct": None,
        "cf_after_debt_10pct": None, "cf_after_debt_20pct": None,
        "coc_return_10pct": None, "coc_return_20pct": None,
        "dscr_10pct": None, "dscr_20pct": None,
        "payoff_years_10pct": None, "payoff_years_20pct": None,
    }

    if not asking or asking <= 0:
        return result

    down_10 = round(asking * 0.10, 2)
    down_20 = round(asking * 0.20, 2)
    loan_90 = round(asking * 0.90, 2)
    loan_80 = round(asking * 0.80, 2)

    monthly_10 = _sba_payment(loan_90)
    monthly_20 = _sba_payment(loan_80)

    result["down_10"] = down_10
    result["down_20"] = down_20
    result["sba_loan_90"] = loan_90
    result["sba_loan_80"] = loan_80
    result["sba_monthly_10pct"] = monthly_10
    result["sba_monthly_20pct"] = monthly_20

    if monthly_10:
        result["annual_debt_service_10pct"] = round(monthly_10 * 12, 2)
    if monthly_20:
        result["annual_debt_service_20pct"] = round(monthly_20 * 12, 2)

    if annual_cf is not None and annual_cf > 0:
        if result["annual_debt_service_10pct"]:
            cf_after_10 = round(annual_cf - result["annual_debt_service_10pct"], 2)
            result["cf_after_debt_10pct"] = cf_after_10
            result["dscr_10pct"] = round(annual_cf / result["annual_debt_service_10pct"], 2)
            if down_10 > 0:
                result["coc_return_10pct"] = round(cf_after_10 / down_10, 4)
            if cf_after_10 > 0 and down_10 > 0:
                result["payoff_years_10pct"] = round(down_10 / cf_after_10, 2)

        if result["annual_debt_service_20pct"]:
            cf_after_20 = round(annual_cf - result["annual_debt_service_20pct"], 2)
            result["cf_after_debt_20pct"] = cf_after_20
            result["dscr_20pct"] = round(annual_cf / result["annual_debt_service_20pct"], 2)
            if down_20 > 0:
                result["coc_return_20pct"] = round(cf_after_20 / down_20, 4)
            if cf_after_20 > 0 and down_20 > 0:
                result["payoff_years_20pct"] = round(down_20 / cf_after_20, 2)

    return result


def _sba_payment(principal, annual_rate=0.10, years=10):
    """Monthly payment for SBA loan: 10% interest, 10-year amortization."""
    if not principal or principal <= 0:
        return None
    r = annual_rate / 12
    n = years * 12
    payment = principal * (r * (1 + r) ** n) / ((1 + r) ** n - 1)
    return round(payment, 2)


def _parse_dollar(text):
    """Parse dollar string like '$1,219,947' to float."""
    if not text:
        return None
    cleaned = re.sub(r'[^\d.]', '', str(text))
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _format_price(val):
    if val is not None:
        return f"${val:,.0f}"
    return ""


def _to_int(val):
    if val is None:
        return None
    try:
        return int(re.sub(r'[^\d]', '', str(val)))
    except (ValueError, TypeError):
        return None
