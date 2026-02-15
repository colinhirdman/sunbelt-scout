import time
import re
import requests
import yaml
from pathlib import Path
from urllib.parse import urlencode, urljoin

HEADERS = {}
MAX_RETRIES = 3
BASE = Path(__file__).resolve().parents[1]


def _load_config():
    return yaml.safe_load((BASE / "sources.yml").read_text())["sunbelt"]


def _get_with_retry(url, params=None, cfg=None):
    delay = cfg.get("rate_limit_delay", 3.0) if cfg else 3.0
    ua = cfg.get("user_agent", "Mozilla/5.0") if cfg else "Mozilla/5.0"
    headers = {"User-Agent": ua}

    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=30)
            if r.status_code == 429:
                wait = 2 ** (attempt + 2)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** (attempt + 1))
            else:
                print(f"  Failed after {MAX_RETRIES} retries: {e}")
                return None
    return None


def _extract_ids_from_html(html):
    """Extract listing IDs from search results page HTML."""
    return set(re.findall(r'id_number=([A-Za-z0-9]{4,})', html))


def _discover_listing_ids(cfg):
    """
    Discover Minnesota listing IDs by hitting the search page with
    many different filter combinations. The server only returns 10
    listings per page in static HTML, so we vary filters to surface
    different subsets.
    """
    base_url = cfg["base_url"]
    delay = cfg.get("rate_limit_delay", 3.0)
    all_ids = set()

    def _fetch_search(extra_params=None):
        params = {"geography[]": "Minnesota"}
        if extra_params:
            params.update(extra_params)
        time.sleep(delay)
        html = _get_with_retry(base_url, params=params, cfg=cfg)
        if html:
            ids = _extract_ids_from_html(html)
            all_ids.update(ids)
            return len(ids)
        return 0

    # 1. Default (no extra filters)
    _fetch_search()

    # 2. By industry
    industries = [
        "Accounting", "Automotive", "Construction", "Distribution",
        "Franchise", "Home Health Care", "Hotels/Motels", "Manufacturing",
        "Medical/Optometry/Dental/Veterinary", "Real Estate",
        "Restaurant & Bar", "Retail", "Service", "Technology",
    ]
    for ind in industries:
        _fetch_search({"industry[]": ind})

    # 3. Cash flow ranges
    for cf_min in [25000, 50000, 75000, 100000, 150000, 200000, 300000, 500000, 750000, 1000000]:
        _fetch_search({"cash_flow_min": cf_min})
    for cf_max in [25000, 50000, 75000, 100000, 150000, 200000, 300000, 500000]:
        _fetch_search({"cash_flow_max": cf_max})

    # 4. Down payment ranges
    for dp_min in [25000, 50000, 100000, 200000, 500000, 1000000]:
        _fetch_search({"down_payment_min": dp_min})
    for dp_max in [25000, 50000, 100000, 200000, 500000]:
        _fetch_search({"down_payment_max": dp_max})

    # 5. Cross filters for large categories
    for ind in ["Service", "Retail", "Franchise", "Construction"]:
        for cf_min in [50000, 100000, 200000]:
            _fetch_search({"industry[]": ind, "cash_flow_min": cf_min})
        for cf_max in [50000, 100000, 200000]:
            _fetch_search({"industry[]": ind, "cash_flow_max": cf_max})

    print(f"  Discovered {len(all_ids)} unique listing IDs")
    return all_ids


