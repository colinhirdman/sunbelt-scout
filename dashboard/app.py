import streamlit as st
import pandas as pd
from pathlib import Path

TRADES_KEYWORDS = [
    "plumb", "electrician", "electrical", "electric",
    "hvac", "heating", "cooling", "air condition",
    "roofing", "roofer",
    "general contractor", "contractor",
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
    "snow removal", "snow plowing", "snow plow", "snow management", "snow contracting",
    "grounds maintenance", "grounds care", "grounds keeping", "groundskeeping",
    "turf", "mowing", "mow",
    "irrigation", "sprinkler",
    "fertiliz", "weed control",
    "tree service", "tree trimming", "tree removal", "arborist",
    "leaf removal", "mulch",
]

HEALTHCARE_KEYWORDS = [
    "home health", "home care", "home healthcare",
    "senior care", "elder care", "assisted living", "memory care",
    "medical", "dental", "optometry", "optometrist", "ophthalmol",
    "veterinary", "veterinarian", "vet clinic", "animal hospital",
    "physical therapy", "occupational therapy", "speech therapy",
    "chiropractic", "chiropractor",
    "pharmacy", "pharmacist",
    "mental health", "behavioral health", "counseling practice",
    "nursing", "nurse staffing", "healthcare staffing",
    "urgent care", "clinic", "medical practice",
    "hospice", "palliative",
    "medical billing", "medical coding",
    "radiology", "laboratory", "lab service",
    "health care", "healthcare",
]

CSV_PATH = Path(__file__).resolve().parents[1] / "output" / "candidates.csv"

