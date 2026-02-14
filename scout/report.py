from pathlib import Path
from datetime import datetime


def write_report(rows: list[dict]):
    base = Path(__file__).resolve().parents[1]
    out = base / "output"
    out.mkdir(parents=True, exist_ok=True)
    p = out / "daily_report.md"

    day = datetime.utcnow().strftime("%Y-%m-%d")
    shortlist = sorted([r for r in rows if r.get("bucket") == "SHORTLIST"],
                       key=lambda x: x.get("score", 0), reverse=True)
    review = sorted([r for r in rows if r.get("bucket") == "REVIEW"],
                    key=lambda x: x.get("score", 0), reverse=True)
    rejected = [r for r in rows if r.get("bucket") == "AUTO-REJECT"]

    lines = [
        f"# Sunbelt Scout — {day}",
        "",
        f"New listings processed: **{len(rows)}**",
        f"Shortlisted: **{len(shortlist)}** | Review: **{len(review)}** | Auto-Rejected: **{len(rejected)}**",
        "",
    ]

    lines.append("## SHORTLIST")
    if not shortlist:
        lines.append("_None today._")
    for r in shortlist[:20]:
        coc = r.get("coc_return_20pct")
        coc_text = f"{coc:.0%}" if coc is not None else "N/A"
        dscr = r.get("dscr_20pct")
        dscr_text = f"{dscr:.2f}x" if dscr is not None else "N/A"
        cf_after = r.get("cf_after_debt_20pct")
        cf_text = f"${cf_after:,.0f}" if cf_after is not None else "N/A"

        lines += [
            f"- **{r.get('title', 'Untitled')}** (score {r.get('score', 0)})",
            f"  Price: {r.get('asking_price_text', 'N/A')} | CF: ${r.get('annual_cash_flow', 0):,.0f} | CF After Debt: {cf_text}",
            f"  CoC: {coc_text} | DSCR: {dscr_text} | Absentee: {r.get('absentee', 'No')}",
            f"  {r.get('url', '')}",
            f"  _Why_: {', '.join(r.get('reasons', []))}",
            "",
        ]

    lines.append("## REVIEW")
    if not review:
        lines.append("_None today._")
    for r in review[:30]:
        lines += [
            f"- **{r.get('title', 'Untitled')}** (score {r.get('score', 0)}) {r.get('asking_price_text', '')}",
            f"  {r.get('url', '')}",
            f"  _Why_: {', '.join(r.get('reasons', []))}",
            "",
        ]

    lines.append(f"## AUTO-REJECTED ({len(rejected)})")
    for r in rejected[:10]:
        lines += [
            f"- {r.get('title', 'Untitled')}: {', '.join(r.get('reasons', []))}",
        ]

    p.write_text("\n".join(lines), encoding="utf-8")
