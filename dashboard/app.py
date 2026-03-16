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

st.set_page_config(page_title="Sunbelt Scout", layout="wide")
st.title("Sunbelt Scout — Minnesota Business Acquisitions")

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

df["is_trades"] = df.apply(_is_trades, axis=1)
df["is_healthcare"] = df.apply(_is_healthcare, axis=1)

# --- Sidebar ---
st.sidebar.header("Filters")

buckets = st.sidebar.multiselect(
    "Bucket",
    options=sorted(df["bucket"].unique()),
    default=[b for b in ["SHORTLIST", "REVIEW"] if b in df["bucket"].unique()],
)

min_score = st.sidebar.slider("Min Score", 0, 100, 35)
max_price = st.sidebar.number_input("Max Asking Price ($)", value=3000000, step=100000)
min_cf = st.sidebar.number_input("Min Annual Cash Flow ($)", value=0, step=25000)

min_coc = st.sidebar.slider("Min Cash-on-Cash Return (20% down)", 0, 200, 0, format="%d%%")
min_coc_decimal = min_coc / 100.0

absentee_only = st.sidebar.checkbox("Absentee / Semi-Absentee Only")
twin_cities_only = st.sidebar.checkbox("Twin Cities Only")
trades_only = st.sidebar.checkbox("Trades Only (plumbing, electrical, HVAC, etc.)")
healthcare_only = st.sidebar.checkbox("Healthcare Only (medical, dental, home health, etc.)")

st.sidebar.divider()
view_mode = st.sidebar.radio("View Mode", ["Table", "Cards"], horizontal=True)

# --- Apply filters ---
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

# --- Top metrics ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Listings", len(df))
col2.metric("Filtered", len(filtered))
col3.metric("Shortlisted", len(df[df["bucket"] == "SHORTLIST"]))
col4.metric("Auto-Rejected", len(df[df["bucket"] == "AUTO-REJECT"]))

st.divider()