def _parse_detail_page(html, id_number):
    """Parse a detail page HTML into a raw listing dict."""
    result = {"id_number": id_number}

    # Extract structured data from the dl/dt/dd table
    # Anchor to the <dl> tag that contains dt/dd pairs, not the stray
    # "Listing ID:" that can appear in the description <p> tags
    listing_section = re.search(r'<dl[^>]*>.*?Listing ID:.*?</dl>', html, re.DOTALL)
    if listing_section:
        section = listing_section.group()
        text = re.sub(r'<[^>]+>', '\n', section)
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        field_map = {}
        i = 0
        while i < len(lines) - 1:
            key = lines[i].rstrip(':')
            val = lines[i + 1] if i + 1 < len(lines) else ""
            # Skip tooltip text
            if val.startswith(('SDE', 'FF & E', 'is an abbreviation', ': Furniture')):
                i += 1
                while i < len(lines) and not lines[i].startswith('$') and ':' not in lines[i]:
                    i += 1
                if i < len(lines) and lines[i].startswith('$'):
                    val = lines[i]
                    i += 1
                    field_map[key] = val
                continue
            field_map[key] = val
            i += 2

        result["industry"] = field_map.get("Industry", "")
        result["location"] = field_map.get("Location", "")
        result["revenue_text"] = field_map.get("Revenue", "")
        result["asking_price_text"] = field_map.get("Business Price", "")
        result["down_payment_text"] = field_map.get("Down Payment", "")
        result["cash_flow_text"] = field_map.get("SDE (Cash Flow)", "")
        result["real_estate"] = field_map.get("Real Estate", "")
        result["ffe_text"] = field_map.get("FF & E", "")
        result["years_in_business"] = field_map.get("Years in Business", "")
        result["is_franchise"] = field_map.get("Is this a franchise", "")
        result["employees_ft"] = field_map.get("Employees (Full-Time)", "")
        result["employees_pt"] = field_map.get("Employees (Part-Time)", "")
        result["reason_for_selling"] = field_map.get("Reason for selling", "")
        result["sba_available"] = field_map.get("SBA Financing Available", "")
        result["relocatable"] = field_map.get("Relocatable", "")
        result["home_based"] = field_map.get("Home-Based", "")
        result["listing_agent"] = field_map.get("Listing Agent", "")
        result["absentee_owner_field"] = field_map.get("Absentee Owner", "")

    # Extract title — on detail pages it's in h3 (not h1 which is "Complete Search Listing")
    # Try h3 first (the real business name), skip generic headers
    h3_matches = re.findall(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
    for h3 in h3_matches:
        clean = re.sub(r'<[^>]+>', '', h3).strip()
        if clean and len(clean) > 10 and "contact" not in clean.lower() and "sunbelt" not in clean.lower():
            result["title"] = clean
            break
    # Fallback to h4 (search results page style)
    if "title" not in result:
        h4_match = re.search(r'<h4[^>]*class="[^"]*sunbelt-red[^"]*"[^>]*>(.*?)</h4>', html, re.DOTALL)
        if h4_match:
            result["title"] = re.sub(r'<[^>]+>', '', h4_match.group(1)).strip()

    # Extract description text
    desc_match = re.search(r'<div[^>]*class="[^"]*web-desc[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
    if desc_match:
        desc = re.sub(r'<[^>]+>', ' ', desc_match.group(1))
        desc = re.sub(r'\s+', ' ', desc).strip()
        result["description"] = desc[:2000]
    else:
        # Fallback: find largest text block after the title
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
        texts = []
        for p in paragraphs:
            clean = re.sub(r'<[^>]+>', ' ', p)
            clean = re.sub(r'\s+', ' ', clean).strip()
            if len(clean) > 50:
                texts.append(clean)
        if texts:
            result["description"] = " ".join(texts)[:2000]

    return result


def fetch_all_listings():
    """
    Main entry point. Discovers listing IDs via search page filter
    combinations, then fetches each detail page for full data.
    Returns list of raw dicts.
    """
    cfg = _load_config()
    detail_delay = cfg.get("detail_rate_limit_delay", 2.0)

    print("Discovering listing IDs...")
    ids = _discover_listing_ids(cfg)

    print(f"Fetching {len(ids)} detail pages...")
    listings = []
    for i, id_number in enumerate(sorted(ids)):
        detail_url = f"https://www.sunbeltmidwest.com/complete-search-listing/?id_number={id_number}"
        time.sleep(detail_delay)
        html = _get_with_retry(detail_url, cfg=cfg)
        if html is None:
            print(f"  [{i+1}/{len(ids)}] Failed: {id_number}")
            continue

        raw = _parse_detail_page(html, id_number)
        raw["detail_url"] = detail_url

        # Check if this is actually a Minnesota listing
        loc = raw.get("location", "").lower()
        if "minnesota" in loc or not loc:
            listings.append(raw)
        else:
            # Skip non-Minnesota (some filter combos leak other states)
            pass

        if (i + 1) % 10 == 0:
            print(f"  [{i+1}/{len(ids)}] fetched...")

    print(f"  Fetched {len(listings)} Minnesota listings")
    return listings
