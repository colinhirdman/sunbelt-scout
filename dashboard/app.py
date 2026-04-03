from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
from supabase import create_client, Client
import anthropic
import json
import io

try:
    from pdfminer.high_level import extract_text as _pdfminer_extract
    _PDFMINER_OK = True
except ImportError:
    _PDFMINER_OK = False

# ── Supabase client ─────────────────────────────────────────────────────────────
@st.cache_resource
def _get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

def _load_watchlist() -> set:
    try:
        res = _get_supabase().table("watchlist").select("listing_id").execute()
        return {r["listing_id"] for r in res.data}
    except Exception:
        return set()

def _save_watchlist(wl: set, added: str | None = None, removed: str | None = None) -> None:
    try:
        sb = _get_supabase()
        if added:
            sb.table("watchlist").upsert({"listing_id": added}).execute()
        if removed:
            sb.table("watchlist").delete().eq("listing_id", removed).execute()
    except Exception:
        pass

def _load_overrides() -> dict:
    """Returns {listing_id: {dimension: value}} from Supabase."""
    try:
        res = _get_supabase().table("profile_overrides").select("listing_id,dimension,value").execute()
        out = {}
        for r in res.data:
            out.setdefault(r["listing_id"], {})[r["dimension"]] = r["value"]
        return out
    except Exception:
        return {}

def _chat_response(messages: list, listing_context: str) -> str:
    """Call Claude Haiku with listing context and return assistant reply."""
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if not key:
            return "ANTHROPIC_API_KEY not configured in Streamlit secrets."
        client = anthropic.Anthropic(api_key=key)
        system = (
            "You are Scout, an AI assistant helping evaluate small business acquisition opportunities "
            "for Monkey Island Ventures. You have deep expertise in SBA lending, business valuation, "
            "owner-operator acquisitions, and SMB due diligence.\n\n"
            "You are analyzing the following listing:\n\n"
            + listing_context +
            "\n\nBe concise and direct. Focus on what matters for an acquisition decision. "
            "If asked to calculate something, show your work briefly."
        )
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=system,
            messages=messages,
        )
        return response.content[0].text
    except Exception as e:
        return f"Error: {e}"


def _build_listing_context(row) -> str:
    """Serialize a listing row into a readable context block for the system prompt."""
    def v(key, fmt=None):
        val = row.get(key)
        if val is None or (isinstance(val, float) and pd.isna(val)) or str(val) in ("", "nan"):
            return "N/A"
        if fmt == "$":
            return f"${float(val):,.0f}"
        if fmt == "%":
            return f"{float(val)*100:.1f}%"
        if fmt == "x":
            return f"{float(val):.2f}x"
        return str(val)

    lines = [
        f"Title: {v('title')}",
        f"ID: {v('id')}  |  Source: {v('source')}",
        f"Location: {v('location')}  |  Industry: {v('industry')}",
        f"Asking Price: {v('asking_price', '$')}",
        f"Annual Cash Flow (SDE): {v('annual_cash_flow', '$')}",
        f"Annual Revenue: {v('annual_revenue', '$')}",
        f"Employees: {v('employees')}",
        f"Years in Business: {v('years_in_business')}",
        f"Absentee Owner: {v('absentee')}",
        f"Franchise: {v('is_franchise')}  |  SBA Available: {v('sba_available')}",
        f"Reason for Selling: {v('reason_for_selling')}",
        f"Listing Agent: {v('listing_agent')}",
        "",
        "── SBA Financing (10% down) ──",
        f"Down Payment: {v('down_10', '$')}  |  Monthly Payment: {v('sba_monthly_10pct', '$')}",
        f"CF After Debt: {v('cf_after_debt_10pct', '$')}  |  CoC Return: {v('coc_return_10pct', '%')}",
        f"DSCR: {v('dscr_10pct', 'x')}  |  Payoff: {v('payoff_years_10pct')} yrs",
        "",
        "── SBA Financing (20% down) ──",
        f"Down Payment: {v('down_20', '$')}  |  Monthly Payment: {v('sba_monthly_20pct', '$')}",
        f"CF After Debt: {v('cf_after_debt_20pct', '$')}  |  CoC Return: {v('coc_return_20pct', '%')}",
        f"DSCR: {v('dscr_20pct', 'x')}  |  Payoff: {v('payoff_years_20pct')} yrs",
        "",
        f"Scout Score: {v('score')}  |  Bucket: {v('bucket')}",
        f"Scoring Signals: {v('reasons')}",
    ]

    narrative = v("narrative")
    if narrative != "N/A":
        lines += ["", f"Scout Narrative: {narrative}"]

    description = v("description")
    if description != "N/A":
        lines += ["", f"Broker Description: {description}"]

    # Include full PDF text if available
    lid = str(row.get("id", ""))
    pdf_record = st.session_state.get("pdf_data", {}).get(lid, {})
    pdf_text = pdf_record.get("pdf_text", "")
    if pdf_text:
        lines += ["", "── Full Broker Document ──", pdf_text[:8000]]

    return "\n".join(lines)


def _save_override(listing_id: str, dimension: str, value: int) -> None:
    try:
        _get_supabase().table("profile_overrides").upsert({
            "listing_id": listing_id,
            "dimension":  dimension,
            "value":      value,
        }).execute()
    except Exception:
        pass


# ── PDF data ────────────────────────────────────────────────────────────────────

def _load_pdf_data() -> dict:
    """Returns {listing_id: {fields: {}, pdf_text: ''}} from Supabase."""
    try:
        res = _get_supabase().table("pdf_data").select("listing_id,fields,pdf_text").execute()
        return {r["listing_id"]: {"fields": r.get("fields") or {}, "pdf_text": r.get("pdf_text") or ""} for r in res.data}
    except Exception:
        return {}


def _save_pdf_data(listing_id: str, fields: dict, pdf_text: str) -> None:
    try:
        _get_supabase().table("pdf_data").upsert({
            "listing_id": listing_id,
            "fields":     fields,
            "pdf_text":   pdf_text,
        }).execute()
    except Exception as e:
        st.error(f"Failed to save PDF data: {e}")


def _upload_pdf_storage(listing_id: str, file_bytes: bytes) -> None:
    try:
        _get_supabase().storage.from_("pdfs").upload(
            f"{listing_id}.pdf",
            file_bytes,
            file_options={"content-type": "application/pdf", "upsert": "true"},
        )
    except Exception as e:
        st.warning(f"PDF storage upload failed: {e}")


_PDF_EXTRACT_PROMPT = """You are extracting structured business listing data from a broker PDF.

Return ONLY a valid JSON object with these fields (use null for anything not found):

{
  "title":             string or null,
  "asking_price":      number or null,
  "annual_cash_flow":  number or null,
  "annual_revenue":    number or null,
  "employees":         number or null,
  "years_in_business": string or null,
  "reason_for_selling":string or null,
  "location":          string or null,
  "industry":          string or null,
  "listing_agent":     string or null,
  "is_franchise":      string or null,
  "sba_available":     string or null,
  "description":       string or null
}

PDF text:
"""


def _extract_pdf_text(file_bytes: bytes) -> str:
    if not _PDFMINER_OK:
        return ""
    try:
        return _pdfminer_extract(io.BytesIO(file_bytes))[:15000]
    except Exception:
        return ""


def _extract_pdf_fields(pdf_text: str) -> dict:
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", "")
        if not key:
            return {}
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{"role": "user", "content": _PDF_EXTRACT_PROMPT + pdf_text}],
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        return json.loads(raw)
    except Exception:
        return {}

# ── Category config ────────────────────────────────────────────────────────────