# --- Deal Sheet dialog ---
@st.dialog("Deal Sheet", width="large")
def show_deal_sheet(row):
    title = row.get("title", "Untitled")
    url = row.get("url", "")
    bucket = str(row.get("bucket", ""))
    score = int(row.get("score", 0))

    bucket_icons = {"SHORTLIST": "🟢", "REVIEW": "🟡", "AUTO-REJECT": "🔴"}
    icon = bucket_icons.get(bucket, "⚪")

    st.markdown(f"## {title}")
    if url and str(url) != "nan":
        st.markdown(f"[View on Sunbelt →]({url})")

    h1, h2, h3 = st.columns(3)
    h1.metric("Score", score)
    h2.metric("Bucket", f"{icon} {bucket}")
    h3.metric("Absentee", row.get("absentee", "No"))

    st.divider()

    # Key financials
    st.subheader("Financials")
    asking = row.get("asking_price")
    cf = row.get("annual_cash_flow")
    rev = row.get("annual_revenue")
    emps = row.get("employees")

    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Asking Price", f"${asking:,.0f}" if pd.notna(asking) else "N/A")
    f2.metric("Annual Cash Flow", f"${cf:,.0f}" if pd.notna(cf) else "N/A")
    f3.metric("Annual Revenue", f"${rev:,.0f}" if pd.notna(rev) else "N/A")
    f4.metric("Employees", int(emps) if pd.notna(emps) else "N/A")

    st.divider()

    # SBA side-by-side
    st.subheader("SBA Financing")
    sba_left, sba_right = st.columns(2)

    with sba_left:
        st.markdown("**10% Down**")
        down10 = row.get("down_10")
        monthly10 = row.get("sba_monthly_10pct")
        cf10 = row.get("cf_after_debt_10pct")
        coc10 = row.get("coc_return_10pct")
        dscr10 = row.get("dscr_10pct")
        s1, s2 = st.columns(2)
        s1.metric("Down Payment", f"${down10:,.0f}" if pd.notna(down10) else "N/A")
        s2.metric("Monthly Payment", f"${monthly10:,.0f}" if pd.notna(monthly10) else "N/A")
        s3, s4 = st.columns(2)
        s3.metric("CF After Debt", f"${cf10:,.0f}" if pd.notna(cf10) else "N/A")
        s4.metric("CoC Return", f"{coc10*100:.0f}%" if pd.notna(coc10) else "N/A")
        st.metric("DSCR", f"{dscr10:.2f}" if pd.notna(dscr10) else "N/A")

    with sba_right:
        st.markdown("**20% Down**")
        down20 = row.get("down_20")
        monthly20 = row.get("sba_monthly_20pct")
        cf20 = row.get("cf_after_debt_20pct")
        coc20 = row.get("coc_return_20pct")
        dscr20 = row.get("dscr_20pct")
        t1, t2 = st.columns(2)
        t1.metric("Down Payment", f"${down20:,.0f}" if pd.notna(down20) else "N/A")
        t2.metric("Monthly Payment", f"${monthly20:,.0f}" if pd.notna(monthly20) else "N/A")
        t3, t4 = st.columns(2)
        t3.metric("CF After Debt", f"${cf20:,.0f}" if pd.notna(cf20) else "N/A")
        t4.metric("CoC Return", f"{coc20*100:.0f}%" if pd.notna(coc20) else "N/A")
        st.metric("DSCR", f"{dscr20:.2f}" if pd.notna(dscr20) else "N/A")

    st.divider()

    # Business details
    st.subheader("Business Details")
    d1, d2, d3 = st.columns(3)
    d1.metric("Location", row.get("location", "N/A") or "N/A")
    d2.metric("Industry", row.get("industry", "N/A") or "N/A")
    d3.metric("Years in Business", row.get("years_in_business", "N/A") or "N/A")

    d4, d5, d6 = st.columns(3)
    d4.metric("Franchise?", row.get("is_franchise", "N/A") or "N/A")
    d5.metric("SBA Available?", row.get("sba_available", "N/A") or "N/A")
    reason = row.get("reason_for_selling", "") or ""
    d6.metric("Reason for Selling", reason[:30] + "…" if len(str(reason)) > 30 else reason or "N/A")

    # Tags
    tags = []
    if row.get("absentee") in ("Likely", "Possible"):
        tags.append("🏠 Absentee")
    if row.get("is_trades"):
        tags.append("🔧 Trades")
    if row.get("is_healthcare"):
        tags.append("🏥 Healthcare")
    if tags:
        st.markdown(" · ".join(tags))

    # Scoring signals
    reasons = row.get("reasons", "")
    if reasons and str(reasons) != "nan":
        st.divider()
        st.subheader("Scoring Signals")
        st.info(str(reasons))

    # Description
    desc = row.get("description", "")
    if desc and str(desc) != "nan":
        st.divider()
        st.subheader("Description")
        st.markdown(str(desc))


# --- Card view ---
def _bucket_color(bucket):
    return {"SHORTLIST": "#2ecc71", "REVIEW": "#f39c12", "AUTO-REJECT": "#e74c3c"}.get(bucket, "#95a5a6")

