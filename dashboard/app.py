import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

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

BUCKET_COLOR = {
    "SHORTLIST":   "#10B981",
    "REVIEW":      "#F59E0B",
    "SKIP":        "#94A3B8",
    "AUTO-REJECT": "#EF4444",
}

CSV_PATH = Path(__file__).resolve().parents[1] / "output" / "candidates.csv"

st.set_page_config(page_title="Sunbelt Scout", layout="wide", page_icon="🏢")

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Top header bar ── */
.top-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 0 16px;
    border-bottom: 2px solid #E2E8F0;
    margin-bottom: 20px;
}
.top-bar-title {
    font-size: 20px;
    font-weight: 800;
    color: #0F172A;
    letter-spacing: -0.5px;
}
.top-bar-title span { color: #2563EB; }
.top-bar-sub { font-size: 12px; color: #94A3B8; margin-top: 1px; }

/* ── Stat pills ── */
.stats-row { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.stat-pill {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 10px 16px;
    min-width: 100px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.stat-pill .sp-label { font-size: 10px; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px; }
.stat-pill .sp-value { font-size: 22px; font-weight: 800; color: #0F172A; line-height: 1.2; margin-top: 2px; }
.stat-pill .sp-value.green  { color: #10B981; }
.stat-pill .sp-value.amber  { color: #F59E0B; }
.stat-pill .sp-value.red    { color: #EF4444; }
.stat-pill .sp-value.blue   { color: #2563EB; }

/* ── Deal list rows ── */
.deal-row {
    background: white;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 12px 14px;
    margin-bottom: 6px;
    cursor: pointer;
    transition: box-shadow 0.15s, border-color 0.15s;
    border-left: 4px solid transparent;
}
.deal-row:hover {
    box-shadow: 0 3px 12px rgba(37,99,235,0.1);
    border-color: #BFDBFE;
}
.deal-row.selected {
    border-left-color: #2563EB;
    background: #EFF6FF;
    border-color: #BFDBFE;
}
.dr-top { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 5px; }
.dr-title { font-size: 14px; font-weight: 700; color: #0F172A; line-height: 1.35; }
.dr-price { font-size: 13px; font-weight: 700; color: #0F172A; white-space: nowrap; }
.dr-meta { font-size: 11px; color: #64748B; margin-bottom: 6px; }
.dr-bottom { display: flex; align-items: center; gap: 8px; }

/* ── Bucket badge ── */
.bucket-badge {
    display: inline-block;
    font-size: 9px;
    font-weight: 800;
    padding: 2px 7px;
    border-radius: 20px;
    letter-spacing: 0.3px;
    text-transform: uppercase;
}
.bb-shortlist { background: #D1FAE5; color: #065F46; }
.bb-review    { background: #FEF3C7; color: #92400E; }
.bb-skip      { background: #F1F5F9; color: #475569; }
.bb-reject    { background: #FEE2E2; color: #991B1B; }

/* ── Score chip ── */
.score-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 10px;
    font-weight: 700;
    color: #475569;
}
.score-dot {
    width: 28px;
    height: 6px;
    border-radius: 3px;
}

/* ── Category tag ── */
.cat-tag {
    font-size: 10px;
    font-weight: 600;
    padding: 2px 7px;
    border-radius: 20px;
}

/* ── Detail panel ── */
.dp-header { padding-bottom: 16px; border-bottom: 1px solid #F1F5F9; margin-bottom: 16px; }
.dp-title { font-size: 18px; font-weight: 800; color: #0F172A; line-height: 1.35; margin-bottom: 6px; }
.dp-section {
    font-size: 10px;
    font-weight: 800;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin: 18px 0 10px;
    padding-top: 14px;
    border-top: 1px solid #F1F5F9;
}

/* ── Score bar ── */
.score-bar-wrap { margin: 10px 0; }
.score-bar-label { display: flex; justify-content: space-between; font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 4px; }
.score-bar-track { background: #F1F5F9; border-radius: 4px; height: 6px; overflow: hidden; }
.score-bar-fill { height: 6px; border-radius: 4px; }

/* ── Finance grid ── */
.fin-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px; }
.fin-cell {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 8px;
    padding: 10px 12px;
}
.fin-label { font-size: 10px; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.4px; }
.fin-value { font-size: 17px; font-weight: 800; color: #0F172A; margin-top: 2px; }
.fin-value.green { color: #10B981; }
.fin-value.red   { color: #EF4444; }
.fin-value.amber { color: #F59E0B; }

/* ── Narrative blocks ── */
.nar-block { border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; }
.nar-label { font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; }
.nar-list { margin: 0; padding-left: 16px; font-size: 12px; line-height: 1.7; color: #1E293B; }
.nar-bottom { background: #1E3A5F; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px; }
.nar-bottom-label { font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.6px; color: #93C5FD; margin-bottom: 4px; }
.nar-bottom-text { font-size: 13px; font-weight: 600; color: white; line-height: 1.5; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: white !important;
    border-right: 1px solid #E2E8F0 !important;
}
[data-testid="stSidebar"] label { font-size: 13px !important; color: #374151 !important; }
[data-testid="stSidebar"] .stMarkdown h3 {
    font-size: 11px !important;
    font-weight: 800 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.6px !important;
    color: #94A3B8 !important;
}

/* ── Expander ── */
[data-testid="stExpander"] { background: white !important; border: 1px solid #E2E8F0 !important; border-radius: 10px !important; }

/* ── Buttons ── */
.stButton > button {
    border-radius: 7px;
    font-size: 12px;
    font-weight: 700;
    padding: 5px 0;
    transition: all 0.12s;
}
[data-testid="stBaseButton-primary"] {
    background: #2563EB !important;
    color: white !important;
    border: none !important;
}
[data-testid="stBaseButton-primary"]:hover { background: #1D4ED8 !important; }
[data-testid="stBaseButton-secondary"] {
    background: white !important;
    color: #374151 !important;
    border: 1.5px solid #D1D5DB !important;
}
[data-testid="stBaseButton-secondary"]:hover {
    background: #F9FAFB !important;
    border-color: #9CA3AF !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #F8FAFC !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    padding: 10px 12px !important;
}
[data-testid="metric-container"] label {
    font-size: 10px !important;
    font-weight: 700 !important;
    color: #64748B !important;
    text-transform: uppercase !important;
    letter-spacing: 0.4px !important;
}
[data-testid="stMetricValue"] { font-size: 15px !important; font-weight: 800 !important; }

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab"] { font-size: 13px; font-weight: 600; }

/* ── Divider ── */
hr { border-color: #F1F5F9 !important; margin: 12px 0 !important; }
</style>
""", unsafe_allow_html=True)


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    if not CSV_PATH.exists():
        return pd.DataFrame()
    df = pd.read_csv(CSV_PATH)
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
if "watchlist"     not in st.session_state: st.session_state.watchlist     = set()
if "active_preset" not in st.session_state: st.session_state.active_preset = None


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
    if score >= 65: return "#10B981"
    if score >= 35: return "#F59E0B"
    return "#94A3B8"

def _bucket_cls(bucket):
    return {"SHORTLIST": "bb-shortlist", "REVIEW": "bb-review", "AUTO-REJECT": "bb-reject"}.get(bucket, "bb-skip")

def _row_categories(row):
    return [(name, cfg) for name, cfg in CATEGORY_CONFIG.items() if row.get(cfg["col"])]

def _primary_category(row):
    cats = _row_categories(row)
    return cats[0] if cats else ("Other", {"emoji": "🏢", "col": None, "color": "#475569", "bg": "#F1F5F9"})


# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown("### Filters")

st.sidebar.markdown("### Scoring")
apply_scoring = st.sidebar.checkbox("Apply scoring filters", value=False,
    help="When off, all listings are shown regardless of score.")
if apply_scoring:
    all_buckets = sorted(df["bucket"].dropna().unique().tolist())
    buckets = st.sidebar.multiselect("Bucket", options=all_buckets,
        default=[b for b in ["SHORTLIST", "REVIEW"] if b in all_buckets])
    min_score = st.sidebar.slider("Min Score", 0, 100, 35)
else:
    buckets   = None
    min_score = 0

st.sidebar.markdown("---")
st.sidebar.markdown("### Financial")
max_price = st.sidebar.number_input("Max Asking Price ($)", value=5000000, step=100000)
min_price = st.sidebar.number_input("Min Asking Price ($)", value=50000,   step=50000)
min_cf    = st.sidebar.number_input("Min Cash Flow ($)",    value=0,       step=25000)
min_coc   = st.sidebar.slider("Min CoC Return (20% down)", 0, 200, 0, format="%d%%")
min_coc_decimal = min_coc / 100.0

st.sidebar.markdown("---")
st.sidebar.markdown("### Location & Operator")
twin_cities_only = st.sidebar.checkbox("Twin Cities Only")
absentee_only    = st.sidebar.checkbox("Absentee / Semi-Absentee Only")

st.sidebar.markdown("---")
with st.sidebar.expander("📊 How scores work"):
    st.markdown("""
**Buckets:** 🟢 SHORTLIST 65+ · 🟡 REVIEW 35–64 · ⚪ SKIP <35 · 🔴 AUTO-REJECT 0

**Auto-Reject triggers:**
Price outside $50K–$5M · No cash flow · DSCR<1.25 · Not MN · Franchise/cannabis/gambling/digital-only

**Scoring (100 pts):**
💰 Financial 40 · ⚙️ Operations 15 · 💻 Tech gap 15 · 🔁 Recurring 10 · 🏗️ Industry 10 · 📍 Geography 10
""")


# ── Base filters ───────────────────────────────────────────────────────────────
mask = pd.Series([True] * len(df))
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
    <div class="top-bar-title">🏢 Sunbelt <span>Scout</span></div>
    <div class="top-bar-sub">Minnesota business acquisition pipeline · updated daily</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="stats-row">
  <div class="stat-pill"><div class="sp-label">Total</div><div class="sp-value blue">{n_total}</div></div>
  <div class="stat-pill"><div class="sp-label">Showing</div><div class="sp-value">{n_filtered}</div></div>
  <div class="stat-pill"><div class="sp-label">Shortlisted</div><div class="sp-value green">{n_shortlist}</div></div>
  <div class="stat-pill"><div class="sp-label">Review</div><div class="sp-value amber">{n_review}</div></div>
  <div class="stat-pill"><div class="sp-label">Auto-Rejected</div><div class="sp-value red">{n_rejected}</div></div>
  <div class="stat-pill"><div class="sp-label">Saved ⭐</div><div class="sp-value">{n_watchlist}</div></div>
</div>
""", unsafe_allow_html=True)


# ── Search & quick filters ─────────────────────────────────────────────────────
search_col, _ = st.columns([2, 1])
with search_col:
    search_query = st.text_input(
        "", placeholder="🔍  Search business name, industry, or location...",
        label_visibility="collapsed",
    )

p1, p2, p3, p4, p5, p6, p7 = st.columns(7)
active = st.session_state.active_preset

def _preset(col, label, key):
    with col:
        is_active = active == key
        if st.button(label, key=f"preset_{key}",
                     type="primary" if is_active else "secondary",
                     use_container_width=True):
            st.session_state.active_preset = None if is_active else key
            st.rerun()

_preset(p1, "All",           "all")
_preset(p2, "🏆 Best CoC",  "best_returns")
_preset(p3, "📍 Twin Cities","twin_cities")
_preset(p4, "💰 Under $500K","under_500k")
_preset(p5, "🏠 Absentee",  "absentee")
_preset(p6, "⭐ Watchlist",  "watchlist")
_preset(p7, "🔴 Rejected",   "rejected")

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
    smask = (
        filtered["title"].str.lower().str.contains(q, na=False)
        | filtered.get("industry", pd.Series(dtype=str)).str.lower().str.contains(q, na=False)
        | filtered["location"].str.lower().str.contains(q, na=False)
        | filtered.get("description", pd.Series(dtype=str)).str.lower().str.contains(q, na=False)
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
elif ap == "twin_cities":
    tc_pat = "|".join(["minneapolis","saint paul","st\\.paul","bloomington","plymouth",
                        "eden prairie","burnsville","minnetonka","eagan","edina",
                        "maple grove","woodbury","coon rapids","brooklyn park","twin cities","metro"])
    filtered = filtered[filtered["location"].str.contains(tc_pat, case=False, na=False)]
elif ap == "under_500k":
    filtered = filtered[filtered["asking_price"].notna() & (filtered["asking_price"] <= 500000)]
elif ap == "absentee":
    filtered = filtered[filtered["absentee"].isin(["Likely", "Possible"])]
elif ap == "watchlist":
    wl = st.session_state.watchlist
    filtered = filtered[filtered["id"].astype(str).isin(wl)]
elif ap == "rejected":
    filtered = df[df["bucket"] == "AUTO-REJECT"].copy()

if ap != "best_returns":
    filtered = filtered.sort_values("score", ascending=False)

# Clear selection if no longer visible
if st.session_state.selected_id is not None:
    if not any(filtered["id"].astype(str) == str(st.session_state.selected_id)):
        st.session_state.selected_id = None


# ── Detail panel renderer ──────────────────────────────────────────────────────
def render_detail_panel(row):
    title    = row.get("title", "Untitled")
    url      = row.get("url", "")
    bucket   = str(row.get("bucket", "SKIP"))
    score    = int(row.get("score", 0))
    asking   = row.get("asking_price")
    cf       = row.get("annual_cash_flow")
    rev      = row.get("annual_revenue")
    emps     = row.get("employees")
    absentee = row.get("absentee", "No")

    col_close, col_link = st.columns([1, 1])
    with col_close:
        if st.button("✕ Close", key="close_panel", use_container_width=True):
            st.session_state.selected_id = None
            st.rerun()
    with col_link:
        if url and str(url) != "nan":
            st.link_button("View on Sunbelt →", url, use_container_width=True)

    sc = _score_color(score)
    bclass = _bucket_cls(bucket)
    st.markdown(f"""
<div class="dp-header">
  <div class="dp-title">{title}</div>
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
    <span class="bucket-badge {bclass}">{bucket}</span>
    <span style="font-size:12px;color:#64748B;font-weight:700">Score {score}/100</span>
  </div>
  <div class="score-bar-wrap">
    <div class="score-bar-track"><div class="score-bar-fill" style="width:{score}%;background:{sc}"></div></div>
  </div>
</div>
""", unsafe_allow_html=True)

    # KPIs
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
    d4, d5 = st.columns(2)
    d4.metric("SBA Pre-Approved?", row.get("sba_available", "—") or "—")
    d5.metric("Real Estate",       row.get("real_estate", "—") or "—")

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

    # Narrative
    narrative = row.get("narrative", "")
    if narrative and str(narrative) != "nan":
        st.markdown('<div class="dp-section">Deal Summary</div>', unsafe_allow_html=True)

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
            html += f'<div style="font-size:12px;color:#475569;margin-bottom:10px;line-height:1.65">{intro}</div>'
        html += _ns(narrative, "What's attractive:", "✅", "#F0FDF4", "#86EFAC", "#15803D")
        html += _ns(narrative, "Watch-outs:", "⚠️", "#FFFBEB", "#FCD34D", "#B45309")
        if "Bottom line:" in narrative:
            bl = narrative.split("Bottom line:", 1)[1].strip()
            html += (f'<div class="nar-bottom">'
                     f'<div class="nar-bottom-label">⚖️ Bottom Line</div>'
                     f'<div class="nar-bottom-text">{bl}</div></div>')
        st.markdown(html, unsafe_allow_html=True)

    # Scoring signals
    reasons = row.get("reasons", "")
    if reasons and str(reasons) != "nan":
        st.markdown('<div class="dp-section">Scoring Signals</div>', unsafe_allow_html=True)
        st.info(str(reasons))

    # Description
    desc = row.get("description", "")
    if desc and str(desc) != "nan":
        with st.expander("📄 Full Listing Description"):
            st.markdown(f'<div style="font-size:13px;line-height:1.65;color:#334155">{desc}</div>',
                        unsafe_allow_html=True)


# ── Deal list renderer ─────────────────────────────────────────────────────────
def render_deal_list(rows):
    watchlist   = st.session_state.watchlist
    selected_id = st.session_state.selected_id

    for _, row in rows.iterrows():
        lid      = str(row.get("id", ""))
        bucket   = str(row.get("bucket", "SKIP"))
        score    = int(row.get("score", 0))
        title    = row.get("title", "Untitled")
        location = row.get("location", "") or ""
        industry = row.get("industry", "") or ""
        asking   = row.get("asking_price")
        cf       = row.get("annual_cash_flow")
        coc      = row.get("coc_return_20pct")
        absentee = row.get("absentee", "No")
        is_saved = lid in watchlist
        is_sel   = str(selected_id) == lid

        sc          = _score_color(score)
        bclass      = _bucket_cls(bucket)
        sel_class   = "selected" if is_sel else ""
        cat_name, cat_cfg = _primary_category(row)

        meta_parts = []
        if location and location != "nan": meta_parts.append(f"📍 {location}")
        if industry and industry != "nan": meta_parts.append(f"· {industry}")
        meta_str = "  ".join(meta_parts)

        coc_str = f"CoC {_fmt(coc, '%')}" if coc and not (isinstance(coc, float) and pd.isna(coc)) else ""
        coc_html  = f'<span style="font-size:10px;color:#64748B">{coc_str}</span>' if coc_str else ""
        star_html = '<span style="font-size:10px;color:#4F46E5;font-weight:700">⭐</span>' if is_saved else ""

        html = (
            f'<div class="deal-row {sel_class}">'
            f'<div class="dr-top">'
            f'<div class="dr-title">{cat_cfg["emoji"]} {title}</div>'
            f'<div class="dr-price">{_fmt(asking, "$M")}</div>'
            f'</div>'
            f'<div class="dr-meta">{meta_str}</div>'
            f'<div class="dr-bottom">'
            f'<span class="bucket-badge {bclass}">{bucket}</span>'
            f'<span class="score-chip">'
            f'<span class="score-dot" style="background:{sc};opacity:{max(0.3, score/100):.2f}"></span>'
            f'{score}</span>'
            f'{coc_html}'
            f'{star_html}'
            f'</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)

        btn_a, btn_b = st.columns([4, 1])
        with btn_a:
            btn_label = "📂 Selected" if is_sel else "View Deal →"
            btn_type  = "primary" if is_sel else "secondary"
            if st.button(btn_label, key=f"view_{lid}", use_container_width=True, type=btn_type):
                st.session_state.selected_id = None if is_sel else lid
                st.rerun()
        with btn_b:
            star_label = "⭐" if is_saved else "☆"
            if st.button(star_label, key=f"wl_{lid}", use_container_width=True):
                new_wl = set(st.session_state.watchlist)
                if is_saved: new_wl.discard(lid)
                else:        new_wl.add(lid)
                st.session_state.watchlist = new_wl
                st.rerun()


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


# ── Main layout ────────────────────────────────────────────────────────────────
view_mode = st.radio("View", ["List", "Table"], horizontal=True, label_visibility="collapsed")

if len(filtered) == 0:
    st.info("No listings match the current filters.")
    st.stop()

selected_id  = st.session_state.selected_id
selected_row = None
if selected_id is not None:
    match = filtered[filtered["id"].astype(str) == str(selected_id)]
    if len(match) > 0:
        selected_row = match.iloc[0]

# Always show split layout — detail panel shows empty state when nothing selected
list_col, detail_col = st.columns([5, 4], gap="large")

with list_col:
    count_label = f"{len(filtered)} listing{'s' if len(filtered) != 1 else ''}"
    st.caption(count_label)

    if view_mode == "List":
        render_deal_list(filtered)
    else:
        render_table(filtered)

with detail_col:
    if selected_row is not None:
        with st.container(border=True):
            render_detail_panel(selected_row)
    else:
        st.markdown("""
<div style="display:flex;flex-direction:column;align-items:center;justify-content:center;
            height:300px;color:#94A3B8;text-align:center;padding:40px">
  <div style="font-size:40px;margin-bottom:12px">👈</div>
  <div style="font-size:15px;font-weight:700;color:#475569;margin-bottom:6px">Select a deal to view details</div>
  <div style="font-size:13px">Click "View Deal" on any listing to open the full deal sheet here</div>
</div>
""", unsafe_allow_html=True)

        # Pipeline analytics in empty state
        with st.expander("📈 Pipeline Analytics"):
            chart_df = filtered[filtered["asking_price"].notna() & filtered["annual_cash_flow"].notna()].copy()
            chart_df["bucket_display"] = chart_df["bucket"].fillna("SKIP")
            if len(chart_df) > 0:
                color_map = {"SHORTLIST": "#10B981", "REVIEW": "#F59E0B", "AUTO-REJECT": "#EF4444", "SKIP": "#94A3B8"}
                fig = px.scatter(chart_df, x="asking_price", y="annual_cash_flow",
                    color="bucket_display", color_discrete_map=color_map,
                    hover_data={"title": True, "location": True, "score": True, "bucket_display": False},
                    labels={"asking_price": "Asking Price ($)", "annual_cash_flow": "Cash Flow ($)", "bucket_display": "Bucket"},
                    title="Price vs. Cash Flow")
                fig.update_traces(marker=dict(size=8, opacity=0.8))
                fig.update_layout(
                    plot_bgcolor="white", paper_bgcolor="white",
                    font=dict(family="Inter", size=12),
                    margin=dict(l=40, r=20, t=40, b=40),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    height=300,
                )
                fig.update_xaxes(tickprefix="$", tickformat=",.0f", gridcolor="#F1F5F9")
                fig.update_yaxes(tickprefix="$", tickformat=",.0f", gridcolor="#F1F5F9")
                st.plotly_chart(fig, use_container_width=True)
