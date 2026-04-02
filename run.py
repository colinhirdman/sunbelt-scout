from scout.fetch import fetch_all_listings as fetch_sunbelt
from scout.fetch_calhoun import fetch_all_listings as fetch_calhoun
from scout.parse import parse_listings
from scout.score import score_listing, profile_score
from scout.narrative import generate_narrative
from scout.storage import load_state, save_state, upsert_rows, SUNBELT_CSV, CALHOUN_CSV
from scout.report import write_report


def _run_source(fetch_fn, source_name, csv_path, seen):
    raw, discovered_ids = fetch_fn()
    listings = parse_listings(raw)
    new_listings = [l for l in listings if l["id"] not in seen]

    scored = []
    for l in new_listings:
        l.update(score_listing(l))
        l.update(profile_score(l))
        l["narrative"] = generate_narrative(l)
        l["source"] = source_name
        scored.append(l)

    upsert_rows(scored, active_ids=discovered_ids, csv_path=csv_path)

    buckets = {}
    for s in scored:
        b = s.get("bucket", "?")
        buckets[b] = buckets.get(b, 0) + 1
    summary = ", ".join(f"{v} {k}" for k, v in sorted(buckets.items()))
    print(f"  [{source_name}] {len(raw)} fetched, {len(new_listings)} new. {summary}")

    return {l["id"] for l in new_listings}, scored


def main():
    state = load_state()
    seen = set(state.get("seen_ids", []))

    print("── Sunbelt Midwest ──")
    sunbelt_new_ids, sunbelt_scored = _run_source(fetch_sunbelt, "sunbelt", SUNBELT_CSV, seen)
    seen.update(sunbelt_new_ids)

    print("── Calhoun Companies ──")
    calhoun_new_ids, calhoun_scored = _run_source(fetch_calhoun, "calhoun", CALHOUN_CSV, seen)
    seen.update(calhoun_new_ids)

    state["seen_ids"] = list(seen)[-5000:]
    save_state(state)

    all_scored = sunbelt_scored + calhoun_scored
    write_report(all_scored)

    total_new = len(sunbelt_new_ids) + len(calhoun_new_ids)
    print(f"Done. {total_new} new listings total.")


if __name__ == "__main__":
    main()