TRADES_KEYWORDS = [
    "plumb", "electrician", "electrical", "electric",
    "hvac", "heating", "cooling", "air condition",
    "roofing", "roofer",
    "landscaping", "landscape", "lawn care", "lawn service",
    "excavat", "concrete", "masonry", "mason",
    "flooring", "carpet", "tile install",
    "siding", "insulation", "gutter",
    "pest control", "exterminator",
    "septic", "drain service", "drain clean",
    "welding", "welder",
    "mechanical contractor", "mechanical service",
    "snow removal", "irrigation",
    "painting contractor", "painting company", "commercial painting",
    "handyman", "restoration contractor", "fire restoration", "water restoration",
    "refrigeration contractor",
]
LAWN_SNOW_KEYWORDS = [
    "lawn care", "lawn service", "lawn mowing", "lawn maintenance", "lawn cutting",
    "landscaping", "landscape", "landscape maintenance",
    "snow removal", "snow plowing", "snow plow", "snow management",
    "grounds maintenance", "grounds care", "groundskeeping",
    "turf", "mowing", "mow", "irrigation", "sprinkler",
    "fertiliz", "weed control", "tree service", "tree trimming", "tree removal",
    "arborist", "leaf removal", "mulch",
]
HEALTHCARE_KEYWORDS = [
    "home health", "home care", "home healthcare",
    "senior care", "elder care", "assisted living", "memory care",
    "medical", "dental", "optometry", "optometrist", "ophthalmol",
    "veterinary", "veterinarian", "vet clinic", "animal hospital",
    "physical therapy", "occupational therapy", "speech therapy",
    "chiropractic", "chiropractor", "pharmacy", "pharmacist",
    "mental health", "behavioral health", "counseling practice",
    "nursing", "nurse staffing", "healthcare staffing",
    "urgent care", "clinic", "medical practice",
    "hospice", "palliative", "medical billing", "medical coding",
    "radiology", "laboratory", "lab service", "health care", "healthcare",
]
CONSTRUCTION_KEYWORDS = [
    "general contractor", "general construction", "commercial construction",
    "commercial contractor", "residential construction", "home builder",
    "remodel", "remodeling", "renovation", "framing", "drywall",
    "finish carpenter", "finish carpentry", "foundation", "earthwork",
    "site work", "construction company", "construction firm",
    "civil contractor", "civil construction",
]
AUTOMOTIVE_KEYWORDS = [
    "auto repair", "auto service", "automotive repair", "automotive service",
    "car repair", "vehicle repair", "mechanic", "auto mechanic",
    "body shop", "collision", "auto body", "oil change", "lube",
    "car wash", "auto detailing", "vehicle detailing",
    "auto parts", "used car", "car dealership", "auto dealer",
    "tire shop", "tire service", "wheel alignment",
    "transmission", "brake shop", "towing", "roadside assistance",
    "fleet service", "fleet maintenance",
]
RESTAURANT_KEYWORDS = [
    "restaurant", "bar ", "tavern", "pub ", "brewery", "brewpub",
    "cafe", "coffee shop", "diner", "fast food", "quick service", "qsr",
    "catering", "food service", "food truck", "pizza", "sandwich shop",
    "deli", "bakery", "pastry", "donut", "food and beverage", "f&b",
    "dining", "eatery", "breakfast", "brunch", "sushi", "steakhouse", "grill",
]
RETAIL_KEYWORDS = [
    "retail", "retail store", "retail shop", "gift shop", "specialty store",
    "boutique", "clothing store", "apparel", "furniture store", "home goods",
    "sporting goods", "outdoor gear", "hardware store", "pet store", "pet supply",
    "toy store", "hobby shop", "book store", "convenience store", "c-store",
    "jewelry store", "florist", "flower shop",
]
MANUFACTURING_KEYWORDS = [
    "manufacturing", "manufacturer", "fabrication", "fabricator",
    "machining", "machine shop", "cnc", "production", "assembly",
    "metal fabrication", "sheet metal", "plastic injection", "injection molding",
    "food manufacturing", "food processing", "food production",
    "packaging", "printing", "print shop", "woodworking", "cabinet making",
    "millwork", "industrial", "factory", "contract manufacturing",
]
DISTRIBUTION_KEYWORDS = [
    "distribution", "distributor", "logistics", "supply chain",
    "trucking", "trucking company", "freight", "warehouse", "warehousing",
    "delivery service", "delivery company", "courier", "last mile",
    "wholesale", "wholesaler", "import", "export", "fulfillment", "cold storage",
]
FINANCIAL_KEYWORDS = [
    "accounting", "accountant", "cpa", "bookkeeping", "bookkeeper",
    "tax preparation", "tax service", "tax firm",
    "financial planning", "financial advisor", "financial services",
    "insurance agency", "insurance broker", "payroll service", "payroll processing",
    "wealth management", "mortgage", "lending",
]
HOSPITALITY_KEYWORDS = [
    "hotel", "motel", "inn ", "bed and breakfast", "b&b",
    "lodge", "lodging", "resort", "vacation rental", "extended stay",
]
TECHNOLOGY_KEYWORDS = [
    "managed service", "msp", "it service", "it support", "it consulting",
    "computer repair", "tech repair", "software", "technology company",
    "web development", "web design", "cybersecurity", "cyber security",
    "data", "cloud services", "telecom", "telecommunications",
]
EDUCATION_KEYWORDS = [
    "daycare", "day care", "childcare", "child care", "preschool",
    "tutoring", "tutor", "learning center", "after school", "early childhood",
    "montessori", "dance studio", "music school", "music lesson",
    "martial arts", "karate", "driving school", "vocational",
]
BEAUTY_KEYWORDS = [
    "salon", "hair salon", "beauty salon", "barber", "barbershop",
    "nail salon", "nail spa", "spa", "day spa", "med spa",
    "massage", "massage therapy", "skincare", "skin care",
    "tanning salon", "gym", "fitness", "fitness center",
    "yoga", "pilates", "crossfit", "personal training", "wellness center",
]

CATEGORY_CONFIG = {
    "Healthcare":            {"keywords": HEALTHCARE_KEYWORDS,   "emoji": "🩺", "col": "is_healthcare",   "color": "#15803D", "bg": "#F0FDF4"},
    "Lawn / Snow":           {"keywords": LAWN_SNOW_KEYWORDS,    "emoji": "🌿", "col": "is_lawn_snow",    "color": "#166534", "bg": "#ECFDF5"},
    "Trades":                {"keywords": TRADES_KEYWORDS,       "emoji": "🔧", "col": "is_trades",       "color": "#C2410C", "bg": "#FFF7ED"},
    "Construction":          {"keywords": CONSTRUCTION_KEYWORDS, "emoji": "🏗️", "col": "is_construction", "color": "#92400E", "bg": "#FEF3C7"},
    "Automotive":            {"keywords": AUTOMOTIVE_KEYWORDS,   "emoji": "🚗", "col": "is_automotive",   "color": "#1D4ED8", "bg": "#EFF6FF"},
    "Restaurant & Bar":      {"keywords": RESTAURANT_KEYWORDS,   "emoji": "🍽️", "col": "is_restaurant",   "color": "#BE123C", "bg": "#FFF1F2"},
    "Retail":                {"keywords": RETAIL_KEYWORDS,       "emoji": "🛍️", "col": "is_retail",       "color": "#7E22CE", "bg": "#FDF4FF"},
    "Manufacturing":         {"keywords": MANUFACTURING_KEYWORDS,"emoji": "🏭", "col": "is_manufacturing","color": "#0369A1", "bg": "#F0F9FF"},
    "Distribution":          {"keywords": DISTRIBUTION_KEYWORDS, "emoji": "🚚", "col": "is_distribution", "color": "#065F46", "bg": "#F0FDF4"},
    "Financial Services":    {"keywords": FINANCIAL_KEYWORDS,    "emoji": "💼", "col": "is_financial",    "color": "#B45309", "bg": "#FFFBEB"},
    "Hospitality":           {"keywords": HOSPITALITY_KEYWORDS,  "emoji": "🏨", "col": "is_hospitality",  "color": "#C2410C", "bg": "#FFF7ED"},
    "Technology / IT":       {"keywords": TECHNOLOGY_KEYWORDS,   "emoji": "💻", "col": "is_technology",   "color": "#1E40AF", "bg": "#EFF6FF"},
    "Education & Childcare": {"keywords": EDUCATION_KEYWORDS,    "emoji": "🎓", "col": "is_education",    "color": "#9F1239", "bg": "#FFF1F2"},
    "Beauty & Wellness":     {"keywords": BEAUTY_KEYWORDS,       "emoji": "💇", "col": "is_beauty",       "color": "#86198F", "bg": "#FDF4FF"},
}

