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

BUCKET_BORDER = {
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

.stApp { background: #D1D9E6; }

/* ── Slim header ── */
.scout-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: linear-gradient(135deg, #1E3A5F 0%, #2563EB 100%);
    border-radius: 12px;
    padding: 18px 28px;
    margin-bottom: 20px;
}
.scout-header-left h1 {
    margin: 0 0 2px;
    font-size: 22px;
    font-weight: 800;
    color: white;
    letter-spacing: -0.5px;
}
.scout-header-left p { margin: 0; font-size: 12px; opacity: 0.7; color: white; }

/* ── Stat pills ── */
.stat-bar { display: flex; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.stat-pill {
    background: white;
    border-radius: 10px;
    padding: 12px 18px;
    min-width: 110px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    border: 1px solid #E2E8F0;
}
.stat-pill .label { font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.6px; }
.stat-pill .value { font-size: 24px; font-weight: 800; color: #0F172A; line-height: 1.2; }
.stat-pill .value.green  { color: #10B981; }
.stat-pill .value.red    { color: #EF4444; }
.stat-pill .value.blue   { color: #2563EB; }
.stat-pill .value.amber  { color: #F59E0B; }

/* ── Quick filter buttons ── */
.preset-row { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
.preset-btn {
    background: white;
    border: 1.5px solid #E2E8F0;
    border-radius: 20px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 600;
    color: #475569;
    cursor: pointer;
    transition: all 0.15s;
}
.preset-btn.active {
    background: #2563EB;
    border-color: #2563EB;
    color: white;
}

/* ── Cards ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06) !important;
    background: #FFFFFF !important;
    transition: box-shadow 0.2s, transform 0.15s;
    margin-bottom: 4px;
}
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stVerticalBlock"] {
    background: #FFFFFF !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 6px 20px rgba(37,99,235,0.12) !important;
    transform: translateY(-2px);
}
.biz-card { padding: 2px 0 6px; min-height: 340px; display: flex; flex-direction: column; }
.card-metrics { margin-top: auto; }
.card-border-bar {
    height: 4px;
    border-radius: 4px 4px 0 0;
    margin: -2px -2px 10px -2px;
}
.card-header { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.card-title { font-size: 17px; font-weight: 700; color: #0F172A; line-height: 1.35; margin: 4px 0; }
.card-meta { font-size: 12px; color: #64748B; margin-bottom: 10px; display: flex; gap: 10px; }
.card-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 8px; }
.card-metric { background: #F8FAFC; border-radius: 8px; padding: 9px 11px; }
.card-metric .cm-label { font-size: 10px; font-weight: 700; color: #94A3B8; text-transform: uppercase; letter-spacing: 0.5px; }
.card-metric .cm-value { font-size: 18px; font-weight: 700; color: #0F172A; }

/* ── Score bar ── */
.score-bar-wrap { margin: 6px 0 10px; }
.score-bar-label { display: flex; justify-content: space-between; font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 3px; }
.score-bar-bg { background: #F1F5F9; border-radius: 4px; height: 5px; overflow: hidden; }
.score-bar-fill { height: 5px; border-radius: 4px; transition: width 0.3s; }

/* ── Tags ── */
.card-tags { display: flex; gap: 5px; flex-wrap: wrap; margin-top: 6px; margin-bottom: 8px; }
.tag { font-size: 10px; font-weight: 600; padding: 2px 7px; border-radius: 20px; }
.tag-absentee { background: #EEF2FF; color: #4F46E5; }

/* ── Badges ── */
.badge { display: inline-block; font-size: 9px; font-weight: 800; padding: 2px 8px; border-radius: 20px; letter-spacing: 0.4px; text-transform: uppercase; }
.badge-shortlist  { background: #D1FAE5; color: #065F46; }
.badge-review     { background: #FEF3C7; color: #92400E; }
.badge-reject     { background: #FEE2E2; color: #991B1B; }
.badge-skip       { background: #F1F5F9; color: #475569; }

/* ── Detail panel ── */
.detail-panel {
    background: white;
    border-radius: 14px;
    border: 1px solid #E2E8F0;
    padding: 24px;
    box-shadow: 0 4px 24px rgba(0,0,0,0.08);
    position: sticky;
    top: 20px;
    max-height: 90vh;
    overflow-y: auto;
}
.ds-title { font-size: 20px; font-weight: 800; color: #0F172A; margin-bottom: 2px; line-height: 1.3; }
.ds-link  { font-size: 12px; color: #2563EB; text-decoration: none; }
.ds-section {
    font-size: 10px;
    font-weight: 800;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin: 18px 0 8px;
    border-top: 1px solid #F1F5F9;
    padding-top: 14px;
}
.sba-block { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 10px; padding: 14px; }
.sba-block h4 { margin: 0 0 10px; font-size: 13px; font-weight: 700; color: #1E3A5F; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: #1E293B !important; border-right: none; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span:not([data-baseweb]),
[data-testid="stSidebar"] div[class*="stMarkdown"] { color: #CBD5E1 !important; }
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 { color: #F1F5F9 !important; font-size: 13px; text-transform: uppercase; letter-spacing: 0.6px; }
[data-testid="stSidebar"] label { color: #94A3B8 !important; font-size: 13px !important; }
[data-testid="stSidebar"] .stRadio label { color: #CBD5E1 !important; font-size: 14px !important; }
[data-testid="stSidebar"] hr { border-color: #334155 !important; }

/* ── Sidebar expander ── */
[data-testid="stSidebar"] [data-testid="stExpander"] { background: #1E293B !important; border: 1px solid #334155 !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] p,
[data-testid="stSidebar"] [data-testid="stExpander"] li,
[data-testid="stSidebar"] [data-testid="stExpander"] span,
[data-testid="stSidebar"] [data-testid="stExpander"] strong,
[data-testid="stSidebar"] [data-testid="stExpander"] div { color: #F1F5F9 !important; }
[data-testid="stSidebar"] [data-testid="stExpander"] summary { color: #F1F5F9 !important; }

/* ── Buttons ── */
.stButton > button {
    border-radius: 8px;
    font-size: 12px;
    font-weight: 700;
    padding: 6px 0;
    transition: all 0.15s;
}
[data-testid="stBaseButton-primary"] {
    background: #2563EB !important;
    color: white !important;
    border: none !important;
}
[data-testid="stBaseButton-primary"]:hover {
    background: #1D4ED8 !important;
    color: white !important;
}
[data-testid="stBaseButton-secondary"] {
    background: white !important;
    color: #475569 !important;
    border: 1.5px solid #CBD5E1 !important;
}
[data-testid="stBaseButton-secondary"]:hover {
    background: #F1F5F9 !important;
    color: #0F172A !important;
    border-color: #94A3B8 !important;
}

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 10px 12px !important;
}
[data-testid="metric-container"] label { font-size: 10px !important; color: #64748B !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.4px; }
[data-testid="stMetricValue"] { font-size: 16px !important; font-weight: 800 !important; color: #0F172A !important; }

/* ── Expanders ── */
[data-testid="stExpander"] { background: white; border: 1px solid #E2E8F0 !important; border-radius: 10px !important; margin-bottom: 10px; }

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab"] { font-size: 13px; font-weight: 600; }

/* ── Divider ── */
hr { border-color: #E2E8F0 !important; margin: 14px 0 !important; }
</style>
<script>
(function() {
    function fixCardBg() {
        document.querySelectorAll('[data-testid="stVerticalBlockBorderWrapper"]').forEach(function(el) {
            el.style.setProperty('background-color', '#FFFFFF', 'important');
            el.querySelectorAll('[data-testid="stVerticalBlock"], [class*="block-container"]').forEach(function(inner) {
                inner.style.setProperty('background-color', '#FFFFFF', 'important');
            });
        });
    }
    new MutationObserver(fixCardBg).observe(document.documentElement, {childList: true, subtree: true});
    fixCardBg();
})();
</script>
""", unsafe_allow_html=True)


# ── Data loading (cached) ──────────────────────────────────────────────────────
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

    # Category detection
    def _detect(row, keywords):
        ctx = f"{row.get('title', '')} {row.get('industry', '')} {row.get('description', '')}".lower()
        return any(kw in ctx for kw in keywords)

    for cfg in CATEGORY_CONFIG.values():
        df[cfg["col"]] = df.apply(lambda r, k=cfg["keywords"]: _detect(r, k), axis=1)

    # Derived metrics
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
    if fmt == "$M": return f"${val/1e6:.2f}M"
    if fmt == "%":  return f"{val*100:.0f}%"
    if fmt == "x":  return f"{val:.2f}x"
    return str(val)

def _val_color(val, good, ok):
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "#94A3B8"
    return "#10B981" if val >= good else ("#F59E0B" if val >= ok else "#EF4444")

def _score_color(score):
    if score >= 65: return "#10B981"
    if score >= 35: return "#F59E0B"
    return "#94A3B8"

def _badge_cls(bucket):
    return {"SHORTLIST": "badge-shortlist", "REVIEW": "badge-review", "AUTO-REJECT": "badge-reject"}.get(bucket, "badge-skip")

def _row_categories(row):
    return [(name, cfg) for name, cfg in CATEGORY_CONFIG.items() if row.get(cfg["col"])]

def _primary_category(row):
    cats = _row_categories(row)
    if cats:
        return cats[0]
    return ("Other", {"emoji": "🏢", "col": None, "color": "#475569", "bg": "#F1F5F9"})


# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.markdown("### Filters")

st.sidebar.markdown("#### Scoring")
apply_scoring = st.sidebar.checkbox(
    "Apply scoring filters", value=False,
    help="When off, all listings are shown regardless of score or bucket.",
)
if apply_scoring:
    all_buckets = sorted(df["bucket"].dropna().unique().tolist())
    buckets = st.sidebar.multiselect(
        "Bucket", options=all_buckets,
        default=[b for b in ["SHORTLIST", "REVIEW"] if b in all_buckets],
    )
    min_score = st.sidebar.slider("Min Score", 0, 100, 35)
else:
    buckets = None
    min_score = 0

st.sidebar.markdown("---")
st.sidebar.markdown("#### Financial")
max_price = st.sidebar.number_input("Max Asking Price ($)", value=5000000, step=100000)
min_price = st.sidebar.number_input("Min Asking Price ($)", value=50000,   step=50000)
min_cf    = st.sidebar.number_input("Min Cash Flow ($)",    value=0,       step=25000)
min_coc   = st.sidebar.slider("Min CoC Return (20% down)", 0, 200, 0, format="%d%%")
min_coc_decimal = min_coc / 100.0

st.sidebar.markdown("---")
st.sidebar.markdown("#### Location & Operator")
twin_cities_only = st.sidebar.checkbox("Twin Cities Only")
absentee_only    = st.sidebar.checkbox("Absentee / Semi-Absentee Only")

st.sidebar.markdown("---")
with st.sidebar.expander("📊 How scores work"):
    st.markdown("""
**Buckets:**
- 🟢 **SHORTLIST** — 65+
- 🟡 **REVIEW** — 35–64
- ⚪ **SKIP** — below 35
- 🔴 **AUTO-REJECT** — 0 (failed screening)

---

**Auto-Reject triggers:**
- Price outside $50K–$5M
- No cash flow data
- DSCR < 1.25 at 20% down
- Negative CF after SBA debt
- Not Minnesota
- Regulated: franchise resale, cannabis, firearms, gambling, pawn, payday loan
- Digital-only: SaaS, Amazon FBA, dropshipping, affiliate

---

**Scoring (100 pts):**

💰 **Financial** — 40 pts
CF $75K+, DSCR ≥1.25, CoC ≥15%

⚙️ **Operations** — 15 pts
<20 employees, no heavy inventory, turnkey

💻 **Tech gap** — 15 pts
No CRM, manual billing, no website

🔁 **Recurring revenue** — 10 pts
Service contracts, routes, retainers

🏗️ **Industry durability** — 10 pts
HVAC, plumbing, healthcare, accounting, trucking

📍 **Geography** — 10 pts
Twin Cities = 10 pts · Outstate MN = 5 pts
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


# ── Header ─────────────────────────────────────────────────────────────────────
n_total     = len(df)
n_filtered  = len(base_filtered)
n_shortlist = len(df[df["bucket"] == "SHORTLIST"])
n_review    = len(df[df["bucket"] == "REVIEW"])
n_rejected  = len(df[df["bucket"] == "AUTO-REJECT"])
n_watchlist = len(st.session_state.watchlist)

st.markdown(f"""
<div class="scout-header">
  <div class="scout-header-left">
    <h1>🏢 Sunbelt Scout</h1>
    <p>Minnesota business acquisition pipeline · Scored &amp; filtered daily</p>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="stat-bar">
  <div class="stat-pill"><div class="label">Total</div><div class="value blue">{n_total}</div></div>
  <div class="stat-pill"><div class="label">Showing</div><div class="value">{n_filtered}</div></div>
  <div class="stat-pill"><div class="label">Shortlisted</div><div class="value green">{n_shortlist}</div></div>
  <div class="stat-pill"><div class="label">Review</div><div class="value amber">{n_review}</div></div>
  <div class="stat-pill"><div class="label">Auto-Rejected</div><div class="value red">{n_rejected}</div></div>
  <div class="stat-pill"><div class="label">Saved</div><div class="value">{n_watchlist} ⭐</div></div>
</div>
""", unsafe_allow_html=True)


# ── Search ─────────────────────────────────────────────────────────────────────
search_query = st.text_input(
    "", placeholder="🔍  Search by business name, industry, or location...",
    label_visibility="collapsed",
)

# ── Quick filter presets ───────────────────────────────────────────────────────
preset_col1, preset_col2, preset_col3, preset_col4, preset_col5, preset_col6 = st.columns(6)
active = st.session_state.active_preset

def _preset_btn(col, label, key):
    with col:
        is_active = active == key
        btn_type = "primary" if is_active else "secondary"
        if st.button(label, key=f"preset_{key}", type=btn_type, use_container_width=True):
            st.session_state.active_preset = None if is_active else key
            st.rerun()

_preset_btn(preset_col1, "🏆 Best Returns",   "best_returns")
_preset_btn(preset_col2, "📍 Twin Cities",    "twin_cities")
_preset_btn(preset_col3, "💰 Under $500K",    "under_500k")
_preset_btn(preset_col4, "🏠 Absentee",       "absentee")
_preset_btn(preset_col5, "⭐ My Watchlist",   "watchlist")
_preset_btn(preset_col6, "🔴 Auto-Rejected",  "rejected")

# ── Category pills ─────────────────────────────────────────────────────────────
selected_categories = st.multiselect(
    "", options=list(CATEGORY_CONFIG.keys()),
    placeholder="Filter by category  (leave empty for all)",
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

# Clear selected listing if it's no longer in filtered set
if st.session_state.selected_id is not None:
    if not any(filtered["id"].astype(str) == str(st.session_state.selected_id)):
        st.session_state.selected_id = None


# ── View mode ──────────────────────────────────────────────────────────────────
view_mode = st.sidebar.radio("View Mode", ["Cards", "Table"], horizontal=True)


# ── Pipeline Analytics ─────────────────────────────────────────────────────────
with st.expander("📈 Pipeline Analytics"):
    chart_df = filtered[filtered["asking_price"].notna() & filtered["annual_cash_flow"].notna()].copy()
    chart_df["bucket_display"] = chart_df["bucket"].fillna("SKIP")

    if len(chart_df) > 0:
        col_scatter, col_hist = st.columns(2)

        with col_scatter:
            color_map = {"SHORTLIST": "#10B981", "REVIEW": "#F59E0B", "AUTO-REJECT": "#EF4444", "SKIP": "#94A3B8"}
            fig_scatter = px.scatter(
                chart_df,
                x="asking_price", y="annual_cash_flow",
                color="bucket_display",
                color_discrete_map=color_map,
                hover_data={"title": True, "location": True, "score": True, "bucket_display": False},
                labels={"asking_price": "Asking Price ($)", "annual_cash_flow": "Annual Cash Flow ($)", "bucket_display": "Bucket"},
                title="Price vs. Cash Flow",
                size_max=12,
            )
            fig_scatter.update_traces(marker=dict(size=8, opacity=0.8))
            fig_scatter.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Inter", size=12),
                margin=dict(l=40, r=20, t=40, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=320,
            )
            fig_scatter.update_xaxes(tickprefix="$", tickformat=",.0f", gridcolor="#F1F5F9")
            fig_scatter.update_yaxes(tickprefix="$", tickformat=",.0f", gridcolor="#F1F5F9")
            st.plotly_chart(fig_scatter, use_container_width=True)

        with col_hist:
            score_bins = list(range(0, 110, 10))
            chart_df["score_bin"] = pd.cut(chart_df["score"], bins=score_bins, right=False, labels=[f"{i}–{i+9}" for i in range(0, 100, 10)])
            hist_data = chart_df.groupby(["score_bin", "bucket_display"], observed=True).size().reset_index(name="count")
            fig_hist = px.bar(
                hist_data,
                x="score_bin", y="count",
                color="bucket_display",
                color_discrete_map=color_map,
                labels={"score_bin": "Score Range", "count": "# Listings", "bucket_display": "Bucket"},
                title="Score Distribution",
            )
            fig_hist.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="Inter", size=12),
                margin=dict(l=40, r=20, t=40, b=40),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=320,
                barmode="stack",
            )
            fig_hist.update_xaxes(gridcolor="#F1F5F9")
            fig_hist.update_yaxes(gridcolor="#F1F5F9")
            st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.info("Not enough data to render charts for current filters.")


# ── Detail panel renderer ──────────────────────────────────────────────────────
def render_detail_panel(row):
    title    = row.get("title", "Untitled")
    url      = row.get("url", "")
    bucket   = str(row.get("bucket", ""))
    score    = int(row.get("score", 0))
    asking   = row.get("asking_price")
    cf       = row.get("annual_cash_flow")
    rev      = row.get("annual_revenue")
    emps     = row.get("employees")
    absentee = row.get("absentee", "No")

    # Close button
    if st.button("✕ Close", key="close_panel"):
        st.session_state.selected_id = None
        st.rerun()

    url_html = f'<a class="ds-link" href="{url}" target="_blank">View on Sunbelt →</a>' if url and str(url) != "nan" else ""
    st.markdown(f"""
        <div class="ds-title">{title}</div>
        <div style="display:flex;align-items:center;gap:10px;margin:6px 0 12px;">
            <span class="badge {_badge_cls(bucket)}">{bucket}</span>
            <span style="font-size:12px;color:#475569;font-weight:700;">Score {score}/100</span>
            {url_html}
        </div>
    """, unsafe_allow_html=True)

    # Score bar
    sc = _score_color(score)
    st.markdown(f"""
        <div class="score-bar-wrap">
            <div class="score-bar-bg"><div class="score-bar-fill" style="width:{score}%;background:{sc}"></div></div>
        </div>
    """, unsafe_allow_html=True)

    # Top KPIs
    k1, k2, k3 = st.columns(3)
    k1.metric("Asking Price",    _fmt(asking), help="Total asking price")
    k2.metric("Cash Flow (SDE)", _fmt(cf),     help="Seller's Discretionary Earnings")
    k3.metric("Annual Revenue",  _fmt(rev),    help="Gross annual revenue")

    k4, k5, k6 = st.columns(3)
    k4.metric("Employees",   int(emps) if pd.notna(emps) else "—")
    k5.metric("Absentee",    absentee)
    k6.metric("Location",    row.get("location", "—") or "—")

    # Category insights
    cats = _row_categories(row)
    rev_multiple  = row.get("revenue_multiple")
    sde_margin    = row.get("sde_margin")
    rev_per_emp   = row.get("revenue_per_employee")

    st.markdown('<div class="ds-section">Deal Metrics</div>', unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Revenue Multiple", f"{rev_multiple:.2f}x" if rev_multiple else "—",
              help="Asking price ÷ revenue. Service: 0.5–1.5x typical.")
    m2.metric("SDE Margin",  f"{sde_margin*100:.0f}%" if sde_margin else "—",
              help="Cash flow ÷ revenue. 20%+ is healthy.")
    m3.metric("Rev / Employee", _fmt(rev_per_emp) if rev_per_emp else "—",
              help="Revenue per employee. $150K+ is strong.")

    # Category notes
    cat_notes = {
        "Restaurant & Bar":      "🍽️ Thin margins (10–20% SDE normal). Verify lease terms and equipment.",
        "Retail":                "🛍️ Confirm inventory included in price. Rev multiples 0.3–0.8x typical.",
        "Manufacturing":         "🏭 Equipment (FF&E) drives value. Check machinery age and customer concentration.",
        "Automotive":            "🚗 Count service bays. Technician tenure is the key constraint.",
        "Distribution":          "🚚 Verify fleet condition. Route density and contract lengths determine defensibility.",
        "Financial Services":    "💼 Client retention rate is critical. CPA/bookkeeping multiples: 1–2x revenue.",
        "Hospitality":           "🏨 Check occupancy rate and RevPAR. Verify any franchise agreement terms.",
        "Technology / IT":       "💻 MSP recurring MRR is key. Expect SDE margins of 30–50%.",
        "Education & Childcare": "🎓 Licensing and capacity utilization matter. Track enrollment trends.",
        "Healthcare":            "🩺 Verify payer mix and reimbursement rates. Check licensing transfer requirements.",
        "Trades":                "🔧 Technician headcount and tenure are key. Service contracts add defensibility.",
        "Construction":          "🏗️ Backlog size and contract types (fixed vs T&M) drive risk profile.",
        "Beauty & Wellness":     "💇 Chair/suite rental vs. employee model affects transferability.",
    }
    for cat_name, _ in cats:
        if cat_name in cat_notes:
            st.info(cat_notes[cat_name])

    # SBA tabs
    st.markdown('<div class="ds-section">SBA Financing</div>', unsafe_allow_html=True)
    tab_10, tab_20, tab_sf = st.tabs(["10% Down", "20% Down", "Seller Financed (0% Down)"])

    def _sba_tab(down_key, monthly_key, cf_key, coc_key, dscr_key):
        down    = row.get(down_key)
        monthly = row.get(monthly_key)
        cf_aft  = row.get(cf_key)
        coc     = row.get(coc_key)
        dscr    = row.get(dscr_key)
        c1, c2 = st.columns(2)
        c1.metric("Down Payment",    _fmt(down),   help="Cash required at close")
        c2.metric("Monthly Payment", _fmt(monthly), help="SBA loan payment (10% rate, 10yr)")
        c3, c4, c5 = st.columns(3)
        c3.metric("CF After Debt",   _fmt(cf_aft), help="Annual CF after SBA payments")
        c4.metric("CoC Return",      _fmt(coc, "%"), help="CF after debt ÷ down. 30%+ strong.")
        c5.metric("DSCR",            _fmt(dscr, "x"), help="≥1.25 required for SBA. 1.5+ comfortable.")

    with tab_10:
        _sba_tab("down_10", "sba_monthly_10pct", "cf_after_debt_10pct", "coc_return_10pct", "dscr_10pct")
    with tab_20:
        _sba_tab("down_20", "sba_monthly_20pct", "cf_after_debt_20pct", "coc_return_20pct", "dscr_20pct")
    with tab_sf:
        sf_note    = row.get("seller_note_amount")
        sf_monthly = row.get("seller_note_monthly")
        sf_standby = row.get("cf_during_standby")
        sf_after   = row.get("cf_after_seller_financing")
        sf_dscr    = row.get("dscr_seller_financed")

        s1, s2, s3 = st.columns(3)
        s1.metric("Your Cash Down", "$0",        help="Seller carries 10% as subordinated note")
        s2.metric("Seller Note",    _fmt(sf_note), help="6% / 5-year seller note")
        s3.metric("Note Payment",   (_fmt(sf_monthly) + "/mo") if sf_monthly else "—", help="Kicks in after 24-month standby")
        s4, s5, s6 = st.columns(3)
        s4.metric("CF Yr 1–2",  _fmt(sf_standby), help="CF after SBA only (seller note on standby)")
        s5.metric("CF Yr 3+",   _fmt(sf_after),   help="CF after SBA + seller note")
        s6.metric("DSCR Yr 3+", _fmt(sf_dscr, "x") if sf_dscr else "—", help="≥1.25 required for SBA")
        st.caption("⚠️ SBA requires seller note on full standby for 24 months. Seller must agree.")

    # Business details
    st.markdown('<div class="ds-section">Business Details</div>', unsafe_allow_html=True)
    d1, d2, d3 = st.columns(3)
    d1.metric("Industry",       row.get("industry", "—") or "—")
    d2.metric("Years Operating",row.get("years_in_business", "—") or "—")
    d3.metric("Franchise?",     row.get("is_franchise", "—") or "—")
    d4, d5 = st.columns(2)
    d4.metric("SBA Pre-Approved?", row.get("sba_available", "—") or "—")
    d5.metric("Real Estate",       row.get("real_estate", "—") or "—")

    reason = row.get("reason_for_selling", "") or ""
    if reason and str(reason) != "nan":
        st.markdown(f'<div style="font-size:12px;color:#475569;margin-top:6px;"><b>Reason for selling:</b> {reason}</div>', unsafe_allow_html=True)

    # Tags
    tags = []
    if absentee in ("Likely", "Possible"):
        tags.append('<span class="tag tag-absentee">🏠 Absentee</span>')
    for cat_name, cfg in cats:
        tags.append(f'<span class="tag" style="background:{cfg["bg"]};color:{cfg["color"]}">{cfg["emoji"]} {cat_name}</span>')
    if tags:
        st.markdown(f'<div class="card-tags">{"".join(tags)}</div>', unsafe_allow_html=True)

    # Narrative
    narrative = row.get("narrative", "")
    if narrative and str(narrative) != "nan":
        st.markdown('<div class="ds-section">Deal Summary</div>', unsafe_allow_html=True)

        def _ns(text, prefix, icon, bg, border, lc):
            if prefix not in text: return ""
            body = text.split(prefix, 1)[1]
            for stop in ["What's attractive:", "Watch-outs:", "Bottom line:"]:
                if stop != prefix and stop in body:
                    body = body.split(stop)[0]
            items = [s.strip().rstrip(".") for s in body.strip().split(";") if s.strip()]
            bullets = "".join(f'<li style="margin-bottom:3px">{i}.</li>' for i in items)
            return f'<div style="background:{bg};border:1px solid {border};border-radius:8px;padding:12px 16px;margin-bottom:8px"><div style="font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:0.6px;color:{lc};margin-bottom:6px">{icon} {prefix.rstrip(":")}</div><ul style="margin:0;padding-left:16px;font-size:12px;line-height:1.7;color:#1E293B">{bullets}</ul></div>'

        intro = narrative.split("What's attractive:")[0].strip() if "What's attractive:" in narrative else ""
        html = ""
        if intro:
            html += f'<div style="font-size:12px;color:#475569;margin-bottom:8px;line-height:1.6">{intro}</div>'
        html += _ns(narrative, "What's attractive:", "✅", "#F0FDF4", "#86EFAC", "#15803D")
        html += _ns(narrative, "Watch-outs:", "⚠️", "#FFFBEB", "#FCD34D", "#B45309")
        if "Bottom line:" in narrative:
            bl = narrative.split("Bottom line:", 1)[1].strip()
            html += f'<div style="background:#1E3A5F;border-radius:8px;padding:12px 16px;margin-bottom:8px"><div style="font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:0.6px;color:#93C5FD;margin-bottom:4px">⚖️ Bottom Line</div><div style="font-size:13px;font-weight:600;color:white;line-height:1.5">{bl}</div></div>'
        st.markdown(html, unsafe_allow_html=True)

    # Scoring signals
    reasons = row.get("reasons", "")
    if reasons and str(reasons) != "nan":
        st.markdown('<div class="ds-section">Scoring Signals</div>', unsafe_allow_html=True)
        st.info(str(reasons))

    # Description
    desc = row.get("description", "")
    if desc and str(desc) != "nan":
        with st.expander("📄 Full Listing Description"):
            st.markdown(f'<div style="font-size:13px;line-height:1.65;color:#334155">{desc}</div>', unsafe_allow_html=True)


# ── Card renderer ──────────────────────────────────────────────────────────────
def render_cards(rows, ncols=3):
    watchlist = st.session_state.watchlist
    cols = st.columns(ncols)
    for i, (_, row) in enumerate(rows.iterrows()):
        bucket   = str(row.get("bucket", "SKIP"))
        score    = int(row.get("score", 0))
        title    = row.get("title", "Untitled")
        location = row.get("location", "")
        industry = row.get("industry", "")
        asking   = row.get("asking_price")
        cf       = row.get("annual_cash_flow")
        coc      = row.get("coc_return_20pct")
        dscr     = row.get("dscr_20pct")
        absentee = row.get("absentee", "No")
        lid      = str(row.get("id", i))

        border_color = BUCKET_BORDER.get(bucket, "#94A3B8")
        score_bar_color = _score_color(score)
        badge_cls = _badge_cls(bucket)
        cat_name, cat_cfg = _primary_category(row)
        cat_emoji = cat_cfg["emoji"]

        dscr_color = _val_color(dscr, 1.5, 1.25)
        coc_color  = _val_color(coc, 0.30, 0.15)

        meta_parts = []
        if location and str(location) != "nan": meta_parts.append(f"📍 {location}")
        if industry and str(industry) != "nan": meta_parts.append(f"🏷 {industry}")
        meta_html = f'<div class="card-meta">' + " &nbsp;·&nbsp; ".join(meta_parts) + '</div>' if meta_parts else ""

        tags_html = ""
        if absentee in ("Likely", "Possible"):
            tags_html += '<span class="tag tag-absentee">🏠 Absentee</span>'
        for c_name, c_cfg in _row_categories(row):
            tags_html += f'<span class="tag" style="background:{c_cfg["bg"]};color:{c_cfg["color"]}">{c_cfg["emoji"]} {c_name}</span>'

        is_saved = lid in watchlist

        saved_icon = '<span style="font-size:16px">⭐</span>' if is_saved else ""
        tags_block = f'<div class="card-tags">{tags_html}</div>' if tags_html else ""
        card_html = (
            f'<div class="biz-card">'
            f'<div class="card-border-bar" style="background:{border_color}"></div>'
            f'<div class="card-header">'
            f'<span class="badge {badge_cls}">{bucket}</span>'
            f'<span style="font-size:20px;margin-left:auto">{cat_emoji}</span>'
            f'{saved_icon}'
            f'</div>'
            f'<div class="card-title">{title}</div>'
            f'{meta_html}'
            f'<div class="score-bar-wrap">'
            f'<div class="score-bar-label"><span>Score</span><span>{score}/100</span></div>'
            f'<div class="score-bar-bg"><div class="score-bar-fill" style="width:{score}%;background:{score_bar_color}"></div></div>'
            f'</div>'
            f'<div class="card-metrics">'
            f'<div class="card-metric"><div class="cm-label">Price</div><div class="cm-value">{_fmt(asking, "$M")}</div></div>'
            f'<div class="card-metric"><div class="cm-label">Cash Flow</div><div class="cm-value">{_fmt(cf)}</div></div>'
            f'<div class="card-metric"><div class="cm-label">CoC (20%)</div><div class="cm-value" style="color:{coc_color}">{_fmt(coc, "%")}</div></div>'
            f'<div class="card-metric"><div class="cm-label">DSCR (20%)</div><div class="cm-value" style="color:{dscr_color}">{_fmt(dscr, "x")}</div></div>'
            f'</div>'
            f'{tags_block}'
            f'</div>'
        )

        with cols[i % ncols]:
            with st.container(border=True):
                st.markdown(card_html, unsafe_allow_html=True)

                btn_col, star_col = st.columns([4, 1])
                with btn_col:
                    if st.button("View Deal →", key=f"view_{lid}", use_container_width=True, type="primary"):
                        st.session_state.selected_id = lid
                        st.rerun()
                with star_col:
                    star_label = "⭐" if is_saved else "☆"
                    if st.button(star_label, key=f"wl_{lid}", use_container_width=True):
                        new_wl = set(st.session_state.watchlist)
                        if is_saved:
                            new_wl.discard(lid)
                        else:
                            new_wl.add(lid)
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
    available = [c for c in display_cols if c in rows.columns]
    display_df = rows[available].copy()
    for col in ["coc_return_20pct", "sde_margin"]:
        if col in display_df.columns:
            display_df[col] = display_df[col] * 100

    event = st.dataframe(
        display_df,
        column_config={
            "score":               st.column_config.NumberColumn("Score",          width="small"),
            "bucket":              st.column_config.TextColumn("Bucket",           width="small"),
            "title":               st.column_config.TextColumn("Business",         width="large"),
            "industry":            st.column_config.TextColumn("Industry",         width="medium"),
            "asking_price":        st.column_config.NumberColumn("Price ($)",       format="%.0f", width="small"),
            "annual_cash_flow":    st.column_config.NumberColumn("Cash Flow ($)",   format="%.0f", width="small"),
            "cf_after_debt_20pct": st.column_config.NumberColumn("CF After Debt ($)",format="%.0f",width="small"),
            "coc_return_20pct":    st.column_config.NumberColumn("CoC (%)",         format="%.0f", width="small"),
            "dscr_20pct":          st.column_config.NumberColumn("DSCR",            format="%.2f", width="small"),
            "revenue_multiple":    st.column_config.NumberColumn("Rev Multiple",    format="%.2f", width="small"),
            "sde_margin":          st.column_config.NumberColumn("SDE Margin (%)",  format="%.0f", width="small"),
            "absentee":            st.column_config.TextColumn("Absentee",          width="small"),
            "location":            st.column_config.TextColumn("Location",          width="small"),
            "url":                 st.column_config.LinkColumn("Link",              width="small"),
        },
        hide_index=True,
        height=680,
        use_container_width=True,
        selection_mode="single-row",
        on_select="rerun",
    )
    if event.selection.rows:
        selected_row = rows.iloc[event.selection.rows[0]]
        st.session_state.selected_id = str(selected_row.get("id", ""))
        st.rerun()


# ── Main layout ────────────────────────────────────────────────────────────────
if len(filtered) == 0:
    st.info("No listings match the current filters.")
else:
    selected_id  = st.session_state.selected_id
    selected_row = None
    if selected_id is not None:
        match = filtered[filtered["id"].astype(str) == str(selected_id)]
        if len(match) > 0:
            selected_row = match.iloc[0]

    if selected_row is not None:
        card_col, detail_col = st.columns([3, 2], gap="large")
        with card_col:
            if view_mode == "Cards":
                render_cards(filtered, ncols=1)
            else:
                render_table(filtered)
        with detail_col:
            with st.container(border=True):
                render_detail_panel(selected_row)
    else:
        if view_mode == "Cards":
            render_cards(filtered, ncols=2)
        else:
            render_table(filtered)

        # Analytics expander at bottom (only in full-width mode)
        with st.expander("💰 SBA Financing Comparison"):
            sba_cols = ["title", "asking_price", "down_10", "sba_monthly_10pct", "cf_after_debt_10pct",
                        "coc_return_10pct", "down_20", "sba_monthly_20pct", "cf_after_debt_20pct", "coc_return_20pct"]
            sba_available = [c for c in sba_cols if c in filtered.columns]
            sba_df = filtered[sba_available].head(20).copy()
            for col in ["coc_return_10pct", "coc_return_20pct"]:
                if col in sba_df.columns:
                    sba_df[col] = sba_df[col] * 100
            st.dataframe(
                sba_df,
                column_config={
                    "title":               st.column_config.TextColumn("Business",               width="large"),
                    "asking_price":        st.column_config.NumberColumn("Price ($)",             format="%.0f"),
                    "down_10":             st.column_config.NumberColumn("Down 10% ($)",          format="%.0f"),
                    "sba_monthly_10pct":   st.column_config.NumberColumn("Monthly 10% ($)",       format="%.0f"),
                    "cf_after_debt_10pct": st.column_config.NumberColumn("CF After Debt 10% ($)", format="%.0f"),
                    "coc_return_10pct":    st.column_config.NumberColumn("CoC 10% (%)",           format="%.0f"),
                    "down_20":             st.column_config.NumberColumn("Down 20% ($)",          format="%.0f"),
                    "sba_monthly_20pct":   st.column_config.NumberColumn("Monthly 20% ($)",       format="%.0f"),
                    "cf_after_debt_20pct": st.column_config.NumberColumn("CF After Debt 20% ($)", format="%.0f"),
                    "coc_return_20pct":    st.column_config.NumberColumn("CoC 20% (%)",           format="%.0f"),
                },
                hide_index=True,
                use_container_width=True,
            )
