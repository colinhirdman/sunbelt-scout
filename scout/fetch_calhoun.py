"""
Calhoun Companies listing scraper.
Returns raw dicts in parse_listings()-compatible format.
"""
import time
import re
import requests

BASE_URL = "https://www.calhouncompanies.com"
SEARCH_URL = f"{BASE_URL}/find-a-business"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
RATE_LIMIT = 2.0
MAX_RETRIES = 3


def _get(url, params=None):
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=30)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.text
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** (attempt + 1))
            else:
                print(f"  [Calhoun] Request failed: {e}")
                return None
    return None


def _clean(text):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', text)).strip()


def _discover_slugs():
    """Paginate search results and return all /business/ slugs."""
    slugs = set()
    page = 0
    while True:
        params = {
            "ux_filter__node__field_industry": "All",
            "ux_filter__node__field_location": "3",  # Minnesota
            "field_price_value": "All",
            "field_cash_flow_value": "All",
            "keys": "",
            "page": page,
        }
        time.sleep(RATE_LIMIT)
        html = _get(SEARCH_URL, params=params)
        if not html:
            break

        found = list(dict.fromkeys(re.findall(r'href="(/business/[^"?#]+)"', html)))
        if not found:
            print(f"  [Calhoun] Page {page}: no listings, stopping.")
            break

        new = [s for s in found if s not in slugs]
        if not new:
            break  # all already seen — end of pagination

        slugs.update(found)
        print(f"  [Calhoun] Page {page}: {len(found)} listings ({len(new)} new) — {len(slugs)} total")
        page += 1

    return slugs


def _parse_detail(html, slug):
    """Parse a Calhoun detail page into a parse_listings()-compatible dict."""
    slug_name = slug.lstrip("/").split("/")[-1]
    result = {
        "id_number":          f"calhoun_{slug_name}",
        "detail_url":         f"{BASE_URL}{slug}",
        "is_franchise":       "",
        "reason_for_selling": "",
        "sba_available":      "",
        "absentee_owner_field": "",
        "employees_ft":       None,
        "employees_pt":       None,
        "real_estate":        "",
    }

    # Title
    h1 = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
    if h1:
        result["title"] = _clean(h1.group(1))
    if not result.get("title"):
        h3 = re.search(r'<h3[^>]*>(.*?)</h3>', html, re.DOTALL)
        if h3:
            result["title"] = _clean(h3.group(1))

    def _field(label):
        # Pattern: Label text near a value in the next element
        m = re.search(
            rf'{re.escape(label)}\s*[:\-]?\s*</[^>]*>\s*<[^>]*>\s*([^<]+)',
            html, re.IGNORECASE
        )
        if m:
            return _clean(m.group(1))
        # Plain text: "Label: value"
        m = re.search(rf'{re.escape(label)}\s*:\s*([^\n<]+)', html, re.IGNORECASE)
        if m:
            return _clean(m.group(1))
        return ""

    result["industry"]          = _field("Industry")
    result["location"]          = _field("Location") or "Minnesota"
    result["asking_price_text"] = _field("Price") or _field("Business Price") or _field("Asking Price")
    result["cash_flow_text"]    = _field("Cash Flow") or _field("SDE (Cash Flow)") or _field("SDE")
    result["revenue_text"]      = _field("Gross Sales") or _field("Revenue") or _field("Annual Revenue")
    result["years_in_business"] = _field("Years Established") or _field("Years in Business")
    result["listing_agent"]     = _field("Listing Agent") or _field("Contact Agent")

    # Description — try common Drupal body field class patterns first
    for pattern in [
        r'<div[^>]*class="[^"]*field--name-body[^"]*"[^>]*>(.*?)</div>\s*</div>',
        r'<div[^>]*class="[^"]*body[^"]*"[^>]*>(.*?)</div>',
        r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>',
    ]:
        m = re.search(pattern, html, re.DOTALL | re.IGNORECASE)
        if m:
            text = _clean(m.group(1))
            if len(text) > 50:
                result["description"] = text[:2000]
                break

    if "description" not in result:
        paragraphs = re.findall(r'<p[^>]*>(.*?)</p>', html, re.DOTALL)
        texts = [_clean(p) for p in paragraphs if len(_clean(p)) > 50]
        if texts:
            result["description"] = " ".join(texts[:5])[:2000]

    return result


def fetch_all_listings():
    """
    Discover and fetch all Calhoun MN listings.
    Returns (listings, discovered_ids) compatible with parse_listings().
    """
    print("  [Calhoun] Discovering listings...")
    slugs = _discover_slugs()
    discovered_ids = {f"calhoun_{s.lstrip('/').split('/')[-1]}" for s in slugs}

    print(f"  [Calhoun] Fetching {len(slugs)} detail pages...")
    listings = []
    for i, slug in enumerate(sorted(slugs)):
        time.sleep(RATE_LIMIT)
        html = _get(f"{BASE_URL}{slug}")
        if html is None:
            continue
        raw = _parse_detail(html, slug)
        listings.append(raw)
        if (i + 1) % 10 == 0:
            print(f"  [Calhoun] [{i+1}/{len(slugs)}] fetched...")

    print(f"  [Calhoun] Fetched {len(listings)} listings")
    return listings, discovered_ids