DIMENSIONS = {
    "dim_ai_proof":      {"label": "AI-Proof",        "icon": "🤖"},
    "dim_fun":           {"label": "Fun to Own",       "icon": "⭐"},
    "dim_weather":       {"label": "Year-Round",       "icon": "☀️"},
    "dim_labor":         {"label": "Manual Labor",     "icon": "🔧"},
    "dim_recurring":     {"label": "Recurring Rev",    "icon": "🔁"},
    "dim_absentee":      {"label": "Absentee",         "icon": "🏠"},
    "dim_capital_light": {"label": "Capital Light",    "icon": "💡"},
    "dim_scalable":      {"label": "Scalable",         "icon": "📈"},
}

BUCKET_COLOR = {
    "SHORTLIST":   "#008A05",
    "REVIEW":      "#C45C00",
    "SKIP":        "#B0B0B0",
    "AUTO-REJECT": "#C13515",
}

BUCKET_DISPLAY = {
    "SHORTLIST":   "Strong Match",
    "REVIEW":      "Worth a Look",
    "SKIP":        "Skip",
    "AUTO-REJECT": "Skip",
}

_OUTPUT = Path(__file__).resolve().parents[1] / "output"
SUNBELT_CSV = _OUTPUT / "sunbelt.csv"
CALHOUN_CSV = _OUTPUT / "calhoun.csv"

