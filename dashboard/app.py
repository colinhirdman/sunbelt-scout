import streamlit as st
import pandas as pd
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[1] / "output" / "candidates.csv"

st.set_page_config(page_title="Sunbelt Scout", layout="wide")
st.title("Sunbelt Scout — Minnesota Business Acquisitions")

if not CSV_PATH.exists():
    st.warning("No candidates.csv found. Run the scout first: `python3 run.py`")
    st.stop()

df = pd.read_csv(CSV_PATH)

# Coerce numeric columns
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

# --- Sidebar filters ---
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

# --- Apply filters ---
mask = df["bucket"].isin(buckets) if buckets else pd.Series([True] * len(df))
mask &= df["score"] >= min_score
mask &= (df["asking_price"].isna()) | (df["asking_price"] <= max_price)
mask &= (df["annual_cash_flow"].isna()) | (df["annual_cash_flow"] >= min_cf)

if min_coc_decimal > 0:
    mask &= (df["coc_return_20pct"].isna()) | (df["coc_return_20pct"] >= min_coc_decimal)

if absentee_only:
    mask &= df["absentee"].isin(["Likely", "Possible"])

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

# --- Main table ---
display_cols = [
    "score", "bucket", "title", "asking_price",
    "annual_cash_flow", "cf_after_debt_20pct", "coc_return_20pct",
    "dscr_20pct", "absentee", "location", "url",
]
available = [c for c in display_cols if c in filtered.columns]

if len(filtered) > 0:
    display_df = filtered[available].copy()

    # Convert CoC from decimal to percentage for display (0.97 -> 97)
    if "coc_return_20pct" in display_df.columns:
        display_df["coc_return_20pct"] = display_df["coc_return_20pct"] * 100

    st.dataframe(
        display_df,
        column_config={
            "score": st.column_config.NumberColumn("Score", width="small"),
            "bucket": st.column_config.TextColumn("Bucket", width="small"),
            "title": st.column_config.TextColumn("Business", width="large"),
            "asking_price": st.column_config.NumberColumn("Price", format="$%,.0f", width="small"),
            "annual_cash_flow": st.column_config.NumberColumn("Cash Flow", format="$%,.0f", width="small"),
            "cf_after_debt_20pct": st.column_config.NumberColumn("CF After Debt", format="$%,.0f", width="small"),
            "coc_return_20pct": st.column_config.NumberColumn("CoC %", format="%.0f%%", width="small"),
            "dscr_20pct": st.column_config.NumberColumn("DSCR", format="%.2f", width="small"),
            "absentee": st.column_config.TextColumn("Absentee", width="small"),
            "location": st.column_config.TextColumn("Location", width="small"),
            "url": st.column_config.LinkColumn("Link", width="small"),
        },
        hide_index=True,
        height=700,
        use_container_width=True,
    )
else:
    st.info("No listings match the current filters.")

# --- Scoring breakdown ---
with st.expander("Scoring Breakdown (top 20)"):
    top = filtered.head(20)
    for _, row in top.iterrows():
        reasons = row.get("reasons", "")
        st.markdown(
            f"**{row.get('title', 'Untitled')}** — Score: {row.get('score', 0)} | "
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

    # Convert CoC from decimal to percentage for display
    for col in ["coc_return_10pct", "coc_return_20pct"]:
        if col in sba_df.columns:
            sba_df[col] = sba_df[col] * 100

    st.dataframe(
        sba_df,
        column_config={
            "title": st.column_config.TextColumn("Business", width="large"),
            "asking_price": st.column_config.NumberColumn("Price", format="$%,.0f"),
            "down_10": st.column_config.NumberColumn("Down 10%", format="$%,.0f"),
            "sba_monthly_10pct": st.column_config.NumberColumn("Monthly (10%)", format="$%,.0f"),
            "cf_after_debt_10pct": st.column_config.NumberColumn("CF After Debt (10%)", format="$%,.0f"),
            "coc_return_10pct": st.column_config.NumberColumn("CoC (10%)", format="%.0f%%"),
            "down_20": st.column_config.NumberColumn("Down 20%", format="$%,.0f"),
            "sba_monthly_20pct": st.column_config.NumberColumn("Monthly (20%)", format="$%,.0f"),
            "cf_after_debt_20pct": st.column_config.NumberColumn("CF After Debt (20%)", format="$%,.0f"),
            "coc_return_20pct": st.column_config.NumberColumn("CoC (20%)", format="%.0f%%"),
        },
        hide_index=True,
        use_container_width=True,
    )