st.set_page_config(page_title="Sunbelt Scout", layout="wide", page_icon="🏢")

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Fonts & base ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Page background ── */
.stApp { background: #F1F5F9; }

/* ── Header banner ── */
.scout-header {
    background: linear-gradient(135deg, #1E3A5F 0%, #2563EB 100%);
    border-radius: 14px;
    padding: 28px 36px;
    margin-bottom: 24px;
    color: white;
}
.scout-header h1 {
    margin: 0 0 4px 0;
    font-size: 28px;
    font-weight: 700;
    color: white !important;
    letter-spacing: -0.5px;
}
.scout-header p {
    margin: 0;
    font-size: 14px;
    opacity: 0.75;
    color: white;
}

/* ── Summary stat pills ── */
.stat-bar {
    display: flex;
    gap: 14px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}
.stat-pill {
    background: white;
    border-radius: 10px;
    padding: 14px 22px;
    min-width: 130px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    border: 1px solid #E2E8F0;
}
.stat-pill .label {
    font-size: 11px;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.6px;
}
.stat-pill .value {
    font-size: 26px;
    font-weight: 700;
    color: #0F172A;
    line-height: 1.2;
}
.stat-pill .value.green  { color: #10B981; }
.stat-pill .value.red    { color: #EF4444; }
.stat-pill .value.blue   { color: #2563EB; }

/* ── Cards ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 12px !important;
    border: 1px solid #E2E8F0 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07) !important;
    background: white !important;
    transition: box-shadow 0.2s, transform 0.15s;
    margin-bottom: 4px;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    box-shadow: 0 6px 20px rgba(37,99,235,0.12) !important;
    transform: translateY(-2px);
}
.biz-card {
    padding: 4px 0 8px;
}
.biz-card .card-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
    width: 100%;
}
.biz-card .card-title {
    font-size: 15px;
    font-weight: 600;
    color: #0F172A;
    line-height: 1.3;
    margin: 4px 0 2px;
}
.biz-card .card-location {
    font-size: 12px;
    color: #64748B;
    margin-bottom: 12px;
}
.card-metrics {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 10px;
}
.card-metric {
    background: #F8FAFC;
    border-radius: 8px;
    padding: 8px 10px;
}
.card-metric .cm-label {
    font-size: 10px;
    font-weight: 600;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.card-metric .cm-value {
    font-size: 16px;
    font-weight: 700;
    color: #0F172A;
}
.card-tags {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-top: 8px;
    margin-bottom: 10px;
}
.tag {
    font-size: 11px;
    font-weight: 500;
    padding: 3px 8px;
    border-radius: 20px;
}
.tag-absentee  { background: #EEF2FF; color: #4F46E5; }
.tag-trades    { background: #FFF7ED; color: #C2410C; }
.tag-healthcare{ background: #F0FDF4; color: #15803D; }
.tag-lawn-snow { background: #F0FDF4; color: #166534; }

/* ── Bucket badges ── */
.badge {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    padding: 3px 9px;
    border-radius: 20px;
    letter-spacing: 0.4px;
    text-transform: uppercase;
}
.badge-shortlist  { background: #D1FAE5; color: #065F46; }
.badge-review     { background: #FEF3C7; color: #92400E; }
.badge-reject     { background: #FEE2E2; color: #991B1B; }

/* ── Score chip ── */
.score-chip {
    font-size: 12px;
    font-weight: 600;
    color: #475569;
    margin-left: 4px;
}

/* ── Tooltips ── */
div[data-testid="stTooltipContent"],
div[data-testid="stTooltipContent"] *,
[role="tooltip"],
[role="tooltip"] * {
    color: #0F172A !important;
    background: white !important;
}

/* ── Section headings with tooltip ── */
.section-heading {
    font-size: 13px;
    font-weight: 700;
    color: #475569;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    margin: 18px 0 10px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.tooltip-icon {
    cursor: help;
    color: #94A3B8;
    font-size: 13px;
    border-bottom: none;
}
[title] { cursor: help; }

/* ── Deal sheet ── */
.ds-title { font-size: 22px; font-weight: 700; color: #0F172A; margin-bottom: 2px; }
.ds-link  { font-size: 13px; color: #2563EB; text-decoration: none; }
.ds-section {
    font-size: 11px;
    font-weight: 700;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin: 20px 0 8px;
}
.sba-block {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 16px;
}
.sba-block h4 { margin: 0 0 12px; font-size: 14px; font-weight: 600; color: #1E3A5F; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #1E293B !important;
    border-right: none;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span:not([data-baseweb]),
[data-testid="stSidebar"] div[class*="stMarkdown"] { color: #CBD5E1 !important; }
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 { color: #F1F5F9 !important; font-size: 13px; text-transform: uppercase; letter-spacing: 0.6px; }
[data-testid="stSidebar"] label { color: #94A3B8 !important; font-size: 13px !important; }
[data-testid="stSidebar"] .stRadio label { color: #CBD5E1 !important; font-size: 14px !important; }
[data-testid="stSidebar"] hr { border-color: #334155 !important; }

/* ── View Deal button ── */
.stButton > button {
    background: #2563EB;
    color: white !important;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 600;
    padding: 6px 0;
    transition: background 0.15s;
}
.stButton > button:hover {
    background: #1D4ED8;
    color: white !important;
}

/* ── Streamlit metric overrides ── */
[data-testid="metric-container"] {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 12px 14px !important;
}
[data-testid="metric-container"] label { font-size: 11px !important; color: #64748B !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: 0.4px; }
[data-testid="stMetricValue"] { font-size: 18px !important; font-weight: 700 !important; color: #0F172A !important; }

/* ── Expanders ── */
[data-testid="stExpander"] {
    background: white;
    border: 1px solid #E2E8F0 !important;
    border-radius: 10px !important;
    margin-bottom: 10px;
}

/* ── Divider ── */
hr { border-color: #E2E8F0 !important; margin: 16px 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="scout-header">
  <h1>🏢 Sunbelt Scout</h1>
  <p>Minnesota business acquisition pipeline · Scored &amp; filtered daily</p>
</div>
""", unsafe_allow_html=True)

if not CSV_PATH.exists():
    st.warning("No candidates.csv found. Run the scout first: `python3 run.py`")
    st.stop()

df = pd.read_csv(CSV_PATH)
df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0).astype(int)

NUMERIC_COLS = [
    "asking_price", "annual_cash_flow", "annual_revenue", "employees",
    "down_10", "down_20",
    "sba_monthly_10pct", "sba_monthly_20pct",
    "annual_debt_service_10pct", "annual_debt_service_20pct",
    "cf_after_debt_10pct", "cf_after_debt_20pct",
    "coc_return_10pct", "coc_return_20pct",
    "dscr_10pct", "dscr_20pct",
    "payoff_years_10pct", "payoff_years_20pct",
]
for col in NUMERIC_COLS:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

def _is_trades(row):
    ctx = f"{row.get('title', '')} {row.get('industry', '')}".lower()
    return any(kw in ctx for kw in TRADES_KEYWORDS)

def _is_healthcare(row):
    ctx = f"{row.get('title', '')} {row.get('industry', '')} {row.get('description', '')}".lower()
    return any(kw in ctx for kw in HEALTHCARE_KEYWORDS)

def _is_lawn_snow(row):
    ctx = f"{row.get('title', '')} {row.get('industry', '')} {row.get('description', '')}".lower()
    return any(kw in ctx for kw in LAWN_SNOW_KEYWORDS)

df["is_trades"] = df.apply(_is_trades, axis=1)
df["is_healthcare"] = df.apply(_is_healthcare, axis=1)
df["is_lawn_snow"] = df.apply(_is_lawn_snow, axis=1)

# ── Sidebar ─────────────────────────────────────────────────────────────────────
st.sidebar.markdown("### Filters")

buckets = st.sidebar.multiselect(
    "Bucket",
    options=sorted(df["bucket"].unique()),
    default=[b for b in ["SHORTLIST", "REVIEW"] if b in df["bucket"].unique()],
    help="SHORTLIST = strong candidate, REVIEW = worth a look, AUTO-REJECT = failed screening criteria",
)

min_score = st.sidebar.slider(
    "Min Score", 0, 100, 35,
    help="Composite 0–100 score based on financial strength, recurring revenue, tech opportunity, industry durability, and geography",
)
max_price = st.sidebar.number_input(
    "Max Asking Price ($)", value=3000000, step=100000,
    help="Filter out businesses above this asking price",
)
min_cf = st.sidebar.number_input(
    "Min Annual Cash Flow ($)", value=0, step=25000,
    help="Seller's Discretionary Earnings (SDE) — pre-debt owner income",
)
min_coc = st.sidebar.slider(
    "Min Cash-on-Cash Return (20% down)", 0, 200, 0, format="%d%%",
    help="Annual cash flow after SBA debt service divided by your 20% down payment. 30%+ is strong.",
)
min_coc_decimal = min_coc / 100.0

st.sidebar.markdown("---")
absentee_only = st.sidebar.checkbox(
    "Absentee / Semi-Absentee Only",
    help="Show only businesses where the owner is not actively working full-time — better for a hands-off investor",
)
twin_cities_only = st.sidebar.checkbox(
    "Twin Cities Only",
    help="Limit to listings in the Minneapolis–Saint Paul metro area",
)
trades_only = st.sidebar.checkbox(
    "Trades Only",
    help="Plumbing, electrical, HVAC, roofing, landscaping, pest control, and other field-service businesses",
)
healthcare_only = st.sidebar.checkbox(
    "Healthcare Only",
    help="Home health, dental, medical practices, physical therapy, senior care, and related healthcare businesses",
)
lawn_snow_only = st.sidebar.checkbox(
    "Lawn Care / Snow Only",
    help="Landscaping, lawn maintenance, snow removal, tree service, irrigation, and grounds care businesses",
)

st.sidebar.markdown("---")
view_mode = st.sidebar.radio(
    "View Mode", ["Cards", "Table"], horizontal=True,
    help="Cards give a visual overview; Table allows sorting and row-click to open a deal sheet",
)

# ── Apply filters ───────────────────────────────────────────────────────────────
mask = df["bucket"].isin(buckets) if buckets else pd.Series([True] * len(df))
mask &= df["score"] >= min_score
mask &= (df["asking_price"].isna()) | (df["asking_price"] <= max_price)
mask &= (df["annual_cash_flow"].isna()) | (df["annual_cash_flow"] >= min_cf)

if min_coc_decimal > 0:
    mask &= (df["coc_return_20pct"].isna()) | (df["coc_return_20pct"] >= min_coc_decimal)
if absentee_only:
    mask &= df["absentee"].isin(["Likely", "Possible"])
if trades_only:
    mask &= df["is_trades"] == True
if healthcare_only:
    mask &= df["is_healthcare"] == True
if lawn_snow_only:
    mask &= df["is_lawn_snow"] == True
if twin_cities_only:
    tc_pattern = "|".join([
        "minneapolis", "saint paul", "st\\. paul", "bloomington", "plymouth",
        "eden prairie", "burnsville", "minnetonka", "eagan", "edina",
        "maple grove", "woodbury", "coon rapids", "brooklyn park",
        "twin cities", "metro",
    ])
    tc_mask = (
        df["location"].str.contains(tc_pattern, case=False, na=False) |
        df["reasons"].str.contains("Twin Cities", case=False, na=False)
    )
    mask &= tc_mask

filtered = df[mask].sort_values("score", ascending=False)

# ── Summary stats bar ───────────────────────────────────────────────────────────
n_total     = len(df)
n_filtered  = len(filtered)
n_shortlist = len(df[df["bucket"] == "SHORTLIST"])
n_rejected  = len(df[df["bucket"] == "AUTO-REJECT"])

st.markdown(f"""
<div class="stat-bar">
  <div class="stat-pill" title="Total listings scraped from Sunbelt Midwest">
    <div class="label">Total Listings</div>
    <div class="value blue">{n_total}</div>
  </div>
  <div class="stat-pill" title="Listings matching your current filters">
    <div class="label">Filtered</div>
    <div class="value">{n_filtered}</div>
  </div>
  <div class="stat-pill" title="Listings scoring above {65} — strong acquisition candidates">
    <div class="label">Shortlisted</div>
    <div class="value green">{n_shortlist}</div>
  </div>
  <div class="stat-pill" title="Listings automatically rejected — missing financials, wrong price range, regulated industry, or digital-only">
    <div class="label">Auto-Rejected</div>
    <div class="value red">{n_rejected}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Helpers ─────────────────────────────────────────────────────────────────────
def _badge(bucket):
    cls = {"SHORTLIST": "badge-shortlist", "REVIEW": "badge-review", "AUTO-REJECT": "badge-reject"}.get(bucket, "badge-review")
    return f'<span class="badge {cls}">{bucket}</span>'

def _fmt(val, fmt="$"):
    if pd.isna(val):
        return "—"
    if fmt == "$":
        return f"${val:,.0f}"
    if fmt == "$M":
        return f"${val/1e6:.2f}M"
    if fmt == "%":
        return f"{val*100:.0f}%"
    if fmt == "x":
        return f"{val:.2f}x"
    return str(val)


# ── Deal Sheet dialog ────────────────────────────────────────────────────────────
@st.dialog("Deal Sheet", width="large")
def show_deal_sheet(row):
    title  = row.get("title", "Untitled")
    url    = row.get("url", "")
    bucket = str(row.get("bucket", ""))
    score  = int(row.get("score", 0))

    # Title row
    url_html = f'<a class="ds-link" href="{url}" target="_blank">View on Sunbelt →</a>' if url and str(url) != "nan" else ""
    badge_cls = {"SHORTLIST": "badge-shortlist", "REVIEW": "badge-review", "AUTO-REJECT": "badge-reject"}.get(bucket, "badge-review")
    st.markdown(f"""
        <div class="ds-title">{title}</div>
        <div style="display:flex;align-items:center;gap:10px;margin:6px 0 16px;">
            <span class="badge {badge_cls}">{bucket}</span>
            <span style="font-size:13px;color:#475569;font-weight:600;">Score: {score} / 100</span>
            {url_html}
        </div>
    """, unsafe_allow_html=True)

    # Top KPIs
    asking = row.get("asking_price")
    cf     = row.get("annual_cash_flow")
    rev    = row.get("annual_revenue")
    emps   = row.get("employees")
    absentee = row.get("absentee", "No")

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Asking Price",    _fmt(asking), help="Total business price as listed by the broker")
    k2.metric("Cash Flow (SDE)", _fmt(cf),     help="Seller's Discretionary Earnings — owner's total pre-debt income from the business")
    k3.metric("Annual Revenue",  _fmt(rev),    help="Total annual gross revenue reported by the seller")
    k4.metric("Employees",       int(emps) if pd.notna(emps) else "—", help="Full-time + part-time headcount")
    k5.metric("Absentee",        absentee,     help="Whether the current owner is hands-off. 'Likely' = explicitly stated. 'Possible' = inferred from description.")

    # SBA
    st.markdown('<div class="ds-section" title="SBA 7(a) loan modeled at 10% interest, 10-year term">SBA Financing Scenarios</div>', unsafe_allow_html=True)
    sba_l, sba_r = st.columns(2)

    def _sba_col(col, pct_label, down_key, monthly_key, cf_key, coc_key, dscr_key):
        with col:
            st.markdown(f'<div class="sba-block"><h4>{pct_label} Down</h4>', unsafe_allow_html=True)
            down    = row.get(down_key)
            monthly = row.get(monthly_key)
            cf_aft  = row.get(cf_key)
            coc     = row.get(coc_key)
            dscr    = row.get(dscr_key)
            r1, r2 = st.columns(2)
            r1.metric("Down Payment",   _fmt(down),          help="Cash required at closing")
            r2.metric("Monthly Payment",_fmt(monthly),       help="SBA loan monthly payment (10% rate, 10-year term)")
            r3, r4 = st.columns(2)
            r3.metric("CF After Debt",  _fmt(cf_aft),        help="Annual cash flow remaining after SBA debt service")
            r4.metric("CoC Return",     _fmt(coc, "%"),      help="Cash-on-cash return: CF after debt ÷ down payment. 30%+ is strong.")
            st.metric("DSCR",           _fmt(dscr, "x"),     help="Debt Service Coverage Ratio: cash flow ÷ annual debt. Must be ≥1.25 for SBA approval. 1.5+ is comfortable.")
            st.markdown('</div>', unsafe_allow_html=True)

    _sba_col(sba_l, "10%", "down_10", "sba_monthly_10pct", "cf_after_debt_10pct", "coc_return_10pct", "dscr_10pct")
    _sba_col(sba_r, "20%", "down_20", "sba_monthly_20pct", "cf_after_debt_20pct", "coc_return_20pct", "dscr_20pct")

    # Seller Financing
    st.markdown('<div class="ds-section" title="Seller carries the 10% down payment as a subordinated note (6% / 5yr). No cash out of pocket.">Seller Financing Scenario (Zero Cash Down)</div>', unsafe_allow_html=True)
    sf_note = row.get("seller_note_amount")
    sf_monthly = row.get("seller_note_monthly")
    sf_standby = row.get("cf_during_standby")
    sf_after = row.get("cf_after_seller_financing")
    sf_dscr = row.get("dscr_seller_financed")

    sf1, sf2, sf3, sf4, sf5 = st.columns(5)
    sf1.metric("Your Cash Down", "$0", help="Seller carries the 10% down payment — you put in nothing at close")
    sf2.metric("Seller Note", _fmt(sf_note), help="10% of purchase price carried by seller at 6% / 5-year term")
    sf3.metric("Seller Note Payment", _fmt(sf_monthly) + "/mo" if sf_monthly else "—", help="Monthly seller note payment (kicks in after 24-month standby)")
    sf4.metric("CF Years 1–2", _fmt(sf_standby), help="Annual cash flow after SBA only — seller note on standby for first 24 months")
    sf5.metric("CF Years 3+", _fmt(sf_after), help="Annual cash flow after both SBA loan and seller note payments")

    if sf_dscr is not None:
        dscr_color = "normal" if sf_dscr >= 1.25 else "inverse"
        st.metric("DSCR (Years 3+)", f"{sf_dscr:.2f}x", help="Combined debt coverage after standby ends. SBA requires ≥1.25.", delta="SBA eligible" if sf_dscr >= 1.25 else "Below SBA minimum", delta_color=dscr_color)

    st.caption("⚠️ SBA requires seller note to be on full standby (no payments) for first 24 months. Seller must agree to this structure.")

    # Business details
    st.markdown('<div class="ds-section">Business Details</div>', unsafe_allow_html=True)
    d1, d2, d3, d4, d5 = st.columns(5)
    d1.metric("Location",         row.get("location", "—") or "—")
    d2.metric("Industry",         row.get("industry",  "—") or "—")
    d3.metric("Years Operating",  row.get("years_in_business", "—") or "—", help="Years the business has been in operation")
    d4.metric("Franchise?",       row.get("is_franchise", "—") or "—",      help="Franchise resales carry ongoing royalty fees and franchisor approval requirements")
    d5.metric("SBA Pre-Approved?",row.get("sba_available",  "—") or "—",    help="Whether the broker has indicated SBA financing is available")

    reason = row.get("reason_for_selling", "") or ""
    if reason and str(reason) != "nan":
        st.markdown(f'<div style="font-size:13px;color:#475569;margin-top:6px;"><b>Reason for selling:</b> {reason}</div>', unsafe_allow_html=True)

    # Tags
    tags = []
    if absentee in ("Likely", "Possible"):
        tags.append('<span class="tag tag-absentee">🏠 Absentee</span>')
    if row.get("is_trades"):
        tags.append('<span class="tag tag-trades">🔧 Trades</span>')
    if row.get("is_healthcare"):
        tags.append('<span class="tag tag-healthcare">🏥 Healthcare</span>')
    if row.get("is_lawn_snow"):
        tags.append('<span class="tag tag-lawn-snow">🌿 Lawn / Snow</span>')
    if tags:
        st.markdown(f'<div class="card-tags">{"".join(tags)}</div>', unsafe_allow_html=True)

    # Rule-based narrative
    narrative = row.get("narrative", "")
    if narrative and str(narrative) != "nan":
        st.markdown('<div class="ds-section" title="Auto-generated deal summary based on scored signals">Deal Summary</div>', unsafe_allow_html=True)

        def _narrative_section(text, prefix, icon, bg, border, label_color):
            if prefix not in text:
                return ""
            body = text.split(prefix, 1)[1]
            # Trim at next known section
            for stop in ["What's attractive:", "Watch-outs:", "Bottom line:"]:
                if stop != prefix and stop in body:
                    body = body.split(stop)[0]
            body = body.strip().rstrip(".")
            items = [s.strip().rstrip(".") for s in body.split(";") if s.strip()]
            bullets = "".join(f'<li style="margin-bottom:4px">{i}.</li>' for i in items)
            return f"""
            <div style="background:{bg};border:1px solid {border};border-radius:10px;padding:14px 18px;margin-bottom:10px">
                <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;color:{label_color};margin-bottom:8px">{icon} {prefix.rstrip(':')}</div>
                <ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.7;color:#1E293B">{bullets}</ul>
            </div>"""

        def _verdict_section(text):
            if "Bottom line:" not in text:
                return ""
            body = text.split("Bottom line:", 1)[1].strip()
            return f"""
            <div style="background:#1E3A5F;border-radius:10px;padding:14px 18px;margin-bottom:10px">
                <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.6px;color:#93C5FD;margin-bottom:6px">⚖️ Bottom Line</div>
                <div style="font-size:14px;font-weight:600;color:white;line-height:1.6">{body}</div>
            </div>"""

        intro_html = ""
        if "What's attractive:" in narrative:
            intro = narrative.split("What's attractive:")[0].strip()
        else:
            intro = narrative
        if intro:
            intro_html = f'<div style="font-size:13px;color:#475569;margin-bottom:10px;line-height:1.65">{intro}</div>'

        html = (
            intro_html
            + _narrative_section(narrative, "What's attractive:", "✅", "#F0FDF4", "#86EFAC", "#15803D")
            + _narrative_section(narrative, "Watch-outs:", "⚠️", "#FFFBEB", "#FCD34D", "#B45309")
            + _verdict_section(narrative)
        )
        st.markdown(html, unsafe_allow_html=True)

    # Scoring signals
    reasons = row.get("reasons", "")
    if reasons and str(reasons) != "nan":
        st.markdown('<div class="ds-section" title="Factors that contributed to this listing\'s score">Scoring Signals</div>', unsafe_allow_html=True)
        st.info(str(reasons))

    # Description
    desc = row.get("description", "")
    if desc and str(desc) != "nan":
        st.markdown('<div class="ds-section">Listing Description</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="font-size:14px;line-height:1.65;color:#334155">{desc}</div>', unsafe_allow_html=True)


# ── Card view ───────────────────────────────────────────────────────────────────
def render_cards(rows):
    cols = st.columns(3)
    for i, (_, row) in enumerate(rows.iterrows()):
        bucket   = str(row.get("bucket", ""))
        score    = int(row.get("score", 0))
        title    = row.get("title", "Untitled")
        location = row.get("location", "")
        asking   = row.get("asking_price")
        cf       = row.get("annual_cash_flow")
        coc      = row.get("coc_return_20pct")
        dscr     = row.get("dscr_20pct")
        absentee = row.get("absentee", "No")

        badge_cls = {"SHORTLIST": "badge-shortlist", "REVIEW": "badge-review", "AUTO-REJECT": "badge-reject"}.get(bucket, "badge-review")

        # Category emoji — pick the most specific match
        if row.get("is_healthcare"):
            cat_emoji = "🩺"
        elif row.get("is_lawn_snow"):
            cat_emoji = "🌿"
        elif row.get("is_trades"):
            cat_emoji = "🔧"
        else:
            cat_emoji = "🏢"

        tags_html = ""
        if absentee in ("Likely", "Possible"):
            tags_html += '<span class="tag tag-absentee">🏠 Absentee</span>'
        if row.get("is_trades"):
            tags_html += '<span class="tag tag-trades">🔧 Trades</span>'
        if row.get("is_healthcare"):
            tags_html += '<span class="tag tag-healthcare">🏥 Healthcare</span>'
        if row.get("is_lawn_snow"):
            tags_html += '<span class="tag tag-lawn-snow">🌿 Lawn / Snow</span>'

        loc_html = f'<div class="card-location">📍 {location}</div>' if location and str(location) != "nan" else ""

        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"""
                <div class="biz-card">
                    <div class="card-header">
                        <span class="badge {badge_cls}">{bucket}</span>
                        <span class="score-chip">Score: {score}</span>
                        <span style="margin-left:auto;font-size:22px">{cat_emoji}</span>
                    </div>
                    <div class="card-title">{title}</div>
                    {loc_html}
                    <div class="card-metrics">
                        <div class="card-metric" title="Total asking price">
                            <div class="cm-label">Price</div>
                            <div class="cm-value">{_fmt(asking, "$M")}</div>
                        </div>
                        <div class="card-metric" title="Seller's Discretionary Earnings — pre-debt owner income">
                            <div class="cm-label">Cash Flow</div>
                            <div class="cm-value">{_fmt(cf)}</div>
                        </div>
                        <div class="card-metric" title="Cash-on-cash return with 20% down payment after SBA debt service">
                            <div class="cm-label">CoC (20%)</div>
                            <div class="cm-value">{_fmt(coc, "%")}</div>
                        </div>
                        <div class="card-metric" title="Debt Service Coverage Ratio with 20% down — must be ≥1.25 for SBA">
                            <div class="cm-label">DSCR (20%)</div>
                            <div class="cm-value">{_fmt(dscr, "x")}</div>
                        </div>
                    </div>
                    {f'<div class="card-tags">{tags_html}</div>' if tags_html else ""}
                </div>
                """, unsafe_allow_html=True)

                if st.button("View Deal →", key=f"card_{row.get('id', i)}", use_container_width=True):
                    show_deal_sheet(row)


# ── Table view ──────────────────────────────────────────────────────────────────
def render_table(rows):
    display_cols = [
        "score", "bucket", "title", "asking_price",
        "annual_cash_flow", "cf_after_debt_20pct", "coc_return_20pct",
        "dscr_20pct", "absentee", "location", "url",
    ]
    available = [c for c in display_cols if c in rows.columns]
    display_df = rows[available].copy()

    if "coc_return_20pct" in display_df.columns:
        display_df["coc_return_20pct"] = display_df["coc_return_20pct"] * 100

    event = st.dataframe(
        display_df,
        column_config={
            "score":              st.column_config.NumberColumn("Score", width="small",  help="Composite 0–100 acquisition score"),
            "bucket":             st.column_config.TextColumn("Bucket",   width="small",  help="SHORTLIST / REVIEW / AUTO-REJECT"),
            "title":              st.column_config.TextColumn("Business", width="large"),
            "asking_price":       st.column_config.NumberColumn("Price ($)",        format="%.0f", width="small", help="Asking price"),
            "annual_cash_flow":   st.column_config.NumberColumn("Cash Flow ($)",    format="%.0f", width="small", help="Seller's Discretionary Earnings"),
            "cf_after_debt_20pct":st.column_config.NumberColumn("CF After Debt ($)",format="%.0f", width="small", help="Annual cash remaining after SBA payments at 20% down"),
            "coc_return_20pct":   st.column_config.NumberColumn("CoC (%)",          format="%.0f", width="small", help="Cash-on-cash return at 20% down. 30%+ is strong."),
            "dscr_20pct":         st.column_config.NumberColumn("DSCR",             format="%.2f", width="small", help="Debt Service Coverage Ratio at 20% down. Must be ≥1.25."),
            "absentee":           st.column_config.TextColumn("Absentee",  width="small",  help="Owner involvement level"),
            "location":           st.column_config.TextColumn("Location",  width="small"),
            "url":                st.column_config.LinkColumn("Link",      width="small"),
        },
        hide_index=True,
        height=680,
        use_container_width=True,
        selection_mode="single-row",
        on_select="rerun",
    )

    if event.selection.rows:
        show_deal_sheet(rows.iloc[event.selection.rows[0]])


# ── Render ───────────────────────────────────────────────────────────────────────
if len(filtered) == 0:
    st.info("No listings match the current filters.")
elif view_mode == "Cards":
    render_cards(filtered)
else:
    render_table(filtered)

# ── Expanders ────────────────────────────────────────────────────────────────────
with st.expander("📊 Scoring Breakdown (top 20)"):
    for _, row in filtered.head(20).iterrows():
        reasons = row.get("reasons", "")
        title   = row.get("title", "Untitled")
        url     = row.get("url", "")
        link    = f"[{title}]({url})" if url and str(url) != "nan" else f"**{title}**"
        st.markdown(
            f"{link} — Score: **{row.get('score', 0)}** | Absentee: {row.get('absentee', 'No')}\n\n"
            f"_{reasons}_"
        )
        st.divider()

with st.expander("💰 SBA Financing Comparison (10% vs 20% Down)"):
    sba_cols = [
        "title",
        "asking_price", "down_10", "sba_monthly_10pct", "cf_after_debt_10pct", "coc_return_10pct",
        "down_20", "sba_monthly_20pct", "cf_after_debt_20pct", "coc_return_20pct",
    ]
    sba_available = [c for c in sba_cols if c in filtered.columns]
    sba_df = filtered[filtered["bucket"] != "AUTO-REJECT"][sba_available].head(20).copy()
    for col in ["coc_return_10pct", "coc_return_20pct"]:
        if col in sba_df.columns:
            sba_df[col] = sba_df[col] * 100

    st.dataframe(
        sba_df,
        column_config={
            "title":               st.column_config.TextColumn("Business", width="large"),
            "asking_price":        st.column_config.NumberColumn("Price ($)",           format="%.0f"),
            "down_10":             st.column_config.NumberColumn("Down 10% ($)",        format="%.0f", help="10% down payment"),
            "sba_monthly_10pct":   st.column_config.NumberColumn("Monthly 10% ($)",     format="%.0f", help="Monthly SBA payment at 10% down"),
            "cf_after_debt_10pct": st.column_config.NumberColumn("CF After Debt 10%($)",format="%.0f", help="Cash flow after SBA debt at 10% down"),
            "coc_return_10pct":    st.column_config.NumberColumn("CoC 10% (%)",         format="%.0f", help="Cash-on-cash return at 10% down"),
            "down_20":             st.column_config.NumberColumn("Down 20% ($)",        format="%.0f", help="20% down payment"),
            "sba_monthly_20pct":   st.column_config.NumberColumn("Monthly 20% ($)",     format="%.0f", help="Monthly SBA payment at 20% down"),
            "cf_after_debt_20pct": st.column_config.NumberColumn("CF After Debt 20%($)",format="%.0f", help="Cash flow after SBA debt at 20% down"),
            "coc_return_20pct":    st.column_config.NumberColumn("CoC 20% (%)",         format="%.0f", help="Cash-on-cash return at 20% down"),
        },
        hide_index=True,
        use_container_width=True,
    )