st.set_page_config(page_title="Sunbelt Scout", layout="wide", page_icon="🏢")

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Page background ── */
.stApp { background: #F7F7F7; }
section[data-testid="stSidebar"] + div .main { background: #F7F7F7; }
.main .block-container { background: #F7F7F7; }

/* ── Top header ── */
.top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 0 18px;
    margin-bottom: 4px;
}
.top-bar-title {
    font-size: 24px;
    font-weight: 800;
    color: #222222;
    letter-spacing: -0.5px;
}
.top-bar-title span { color: #FF385C; }
.top-bar-sub { font-size: 13px; color: #717171; margin-top: 3px; }

/* ── Stat pills ── */
.stats-row { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
.stat-pill {
    background: white;
    border-radius: 14px;
    padding: 12px 18px;
    min-width: 90px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border: 1px solid #EBEBEB;
}
.stat-pill .sp-label { font-size: 11px; font-weight: 600; color: #717171; text-transform: uppercase; letter-spacing: 0.4px; }
.stat-pill .sp-value { font-size: 24px; font-weight: 800; color: #222222; line-height: 1.2; margin-top: 2px; }
.stat-pill .sp-value.green  { color: #008A05; }
.stat-pill .sp-value.amber  { color: #C45C00; }
.stat-pill .sp-value.red    { color: #C13515; }
.stat-pill .sp-value.blue   { color: #FF385C; }

/* ── Deal cards ── */
.deal-card {
    background: white;
    border-radius: 16px 16px 0 0;
    padding: 16px 16px 12px;
    margin-bottom: 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    border: 1px solid #EBEBEB;
    border-bottom: none;
    border-left: 4px solid #EBEBEB;
    transition: box-shadow 0.2s;
}
.deal-card.bucket-shortlist { border-left-color: #008A05; }
.deal-card.bucket-review    { border-left-color: #C45C00; }
.deal-card.bucket-reject    { border-left-color: #C13515; opacity: 0.75; }
.deal-card.selected {
    border-left-color: #FF385C !important;
    box-shadow: 0 4px 16px rgba(255,56,92,0.12);
    background: #FFF8F9;
}

.dc-top { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 4px; }
.dc-title { font-size: 14px; font-weight: 600; color: #222222; line-height: 1.35; flex: 1; margin-right: 12px; }
.dc-price { font-size: 18px; font-weight: 800; color: #222222; white-space: nowrap; }
.dc-meta { font-size: 12px; color: #717171; margin-bottom: 10px; }
.dc-footer { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; padding-top: 8px; border-top: 1px solid #F5F5F5; }

/* ── Score pill (footer) ── */
.score-pill {
    font-size: 11px;
    font-weight: 700;
    padding: 3px 8px;
    border-radius: 20px;
    margin-left: auto;
}

/* ── Bucket badge ── */
.bucket-badge {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 10px;
    border-radius: 20px;
}
.bb-shortlist { background: #D4EDDA; color: #155724; }
.bb-review    { background: #FFF3CD; color: #856404; }
.bb-skip      { background: #F1F5F9; color: #6C757D; }
.bb-reject    { background: #FDECEA; color: #C13515; }

/* ── Category tag ── */
.cat-tag {
    font-size: 10px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 20px;
}

/* ── CoC / CF badges ── */
.coc-badge {
    font-size: 11px;
    font-weight: 700;
    color: #008A05;
    background: #D4EDDA;
    padding: 3px 8px;
    border-radius: 20px;
}
.cf-badge {
    font-size: 11px;
    font-weight: 600;
    color: #717171;
    background: #F7F7F7;
    padding: 3px 8px;
    border-radius: 20px;
}

/* ── Card action row (fused below card) ── */
.card-actions {
    display: flex;
    border: 1px solid #EBEBEB;
    border-top: none;
    border-radius: 0 0 16px 16px;
    margin-bottom: 16px;
    overflow: hidden;
    background: white;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.card-actions .stButton button {
    border-radius: 0 !important;
    border: none !important;
    background: white !important;
    color: #717171 !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    padding: 8px 0 !important;
    transition: background 0.15s !important;
}
.card-actions .stButton button:hover {
    background: #F7F7F7 !important;
    color: #222222 !important;
}
.card-actions .stButton:first-child button {
    border-right: 1px solid #EBEBEB !important;
}
.card-actions .stButton button[kind="primary"] {
    background: #FFF8F9 !important;
    color: #FF385C !important;
}

/* ── Detail panel ── */
.dp-header { padding-bottom: 16px; border-bottom: 1px solid #EBEBEB; margin-bottom: 16px; }
.dp-title { font-size: 20px; font-weight: 800; color: #222222; line-height: 1.3; margin-bottom: 8px; }
.dp-section {
    font-size: 11px;
    font-weight: 700;
    color: #717171;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin: 20px 0 10px;
    padding-top: 16px;
    border-top: 1px solid #EBEBEB;
}

/* ── Score bar ── */
.score-bar-wrap { margin: 10px 0; }
.score-bar-label { display: flex; justify-content: space-between; font-size: 11px; font-weight: 600; color: #717171; margin-bottom: 5px; }
.score-bar-track { background: #EBEBEB; border-radius: 6px; height: 8px; overflow: hidden; }
.score-bar-fill { height: 8px; border-radius: 6px; }

/* ── Finance grid ── */
.fin-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 12px; }
.fin-cell {
    background: #F7F7F7;
    border: 1px solid #EBEBEB;
    border-radius: 12px;
    padding: 12px 14px;
}
.fin-label { font-size: 11px; font-weight: 600; color: #717171; text-transform: uppercase; letter-spacing: 0.3px; }
.fin-value { font-size: 18px; font-weight: 800; color: #222222; margin-top: 2px; }
.fin-value.green { color: #008A05; }
.fin-value.red   { color: #C13515; }
.fin-value.amber { color: #C45C00; }

/* ── Narrative blocks ── */
.nar-block { border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; }
.nar-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px; }
.nar-list { margin: 0; padding-left: 16px; font-size: 13px; line-height: 1.75; color: #222222; }
.nar-bottom { background: #FF385C; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; }
.nar-bottom-label { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: rgba(255,255,255,0.8); margin-bottom: 4px; }
.nar-bottom-text { font-size: 14px; font-weight: 600; color: white; line-height: 1.5; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: white !important;
    border-right: 1px solid #EBEBEB !important;
}
[data-testid="stSidebar"] label { font-size: 13px !important; color: #374151 !important; }
[data-testid="stSidebar"] .stMarkdown h3 {
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.6px !important;
    color: #717171 !important;
}

/* ── Expander ── */
[data-testid="stExpander"] { background: white !important; border: 1px solid #EBEBEB !important; border-radius: 12px !important; }

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px;
    font-size: 13px;
    font-weight: 600;
    padding: 6px 0;
    transition: all 0.15s;
}
[data-testid="stBaseButton-primary"] {
    background: #FF385C !important;
    color: white !important;
    border: none !important;
}
[data-testid="stBaseButton-primary"]:hover { background: #E0314F !important; }
[data-testid="stBaseButton-secondary"] {
    background: white !important;
    color: #222222 !important;
    border: 1.5px solid #DDDDDD !important;
}
[data-testid="stBaseButton-secondary"]:hover {
    background: #F7F7F7 !important;
    border-color: #B0B0B0 !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #F7F7F7 !important;
    border: 1px solid #EBEBEB !important;
    border-radius: 12px !important;
    padding: 12px 14px !important;
}
[data-testid="metric-container"] label {
    font-size: 11px !important;
    font-weight: 600 !important;
    color: #717171 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.3px !important;
}
[data-testid="stMetricValue"] { font-size: 16px !important; font-weight: 800 !important; color: #222222 !important; }

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    background: #EBEBEB !important;
    border-radius: 10px !important;
    padding: 3px !important;
    gap: 2px !important;
}
[data-baseweb="tab"] {
    font-size: 13px !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    color: #717171 !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: white !important;
    color: #222222 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1) !important;
}

/* ── Search input ── */
[data-testid="stTextInput"] input {
    border-radius: 50px !important;
    border: 1.5px solid #DDDDDD !important;
    padding: 10px 16px !important;
    font-size: 14px !important;
    background: white !important;
}
[data-testid="stTextInput"] input:focus {
    border-color: #222222 !important;
    box-shadow: none !important;
}

/* ── Divider ── */
hr { border-color: #EBEBEB !important; margin: 16px 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    frames = []
    for source_name, path in [("sunbelt", SUNBELT_CSV), ("calhoun", CALHOUN_CSV)]:
        if not path.exists():
            continue
        part = pd.read_csv(path)
        if "source" not in part.columns or part["source"].isna().all():
            part["source"] = source_name
        frames.append(part)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0).astype(int)

    numeric_cols = [
        "asking_price", "annual_cash_flow", "annual_revenue", "employees",
        "down_10", "down_20", "sba_monthly_10pct", "sba_monthly_20pct",
        "annual_debt_service_10pct", "annual_debt_service_20pct",
        "cf_after_debt_10pct", "cf_after_debt_20pct",
        "coc_return_10pct", "coc_return_20pct",
        "dscr_10pct", "dscr_20pct",
        "payoff_years_10pct", "payoff_years_20pct",
        "seller_note_amount", "seller_note_monthly", "seller_note_annual",
        "cf_during_standby", "cf_after_seller_financing", "dscr_seller_financed",
        "dim_ai_proof", "dim_fun", "dim_weather", "dim_labor",
        "dim_recurring", "dim_absentee", "dim_capital_light", "dim_scalable",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    def _detect(row, keywords):
        ctx = f"{row.get('title', '')} {row.get('industry', '')} {row.get('description', '')}".lower()
        return any(kw in ctx for kw in keywords)

    for cfg in CATEGORY_CONFIG.values():
        df[cfg["col"]] = df.apply(lambda r, k=cfg["keywords"]: _detect(r, k), axis=1)

    df["revenue_multiple"] = df.apply(
        lambda r: round(r["asking_price"] / r["annual_revenue"], 2)
        if pd.notna(r.get("asking_price")) and pd.notna(r.get("annual_revenue")) and r["annual_revenue"] > 0
        else None, axis=1
    )
    df["sde_margin"] = df.apply(
        lambda r: round(r["annual_cash_flow"] / r["annual_revenue"], 4)
        if pd.notna(r.get("annual_cash_flow")) and pd.notna(r.get("annual_revenue")) and r["annual_revenue"] > 0
        else None, axis=1
    )
    df["revenue_per_employee"] = df.apply(
        lambda r: round(r["annual_revenue"] / r["employees"], 0)
        if pd.notna(r.get("annual_revenue")) and pd.notna(r.get("employees")) and r["employees"] > 0
        else None, axis=1
    )
    return df


df = load_data()
if df.empty:
    st.warning("No candidates.csv found. Run the scout first: `python3 run.py`")
    st.stop()


# ── Session state ──────────────────────────────────────────────────────────────
if "selected_id"   not in st.session_state: st.session_state.selected_id   = None
if "watchlist"     not in st.session_state: st.session_state.watchlist     = _load_watchlist()
if "active_preset" not in st.session_state: st.session_state.active_preset = None
if "overrides"     not in st.session_state: st.session_state.overrides     = _load_overrides()
if "pdf_data"      not in st.session_state: st.session_state.pdf_data      = _load_pdf_data()


# ── Helpers ────────────────────────────────────────────────────────────────────
def _fmt(val, fmt="$"):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    if fmt == "$":  return f"${val:,.0f}"
    if fmt == "$M":
        if val >= 1_000_000: return f"${val/1e6:.2f}M"
        return f"${val:,.0f}"
    if fmt == "%":  return f"{val*100:.0f}%"
    if fmt == "x":  return f"{val:.2f}x"
    return str(val)

def _val_color(val, good, ok):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return "green" if val >= good else ("amber" if val >= ok else "red")

def _score_color(score):
    if score >= 65: return "#008A05"
    if score >= 35: return "#C45C00"
    return "#B0B0B0"

def _bucket_cls(bucket):
    return {"SHORTLIST": "bb-shortlist", "REVIEW": "bb-review", "AUTO-REJECT": "bb-reject"}.get(bucket, "bb-skip")

def _dim_score_color(v):
    if v >= 3: return "#008A05"
    if v >= 2: return "#C45C00"
    return "#B0B0B0"

def _effective_profile(row) -> dict:
    """Return dimension scores with any manual overrides applied."""
    lid = str(row.get("id", ""))
    overrides = st.session_state.overrides.get(lid, {})
    result = {}
    for dim in DIMENSIONS:
        raw = row.get(dim)
        try:
            raw = int(float(raw)) if raw not in (None, "", "nan") else 2
        except (ValueError, TypeError):
            raw = 2
        result[dim] = overrides.get(dim, raw)
    return result

def _row_categories(row):
    return [(name, cfg) for name, cfg in CATEGORY_CONFIG.items() if row.get(cfg["col"])]

def _primary_category(row):
    cats = _row_categories(row)
    return cats[0] if cats else ("Other", {"emoji": "🏢", "col": None, "color": "#475569", "bg": "#F1F5F9"})


# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown("### Price Range")
min_price = st.sidebar.number_input("Min ($)", value=50000,   step=50000)
max_price = st.sidebar.number_input("Max ($)", value=5000000, step=100000)

st.sidebar.markdown("### Cash Flow")
min_cf = st.sidebar.number_input("Min Cash Flow ($)", value=0, step=25000)

with st.sidebar.expander("More filters"):
    min_coc   = st.sidebar.slider("Min CoC Return (20% down)", 0, 200, 0, format="%d%%")
    twin_cities_only = st.sidebar.checkbox("Twin Cities Only")
    absentee_only    = st.sidebar.checkbox("Absentee / Semi-Absentee Only")
    source_filter    = st.sidebar.radio("Source", ["All", "Sunbelt", "Calhoun"], horizontal=True)
    st.markdown("---")
    apply_scoring = st.sidebar.checkbox("Filter by score", value=False)
    if apply_scoring:
        all_buckets = sorted(df["bucket"].dropna().unique().tolist())
        buckets   = st.sidebar.multiselect("Match quality", options=all_buckets,
            default=[b for b in ["SHORTLIST", "REVIEW"] if b in all_buckets])
        min_score = st.sidebar.slider("Min score", 0, 100, 35)
    else:
        buckets   = None
        min_score = 0

min_coc_decimal = min_coc / 100.0
if not apply_scoring:
    buckets   = None
    min_score = 0


# ── Base filters ───────────────────────────────────────────────────────────────
mask = pd.Series([True] * len(df))
if "is_active" in df.columns:
    mask &= df["is_active"].fillna("True").astype(str).str.lower() != "false"
if source_filter != "All":
    mask &= df["source"].fillna("").str.lower() == source_filter.lower()
if apply_scoring and buckets:
    mask &= df["bucket"].isin(buckets)
if apply_scoring:
    mask &= df["score"] >= min_score
mask &= (df["asking_price"].isna()) | (df["asking_price"] <= max_price)
mask &= (df["asking_price"].isna()) | (df["asking_price"] >= min_price)
mask &= (df["annual_cash_flow"].isna()) | (df["annual_cash_flow"] >= min_cf)
if min_coc_decimal > 0:
    mask &= (df["coc_return_20pct"].isna()) | (df["coc_return_20pct"] >= min_coc_decimal)
if absentee_only:
    mask &= df["absentee"].isin(["Likely", "Possible"])
if twin_cities_only:
    tc_pat = "|".join(["minneapolis","saint paul","st\\.paul","bloomington","plymouth",
                        "eden prairie","burnsville","minnetonka","eagan","edina",
                        "maple grove","woodbury","coon rapids","brooklyn park","twin cities","metro"])
    mask &= df["location"].str.contains(tc_pat, case=False, na=False)

base_filtered = df[mask].copy()


# ── Top bar ─────────────────────────────────────────────────────────────────────
n_total     = len(df)
n_filtered  = len(base_filtered)
n_shortlist = len(df[df["bucket"] == "SHORTLIST"])
n_review    = len(df[df["bucket"] == "REVIEW"])
n_rejected  = len(df[df["bucket"] == "AUTO-REJECT"])
n_watchlist = len(st.session_state.watchlist)

st.markdown(f"""
<div class="top-bar">
  <div>
    <div class="top-bar-title">Sunbelt <span>Scout</span></div>
    <div class="top-bar-sub">Minnesota business acquisition pipeline &middot; updated daily</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="stats-row">
  <div class="stat-pill"><div class="sp-label">Total</div><div class="sp-value blue">{n_total}</div></div>
  <div class="stat-pill"><div class="sp-label">Showing</div><div class="sp-value">{n_filtered}</div></div>
  <div class="stat-pill"><div class="sp-label">Strong Match</div><div class="sp-value green">{n_shortlist}</div></div>
  <div class="stat-pill"><div class="sp-label">Worth a Look</div><div class="sp-value amber">{n_review}</div></div>
  <div class="stat-pill"><div class="sp-label">Saved</div><div class="sp-value">{n_watchlist}</div></div>
</div>
""", unsafe_allow_html=True)


# ── Search & quick filters ─────────────────────────────────────────────────────
search_col, _ = st.columns([2, 1])
with search_col:
    search_query = st.text_input(
        "", placeholder="🔍  Search business name, industry, or location...",
        label_visibility="collapsed",
    )

p1, p2, p3, p4, p5, p6 = st.columns(6)
active = st.session_state.active_preset

_n_coc          = len(base_filtered[base_filtered["coc_return_20pct"].notna() & (base_filtered["coc_return_20pct"] >= 0.20)])
_pdf_ids = set(st.session_state.get("pdf_data", {}).keys())
if "has_pdf" in df.columns:
    _csv_pdf = set(df[df["has_pdf"].fillna("False").astype(str).str.lower() == "true"]["id"].astype(str))
else:
    _csv_pdf = set()
_n_opportunities = len(_csv_pdf | _pdf_ids)
_n_wl           = len(st.session_state.watchlist)
_n_rejected     = len(df[df["bucket"] == "AUTO-REJECT"])
_n_archived     = len(df[df["is_active"].fillna("True").astype(str).str.lower() == "false"]) if "is_active" in df.columns else 0

def _preset(col, label, key):
    with col:
        is_active = active == key
        if st.button(label, key=f"preset_{key}",
                     type="primary" if is_active else "secondary",
                     use_container_width=True):
            st.session_state.active_preset = None if is_active else key
            st.rerun()

_preset(p1, f"All  ({len(base_filtered)})",           "all")
_preset(p2, f"Top Picks  ({_n_coc})",               "best_returns")
_preset(p3, f"Opportunities  ({_n_opportunities})",  "opportunities")
_preset(p4, f"Saved  ({_n_wl})",                    "watchlist")
_preset(p5, f"Rejected  ({_n_rejected})",           "rejected")
_preset(p6, f"Archived  ({_n_archived})",        "archived")

# Category filter
selected_categories = st.multiselect(
    "", options=list(CATEGORY_CONFIG.keys()),
    placeholder="Filter by category  (leave empty = all)",
    label_visibility="collapsed",
)


# ── Apply search + preset + category filters ───────────────────────────────────
filtered = base_filtered.copy()

if search_query:
    q = search_query.lower()
    def _search_col(df, col):
        return df[col].fillna("").astype(str).str.lower().str.contains(q, na=False)

    smask = (
        _search_col(filtered, "id")
        | _search_col(filtered, "title")
        | _search_col(filtered, "industry")
        | _search_col(filtered, "location")
        | _search_col(filtered, "description")
    )
    filtered = filtered[smask]

if selected_categories:
    cat_mask = pd.Series([False] * len(filtered), index=filtered.index)
    for cat_name in selected_categories:
        col = CATEGORY_CONFIG[cat_name]["col"]
        cat_mask |= filtered[col].fillna(False).astype(bool)
    filtered = filtered[cat_mask]

ap = st.session_state.active_preset
if ap == "best_returns":
    filtered = filtered[filtered["coc_return_20pct"].notna() & (filtered["coc_return_20pct"] >= 0.20)]
    filtered = filtered.sort_values("coc_return_20pct", ascending=False)
elif ap == "opportunities":
    all_pdf_ids = _csv_pdf | _pdf_ids
    filtered = df[df["id"].astype(str).isin(all_pdf_ids)].copy()
elif ap == "watchlist":
    wl = st.session_state.watchlist
    filtered = filtered[filtered["id"].astype(str).isin(wl)]
elif ap == "rejected":
    filtered = df[df["bucket"] == "AUTO-REJECT"].copy()
elif ap == "archived":
    if "is_active" in df.columns:
        filtered = df[df["is_active"].fillna("True").astype(str).str.lower() == "false"].copy()
    else:
        filtered = df.iloc[0:0].copy()  # empty

if ap != "best_returns":
    filtered = filtered.sort_values("score", ascending=False)

# Clear selection if no longer visible
if st.session_state.selected_id is not None:
    if not any(filtered["id"].astype(str) == str(st.session_state.selected_id)):
        st.session_state.selected_id = None


# ── Detail panel renderer ──────────────────────────────────────────────────────
def render_detail_panel(row):
    # Merge pdf_data fields (from Supabase) over CSV row values
    row = dict(row)
    listing_id  = str(row.get("id", ""))
    pdf_record  = st.session_state.get("pdf_data", {}).get(listing_id, {})
    pdf_fields  = pdf_record.get("fields", {})
    for k, val in pdf_fields.items():
        if val is not None and str(val) not in ("", "None", "null"):
            row[k] = val

    title    = row.get("title", "Untitled")
    url      = row.get("url", "")
    bucket   = str(row.get("bucket", "SKIP"))
    score    = int(row.get("score", 0))
    asking   = row.get("asking_price")
    cf       = row.get("annual_cash_flow")
    rev      = row.get("annual_revenue")
    emps     = row.get("employees")
    absentee = row.get("absentee", "No")

    is_active = str(row.get("is_active", "True")).lower() != "false"
    if not is_active:
        last_seen = row.get("last_seen", "")
        st.warning(f"This listing is no longer active on Sunbelt. Last seen: {str(last_seen)[:10] if last_seen else 'unknown'}")

    description   = str(row.get("description") or "")
    has_pdf_csv   = str(row.get("has_pdf", "False")).lower() == "true"
    has_pdf_cloud = bool(pdf_record)   # only True if uploaded via dashboard/Supabase
    has_pdf       = has_pdf_csv or has_pdf_cloud
    listing_agent = str(row.get("listing_agent") or "")
    if listing_agent == "nan": listing_agent = ""

    col_close, col_link = st.columns([1, 1])
    with col_close:
        if st.button("✕ Close", key="close_panel", use_container_width=True):
            st.session_state.selected_id = None
            st.rerun()
    with col_link:
        if url and str(url) != "nan":
            source = str(row.get("source") or "sunbelt").lower()
            site_label = "Calhoun" if source == "calhoun" else "Sunbelt"
            st.link_button(f"View on {site_label} →", url, use_container_width=True)

    sc            = _score_color(score)
    bclass        = _bucket_cls(bucket)
    bucket_label  = BUCKET_DISPLAY.get(bucket, bucket)
    st.markdown(f"""
<div class="dp-header">
  <div class="dp-title">{title}</div>
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
    <span class="bucket-badge {bclass}">{bucket_label}</span>
    <span style="font-size:12px;color:#717171;font-weight:600">Score {score}/100</span>
  </div>
  <div class="score-bar-wrap">
    <div class="score-bar-track"><div class="score-bar-fill" style="width:{score}%;background:{sc}"></div></div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── PDF badge + upload ──────────────────────────────────────────────────────
    if has_pdf:
        agent_str = f" · {listing_agent}" if listing_agent else ""
        badge_col, dl_col = st.columns([3, 1])
        with badge_col:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;'
                f'padding:8px 12px;background:#7C3AED0D;border-radius:10px;border:1px solid #7C3AED22">'
                f'<span style="font-size:13px">📄</span>'
                f'<span style="font-size:12px;font-weight:700;color:#7C3AED">PDF Reviewed</span>'
                f'<span style="font-size:11px;color:#717181">{agent_str}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with dl_col:
            if has_pdf_cloud:
                try:
                    pdf_bytes = _get_supabase().storage.from_("pdfs").download(f"{listing_id}.pdf")
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name=f"{listing_id}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception:
                    pass

    if not has_pdf_cloud:
        uploaded = st.file_uploader(
            "Attach broker PDF" if not has_pdf_csv else "Upload PDF to enable download & full chat context",
            type="pdf",
            key=f"upload_{listing_id}",
            help="Upload a broker PDF to enrich this listing and enable AI chat with full document context",
        )
        if uploaded is not None:
            with st.spinner("Extracting and analyzing PDF…"):
                file_bytes = uploaded.read()
                pdf_text   = _extract_pdf_text(file_bytes)
                fields     = _extract_pdf_fields(pdf_text)
                _save_pdf_data(listing_id, fields, pdf_text)
                _upload_pdf_storage(listing_id, file_bytes)
                st.session_state.pdf_data[listing_id] = {"fields": fields, "pdf_text": pdf_text}
            st.success("PDF imported — listing enriched.")
            st.rerun()
        st.markdown('<div class="dp-section">Business Overview</div>', unsafe_allow_html=True)
        pdf_full_text = pdf_record.get("pdf_text", "") if pdf_record else ""
        if pdf_full_text:
            st.markdown(
                f'<div style="font-size:13px;line-height:1.7;color:#334155;padding:4px 0 12px;'
                f'white-space:pre-wrap">{pdf_full_text}</div>',
                unsafe_allow_html=True,
            )
        elif description:
            st.markdown(
                f'<div style="font-size:13px;line-height:1.7;color:#334155;padding:4px 0 12px">{description}</div>',
                unsafe_allow_html=True,
            )

    # ── Deal Summary FIRST ──────────────────────────────────────────────────────
    narrative = row.get("narrative", "")
    if narrative and str(narrative) != "nan":
        def _ns(text, prefix, icon, bg, border, lc):
            if prefix not in text: return ""
            body = text.split(prefix, 1)[1]
            for stop in ["What's attractive:", "Watch-outs:", "Bottom line:"]:
                if stop != prefix and stop in body:
                    body = body.split(stop)[0]
            items = [s.strip().rstrip(".") for s in body.strip().split(";") if s.strip()]
            bullets = "".join(f'<li style="margin-bottom:3px">{i}.</li>' for i in items)
            return (f'<div class="nar-block" style="background:{bg};border:1px solid {border}">'
                    f'<div class="nar-label" style="color:{lc}">{icon} {prefix.rstrip(":")}</div>'
                    f'<ul class="nar-list">{bullets}</ul></div>')

        intro = narrative.split("What's attractive:")[0].strip() if "What's attractive:" in narrative else ""
        html = ""
        if intro:
            html += f'<div style="font-size:13px;color:#717171;margin-bottom:10px;line-height:1.65">{intro}</div>'
        html += _ns(narrative, "What's attractive:", "✅", "#F0FDF4", "#86EFAC", "#15803D")
        html += _ns(narrative, "Watch-outs:", "⚠️", "#FFFBEB", "#FCD34D", "#B45309")
        if "Bottom line:" in narrative:
            bl = narrative.split("Bottom line:", 1)[1].strip()
            html += (f'<div class="nar-bottom">'
                     f'<div class="nar-bottom-label">⚖️ Bottom Line</div>'
                     f'<div class="nar-bottom-text">{bl}</div></div>')
        st.markdown(html, unsafe_allow_html=True)

    # ── KPIs ───────────────────────────────────────────────────────────────────
    st.markdown('<div class="dp-section">Financials</div>', unsafe_allow_html=True)
    k1, k2, k3 = st.columns(3)
    k1.metric("Asking Price",    _fmt(asking))
    k2.metric("Cash Flow (SDE)", _fmt(cf))
    k3.metric("Annual Revenue",  _fmt(rev))

    k4, k5, k6 = st.columns(3)
    k4.metric("Employees",   int(emps) if pd.notna(emps) else "—")
    k5.metric("Absentee",    absentee)
    k6.metric("Location",    row.get("location", "—") or "—")

    # Deal metrics
    rev_multiple = row.get("revenue_multiple")
    sde_margin   = row.get("sde_margin")
    rev_per_emp  = row.get("revenue_per_employee")

    st.markdown('<div class="dp-section">Deal Metrics</div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Revenue Multiple", f"{rev_multiple:.2f}x" if rev_multiple else "—",
              help="Asking ÷ revenue. Service: 0.5–1.5x typical.")
    m2.metric("SDE Margin",  f"{sde_margin*100:.0f}%" if sde_margin else "—",
              help="CF ÷ revenue. 20%+ is healthy.")
    m3.metric("Rev / Employee", _fmt(rev_per_emp) if rev_per_emp else "—",
              help="$150K+ is strong.")

    # Category notes
    cat_notes = {
        "Restaurant & Bar":      "🍽️ Thin margins (10–20% SDE normal). Verify lease terms and equipment.",
        "Retail":                "🛍️ Confirm inventory included. Rev multiples 0.3–0.8x typical.",
        "Manufacturing":         "🏭 Equipment drives value. Check machinery age and customer concentration.",
        "Automotive":            "🚗 Count service bays. Technician tenure is the key constraint.",
        "Distribution":          "🚚 Verify fleet condition. Route density determines defensibility.",
        "Financial Services":    "💼 Client retention rate is critical. CPA multiples: 1–2x revenue.",
        "Hospitality":           "🏨 Check occupancy rate and RevPAR. Verify franchise agreement terms.",
        "Technology / IT":       "💻 MSP recurring MRR is key. Expect SDE margins 30–50%.",
        "Education & Childcare": "🎓 Licensing and enrollment trends matter.",
        "Healthcare":            "🩺 Verify payer mix. Check licensing transfer requirements.",
        "Trades":                "🔧 Technician headcount and tenure are key. Service contracts add defensibility.",
        "Construction":          "🏗️ Backlog size and contract types (fixed vs T&M) drive risk.",
        "Beauty & Wellness":     "💇 Chair/suite rental vs. employee model affects transferability.",
    }
    cats = _row_categories(row)
    for cat_name, _ in cats:
        if cat_name in cat_notes:
            st.info(cat_notes[cat_name])

    # SBA financing tabs
    st.markdown('<div class="dp-section">SBA Financing</div>', unsafe_allow_html=True)
    tab_10, tab_20, tab_sf = st.tabs(["10% Down", "20% Down", "Seller Financed"])

    def _sba_tab(down_key, monthly_key, cf_key, coc_key, dscr_key):
        down    = row.get(down_key)
        monthly = row.get(monthly_key)
        cf_aft  = row.get(cf_key)
        coc     = row.get(coc_key)
        dscr    = row.get(dscr_key)
        c1, c2 = st.columns(2)
        c1.metric("Down Payment",    _fmt(down))
        c2.metric("Monthly Payment", _fmt(monthly))
        c3, c4, c5 = st.columns(3)
        c3.metric("CF After Debt",   _fmt(cf_aft))
        c4.metric("CoC Return",      _fmt(coc, "%"))
        c5.metric("DSCR",            _fmt(dscr, "x"))

    with tab_10:
        _sba_tab("down_10","sba_monthly_10pct","cf_after_debt_10pct","coc_return_10pct","dscr_10pct")
    with tab_20:
        _sba_tab("down_20","sba_monthly_20pct","cf_after_debt_20pct","coc_return_20pct","dscr_20pct")
    with tab_sf:
        s1, s2, s3 = st.columns(3)
        s1.metric("Your Cash Down",  "$0")
        s2.metric("Seller Note",     _fmt(row.get("seller_note_amount")))
        s3.metric("Note Payment",    (_fmt(row.get("seller_note_monthly")) + "/mo") if row.get("seller_note_monthly") else "—")
        s4, s5, s6 = st.columns(3)
        s4.metric("CF Yr 1–2",  _fmt(row.get("cf_during_standby")))
        s5.metric("CF Yr 3+",   _fmt(row.get("cf_after_seller_financing")))
        s6.metric("DSCR Yr 3+", _fmt(row.get("dscr_seller_financed"), "x") if row.get("dscr_seller_financed") else "—")
        st.caption("⚠️ SBA requires seller note on full standby for 24 months.")

    # Business details
    st.markdown('<div class="dp-section">Business Details</div>', unsafe_allow_html=True)
    d1, d2, d3 = st.columns(3)
    d1.metric("Industry",        row.get("industry", "—") or "—")
    d2.metric("Years Operating", row.get("years_in_business", "—") or "—")
    d3.metric("Franchise?",      row.get("is_franchise", "—") or "—")
    d4, d5, d6 = st.columns(3)
    d4.metric("SBA Pre-Approved?", row.get("sba_available", "—") or "—")
    d5.metric("Real Estate",       row.get("real_estate", "—") or "—")
    d6.metric("Listing Agent",     listing_agent or "—")

    reason = row.get("reason_for_selling", "") or ""
    if reason and str(reason) != "nan":
        st.markdown(f'<div style="font-size:12px;color:#475569;margin-top:8px"><b>Reason for selling:</b> {reason}</div>',
                    unsafe_allow_html=True)

    # Tags
    tags = []
    if absentee in ("Likely", "Possible"):
        tags.append('<span class="cat-tag" style="background:#EEF2FF;color:#4F46E5">🏠 Absentee</span>')
    for cat_name, cfg in cats:
        tags.append(f'<span class="cat-tag" style="background:{cfg["bg"]};color:{cfg["color"]}">{cfg["emoji"]} {cat_name}</span>')
    if tags:
        st.markdown(f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px">{"".join(tags)}</div>',
                    unsafe_allow_html=True)

    # ── Ask Scout ──────────────────────────────────────────────────────────────
    st.markdown('<div class="dp-section">Ask Scout</div>', unsafe_allow_html=True)
    chat_key = f"chat_{listing_id}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    for msg in st.session_state[chat_key]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask about this opportunity…", key=f"ci_{listing_id}"):
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        context = _build_listing_context(row)
        reply = _chat_response(st.session_state[chat_key], context)
        st.session_state[chat_key].append({"role": "assistant", "content": reply})
        st.rerun()

    if st.session_state[chat_key]:
        if st.button("Clear chat", key=f"clearchat_{listing_id}", use_container_width=False):
            st.session_state[chat_key] = []
            st.rerun()

    # Narrative rendered at top — skip here

    # Scoring signals
    reasons = row.get("reasons", "")
    if reasons and str(reasons) != "nan":
        st.markdown('<div class="dp-section">Scoring Signals</div>', unsafe_allow_html=True)
        st.info(str(reasons))

    # ── Operator Profile ───────────────────────────────────────────────────────
    st.markdown('<div class="dp-section">Operator Profile</div>', unsafe_allow_html=True)
    lid     = str(row.get("id", ""))
    profile = _effective_profile(row)

    for dim, cfg in DIMENSIONS.items():
        v  = profile[dim]
        c  = _dim_score_color(v)
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">'
                f'<span style="font-size:13px">{cfg["icon"]}</span>'
                f'<span style="font-size:12px;font-weight:600;color:#222222">{cfg["label"]}</span>'
                f'</div>'
                f'<div style="background:#EBEBEB;border-radius:4px;height:6px;margin-bottom:10px">'
                f'<div style="width:{v/3*100:.0f}%;background:{c};height:6px;border-radius:4px"></div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with c2:
            new_val = st.radio(
                f"_{dim}",
                options=[1, 2, 3],
                index=v - 1,
                horizontal=True,
                label_visibility="collapsed",
                key=f"prof_{lid}_{dim}",
            )
            if new_val != v:
                overrides = dict(st.session_state.overrides)
                overrides.setdefault(lid, {})[dim] = new_val
                st.session_state.overrides = overrides
                _save_override(lid, dim, new_val)
                st.rerun()



# ── Deal list renderer ─────────────────────────────────────────────────────────
def render_deal_list(rows):
    watchlist   = st.session_state.watchlist
    selected_id = st.session_state.selected_id

    for _, row in rows.iterrows():
        lid      = str(row.get("id", ""))
        bucket   = str(row.get("bucket", "SKIP"))
        score    = int(row.get("score", 0))
        title    = row.get("title", "Untitled")
        location = str(row.get("location") or "")
        industry = str(row.get("industry") or "")
        asking   = row.get("asking_price")
        cf       = row.get("annual_cash_flow")
        coc      = row.get("coc_return_20pct")
        absentee = row.get("absentee", "No")
        is_saved = lid in watchlist
        is_sel   = str(selected_id) == lid

        sc            = _score_color(score)
        bclass        = _bucket_cls(bucket)
        bucket_label  = BUCKET_DISPLAY.get(bucket, bucket)
        sel_class     = "selected" if is_sel else ""
        cat_name, cat_cfg = _primary_category(row)

        bucket_card_cls = {
            "SHORTLIST":   "bucket-shortlist",
            "REVIEW":      "bucket-review",
            "AUTO-REJECT": "bucket-reject",
        }.get(bucket, "")

        meta_parts = []
        if location and location != "nan": meta_parts.append(f"📍 {location}")
        if industry and industry != "nan": meta_parts.append(industry)
        meta_str = "  ·  ".join(meta_parts)

        source = str(row.get("source", "sunbelt") or "sunbelt").lower()
        source_label = "Calhoun" if source == "calhoun" else "Sunbelt"
        source_color = "#0066CC" if source == "calhoun" else "#FF385C"
        source_html = (f'<span style="font-size:10px;font-weight:700;padding:2px 6px;'
                       f'border-radius:6px;background:{source_color}18;color:{source_color}">'
                       f'{source_label}</span>')

        has_pdf = str(row.get("has_pdf", "False")).lower() == "true"
        pdf_html = ('<span style="font-size:10px;font-weight:700;padding:2px 6px;border-radius:6px;'
                    'background:#7C3AED18;color:#7C3AED">📄 Reviewed</span>') if has_pdf else ""

        coc_html = (f'<span class="coc-badge">CoC {_fmt(coc, "%")}</span>'
                    if coc and not (isinstance(coc, float) and pd.isna(coc)) else "")
        cf_html  = (f'<span class="cf-badge">CF {_fmt(cf, "$M")}</span>'
                    if cf and not (isinstance(cf, float) and pd.isna(cf)) else "")
        score_pill_html = (f'<span class="score-pill" style="background:{sc}22;color:{sc}">'
                           f'{score}</span>')

        html = (
            f'<div class="deal-card {bucket_card_cls} {sel_class}">'
            f'<div class="dc-top">'
            f'<div class="dc-title">{cat_cfg["emoji"]} {title}</div>'
            f'<div class="dc-price">{_fmt(asking, "$M")}</div>'
            f'</div>'
            f'<div class="dc-meta">{meta_str}</div>'
            f'<div class="dc-footer">'
            f'<span class="bucket-badge {bclass}">{bucket_label}</span>'
            f'{coc_html}'
            f'{cf_html}'
            f'<span class="cat-tag" style="background:{cat_cfg["bg"]};color:{cat_cfg["color"]}">'
            f'{cat_name}</span>'
            f'{source_html}'
            f'{pdf_html}'
            f'{score_pill_html}'
            f'</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)

        st.markdown('<div class="card-actions">', unsafe_allow_html=True)
        btn_a, btn_b = st.columns([5, 1])
        with btn_a:
            view_label = "Selected" if is_sel else "View details →"
            view_type  = "primary" if is_sel else "secondary"
            if st.button(view_label, key=f"view_{lid}", use_container_width=True, type=view_type):
                st.session_state.selected_id = None if is_sel else lid
                st.rerun()
        with btn_b:
            bookmark = "🔖" if is_saved else "♡"
            if st.button(bookmark, key=f"wl_{lid}", use_container_width=True):
                new_wl = set(st.session_state.watchlist)
                if is_saved:
                    new_wl.discard(lid)
                    _save_watchlist(new_wl, removed=lid)
                else:
                    new_wl.add(lid)
                    _save_watchlist(new_wl, added=lid)
                st.session_state.watchlist = new_wl
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


# ── Table renderer ─────────────────────────────────────────────────────────────
def render_table(rows):
    display_cols = [
        "score", "bucket", "title", "industry", "asking_price",
        "annual_cash_flow", "cf_after_debt_20pct", "coc_return_20pct",
        "dscr_20pct", "revenue_multiple", "sde_margin",
        "absentee", "location", "url",
    ]
    available  = [c for c in display_cols if c in rows.columns]
    display_df = rows[available].copy()
    for col in ["coc_return_20pct", "sde_margin"]:
        if col in display_df.columns:
            display_df[col] = display_df[col] * 100

    event = st.dataframe(
        display_df,
        column_config={
            "score":               st.column_config.NumberColumn("Score",           width="small"),
            "bucket":              st.column_config.TextColumn("Bucket",            width="small"),
            "title":               st.column_config.TextColumn("Business",          width="large"),
            "industry":            st.column_config.TextColumn("Industry",          width="medium"),
            "asking_price":        st.column_config.NumberColumn("Price ($)",        format="%.0f", width="small"),
            "annual_cash_flow":    st.column_config.NumberColumn("Cash Flow ($)",    format="%.0f", width="small"),
            "cf_after_debt_20pct": st.column_config.NumberColumn("CF After Debt ($)",format="%.0f",width="small"),
            "coc_return_20pct":    st.column_config.NumberColumn("CoC (%)",          format="%.0f", width="small"),
            "dscr_20pct":          st.column_config.NumberColumn("DSCR",             format="%.2f", width="small"),
            "revenue_multiple":    st.column_config.NumberColumn("Rev Multiple",     format="%.2f", width="small"),
            "sde_margin":          st.column_config.NumberColumn("SDE Margin (%)",   format="%.0f", width="small"),
            "absentee":            st.column_config.TextColumn("Absentee",           width="small"),
            "location":            st.column_config.TextColumn("Location",           width="small"),
            "url":                 st.column_config.LinkColumn("Link",               width="small"),
        },
        hide_index=True, height=680, use_container_width=True,
        selection_mode="single-row", on_select="rerun",
    )
    if event.selection.rows:
        selected_row = rows.iloc[event.selection.rows[0]]
        st.session_state.selected_id = str(selected_row.get("id", ""))
        st.rerun()


# ── Profile column view renderer ───────────────────────────────────────────────
def render_profile_view(rows):
    selected_id = st.session_state.selected_id

    dim_keys   = list(DIMENSIONS.keys())
    dim_labels = [f"{DIMENSIONS[d]['icon']} {DIMENSIONS[d]['label']}" for d in dim_keys]

    # Header
    header_html = (
        '<div style="display:grid;grid-template-columns:2fr 1fr ' + ' '.join(['80px'] * 8) + ';'
        'gap:8px;padding:8px 12px;background:#F7F7F7;border-radius:12px 12px 0 0;'
        'font-size:11px;font-weight:700;color:#717171;text-transform:uppercase;letter-spacing:0.3px;'
        'border:1px solid #EBEBEB;border-bottom:none;margin-bottom:0">'
        '<div>Business</div><div>Price</div>'
        + "".join(f'<div style="text-align:center">{lbl}</div>' for lbl in dim_labels)
        + '</div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)

    for _, row in rows.iterrows():
        lid      = str(row.get("id", ""))
        title    = row.get("title", "Untitled")
        asking   = row.get("asking_price")
        is_sel   = str(selected_id) == lid
        profile  = _effective_profile(row)

        def _dot(v):
            c = _dim_score_color(v)
            return (f'<div style="display:flex;align-items:center;justify-content:center">'
                    f'<div style="width:28px;height:28px;border-radius:50%;background:{c}22;'
                    f'color:{c};font-size:11px;font-weight:800;display:flex;align-items:center;'
                    f'justify-content:center">{v}</div></div>')

        dots = "".join(_dot(profile[d]) for d in dim_keys)
        bg   = "#FFF8F9" if is_sel else "white"
        bl   = "#FF385C" if is_sel else "#EBEBEB"

        row_html = (
            f'<div style="display:grid;grid-template-columns:2fr 1fr ' + ' '.join(['80px'] * 8) + ';'
            f'gap:8px;padding:10px 12px;background:{bg};'
            f'border:1px solid #EBEBEB;border-left:4px solid {bl};border-bottom:none;'
            f'align-items:center">'
            f'<div style="font-size:13px;font-weight:600;color:#222222">{title}</div>'
            f'<div style="font-size:13px;font-weight:700;color:#222222">{_fmt(asking, "$M")}</div>'
            f'{dots}'
            f'</div>'
        )
        st.markdown(row_html, unsafe_allow_html=True)

        if st.button("View →", key=f"pv_{lid}", use_container_width=True):
            st.session_state.selected_id = None if is_sel else lid
            st.rerun()

    # Close border
    st.markdown('<div style="height:4px;background:#F7F7F7;border:1px solid #EBEBEB;border-top:none;border-radius:0 0 12px 12px"></div>', unsafe_allow_html=True)


# ── Pipeline chart (always visible, above list) ─────────────────────────────────
with st.expander("Pipeline Overview", expanded=False):
    chart_df = filtered[filtered["asking_price"].notna() & filtered["annual_cash_flow"].notna()].copy()
    chart_df["bucket_display"] = chart_df["bucket"].fillna("SKIP")
    if len(chart_df) > 0:
        color_map = {"SHORTLIST": "#008A05", "REVIEW": "#C45C00", "AUTO-REJECT": "#C13515", "SKIP": "#B0B0B0"}
        fig = px.scatter(chart_df, x="asking_price", y="annual_cash_flow",
            color="bucket_display", color_discrete_map=color_map,
            hover_data={"title": True, "location": True, "score": True, "bucket_display": False},
            labels={"asking_price": "Asking Price ($)", "annual_cash_flow": "Cash Flow ($)", "bucket_display": "Match"},
            title="")
        fig.update_traces(marker=dict(size=9, opacity=0.85))
        fig.update_layout(
            plot_bgcolor="white", paper_bgcolor="white",
            font=dict(family="Inter", size=12),
            margin=dict(l=40, r=20, t=10, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=260,
        )
        fig.update_xaxes(tickprefix="$", tickformat=",.0f", gridcolor="#F5F5F5", linecolor="#EBEBEB")
        fig.update_yaxes(tickprefix="$", tickformat=",.0f", gridcolor="#F5F5F5", linecolor="#EBEBEB")
        st.plotly_chart(fig, use_container_width=True)

# ── Main layout ────────────────────────────────────────────────────────────────
view_mode = st.radio("View", ["List", "Table", "Profile"], horizontal=True, label_visibility="collapsed")

if len(filtered) == 0:
    st.info("No listings match the current filters.")
    st.stop()

selected_id  = st.session_state.selected_id
selected_row = None
if selected_id is not None:
    match = filtered[filtered["id"].astype(str) == str(selected_id)]
    if len(match) > 0:
        selected_row = match.iloc[0]

# Split layout
list_col, detail_col = st.columns([5, 4], gap="large")

with list_col:
    count_label = f"{len(filtered)} listing{'s' if len(filtered) != 1 else ''}"
    st.caption(count_label)

    if view_mode == "List":
        render_deal_list(filtered)
    elif view_mode == "Profile":
        render_profile_view(filtered)
    else:
        render_table(filtered)

with detail_col:
    if selected_row is not None:
        with st.container(border=True):
            render_detail_panel(selected_row)
    else:
        st.markdown("""
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
            height:260px;text-align:center;padding:40px">
  <div style="font-size:13px;color:#717171;margin-top:16px">Select a listing to view the full deal sheet</div>
</div>
""", unsafe_allow_html=True)