def render_cards(rows):
    cols = st.columns(3)
    for i, (_, row) in enumerate(rows.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                bucket = str(row.get("bucket", ""))
                score = int(row.get("score", 0))
                title = row.get("title", "Untitled")
                location = row.get("location", "")
                asking = row.get("asking_price")
                cf = row.get("annual_cash_flow")
                coc = row.get("coc_return_20pct")
                dscr = row.get("dscr_20pct")
                absentee = row.get("absentee", "No")

                color = _bucket_color(bucket)
                st.markdown(
                    f'<span style="background:{color};color:white;padding:2px 8px;'
                    f'border-radius:4px;font-size:11px;font-weight:bold">{bucket}</span>'
                    f'&nbsp;<span style="font-size:12px;color:#888">Score: {score}</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(f"**{title}**")
                if location and str(location) != "nan":
                    st.caption(str(location))

                m1, m2 = st.columns(2)
                m1.metric("Price", f"${asking/1e6:.2f}M" if pd.notna(asking) else "N/A")
                m2.metric("Cash Flow", f"${cf:,.0f}" if pd.notna(cf) else "N/A")
                m3, m4 = st.columns(2)
                m3.metric("CoC (20%)", f"{coc*100:.0f}%" if pd.notna(coc) else "N/A")
                m4.metric("DSCR (20%)", f"{dscr:.2f}" if pd.notna(dscr) else "N/A")

                tags = []
                if absentee in ("Likely", "Possible"):
                    tags.append("🏠 Absentee")
                if row.get("is_trades"):
                    tags.append("🔧 Trades")
                if row.get("is_healthcare"):
                    tags.append("🏥 Healthcare")
                if tags:
                    st.caption(" · ".join(tags))

                if st.button("View Deal", key=f"card_{row.get('id', i)}", use_container_width=True):
                    show_deal_sheet(row)


# --- Table view ---
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
            "score": st.column_config.NumberColumn("Score", width="small"),
            "bucket": st.column_config.TextColumn("Bucket", width="small"),
            "title": st.column_config.TextColumn("Business", width="large"),
            "asking_price": st.column_config.NumberColumn("Price ($)", format="%.0f", width="small"),
            "annual_cash_flow": st.column_config.NumberColumn("Cash Flow ($)", format="%.0f", width="small"),
            "cf_after_debt_20pct": st.column_config.NumberColumn("CF After Debt ($)", format="%.0f", width="small"),
            "coc_return_20pct": st.column_config.NumberColumn("CoC (%)", format="%.0f", width="small"),
            "dscr_20pct": st.column_config.NumberColumn("DSCR", format="%.2f", width="small"),
            "absentee": st.column_config.TextColumn("Absentee", width="small"),
            "location": st.column_config.TextColumn("Location", width="small"),
            "url": st.column_config.LinkColumn("Link", width="small"),
        },
        hide_index=True,
        height=700,
        use_container_width=True,
        selection_mode="single-row",
        on_select="rerun",
    )

    if event.selection.rows:
        idx = event.selection.rows[0]
        show_deal_sheet(rows.iloc[idx])


# --- Render ---
if len(filtered) == 0:
    st.info("No listings match the current filters.")
elif view_mode == "Cards":
    render_cards(filtered)
else:
    render_table(filtered)

# --- Scoring breakdown ---
with st.expander("Scoring Breakdown (top 20)"):
    top = filtered.head(20)
    for _, row in top.iterrows():
        reasons = row.get("reasons", "")
        title = row.get("title", "Untitled")
        url = row.get("url", "")
        title_display = f"[{title}]({url})" if url and str(url) != "nan" else f"**{title}**"
        st.markdown(
            f"**{title_display}** — Score: {row.get('score', 0)} | "
            f"Absentee: {row.get('absentee', 'No')}\n\n"
            f"_{reasons}_"
        )
        st.divider()

# --- SBA Comparison ---
with st.expander("SBA Financing Comparison (10% vs 20% Down)"):
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
            "title": st.column_config.TextColumn("Business", width="large"),
            "asking_price": st.column_config.NumberColumn("Price ($)", format="%.0f"),
            "down_10": st.column_config.NumberColumn("Down 10% ($)", format="%.0f"),
            "sba_monthly_10pct": st.column_config.NumberColumn("Monthly 10% ($)", format="%.0f"),
            "cf_after_debt_10pct": st.column_config.NumberColumn("CF After Debt 10% ($)", format="%.0f"),
            "coc_return_10pct": st.column_config.NumberColumn("CoC 10% (%)", format="%.0f"),
            "down_20": st.column_config.NumberColumn("Down 20% ($)", format="%.0f"),
            "sba_monthly_20pct": st.column_config.NumberColumn("Monthly 20% ($)", format="%.0f"),
            "cf_after_debt_20pct": st.column_config.NumberColumn("CF After Debt 20% ($)", format="%.0f"),
            "coc_return_20pct": st.column_config.NumberColumn("CoC 20% (%)", format="%.0f"),
        },
        hide_index=True,
        use_container_width=True,
    )
