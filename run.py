from scout.fetch import fetch_all_listings
from scout.parse import parse_listings
from scout.score import score_listing, profile_score
from scout.narrative import generate_narrative
from scout.storage import load_state, save_state, upsert_rows
from scout.report import write_report


def main():
    state = load_state()
    seen = set(state.get("seen_ids", []))

    raw = fetch_all_listings()
    listings = parse_listings(raw)

    new_listings = [l for l in listings if l["id"] not in seen]

    scored = []
    for l in new_listings:
        s = score_listing(l)
        l.update(s)
        l.update(profile_score(l))
        l["narrative"] = generate_narrative(l)
        scored.append(l)

    active_ids = {l["id"] for l in listings}
    upsert_rows(scored, active_ids=active_ids)

    for l in new_listings:
        seen.add(l["id"])
    state["seen_ids"] = list(seen)[-5000:]
    save_state(state)

    write_report(scored)

    buckets = {}
    for s in scored:
        b = s.get("bucket", "?")
        buckets[b] = buckets.get(b, 0) + 1
    summary = ", ".join(f"{v} {k}" for k, v in sorted(buckets.items()))
    print(f"Done. {len(raw)} fetched, {len(new_listings)} new. {summary}")


if __name__ == "__main__":
    main()
