"""Main entry point for the 4.2 Data Collection re-run.

Collects reviews for all three apps from BOTH Google Play and the Apple
App Store, applies the same 24-month window and English-language filter to
both, pseudonymizes IDs, drops any reviewer-identifying fields, and writes:

  output/reviews_<app>_google_play.csv
  output/reviews_<app>_app_store.csv
  output/combined_reviews.csv            (all apps, both platforms)
  output/collection_manifest.json        (run metadata, for the write-up)

Usage:
    python collect_reviews.py
"""

import csv
import json
import os
from datetime import timedelta

import config
from scrape_app_store import fetch_app_store_reviews, resolve_apple_id
from scrape_google_play import fetch_google_play_reviews


def compute_window():
    end_dt = config.COLLECTION_TIMESTAMP
    # Approximate 24 calendar months as 730 days (24 * ~30.4) would drift;
    # do the calendar-correct subtraction instead.
    year = end_dt.year
    month = end_dt.month - config.WINDOW_MONTHS
    while month <= 0:
        month += 12
        year -= 1
    cutoff_dt = end_dt.replace(year=year, month=month)
    return cutoff_dt, end_dt


def write_csv(path, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=config.OUTPUT_SCHEMA)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main():
    cutoff_dt, end_dt = compute_window()
    print(f"Collection timestamp (fixed): {end_dt.isoformat()}")
    print(f"Window: {config.WINDOW_MONTHS} months -> cutoff {cutoff_dt.isoformat()}")
    print(
        "Note: the originally documented Google-Play-only corpus reports earliest "
        "reviews around 2024-08-25/26, a few days after this window's exact "
        f"calendar cutoff of {cutoff_dt.date()}. That's a real, pre-existing gap "
        "between the two — sanity-check it against this run's actual earliest "
        "review dates rather than assuming either number is wrong.\n"
    )

    all_rows = []
    manifest = {
        "collection_timestamp": end_dt.isoformat(),
        "window_months": config.WINDOW_MONTHS,
        "cutoff_date": cutoff_dt.isoformat(),
        "apps": [],
    }

    for app in config.APPS:
        app_label = app["name"]
        print(f"=== {app_label} ===")

        gp_rows = fetch_google_play_reviews(
            package_name=app["google_play_package"],
            app_label=app_label,
            cutoff_dt=cutoff_dt,
            end_dt=end_dt,
            storefronts=config.GOOGLE_PLAY_STOREFRONTS,
            lang=config.GOOGLE_PLAY_LANG,
            batch_size=config.GOOGLE_PLAY_BATCH_SIZE,
            max_batches_per_storefront=config.GOOGLE_PLAY_MAX_BATCHES_PER_STOREFRONT,
            request_delay_sec=config.GOOGLE_PLAY_REQUEST_DELAY_SEC,
        )
        print(f"  Google Play: {len(gp_rows)} reviews fetched (already language-filtered; dedup'd across storefronts)")

        apple_id = resolve_apple_id(
            bundle_id=app["apple_bundle_id"],
            lookup_countries=config.APPLE_ID_LOOKUP_COUNTRIES,
            delay_sec=config.APPLE_ID_LOOKUP_DELAY_SEC,
        )
        if apple_id is None:
            print(f"  App Store:   SKIPPED — could not resolve Apple ID for bundle {app['apple_bundle_id']!r}")
            as_rows = []
        else:
            print(f"  App Store:   resolved bundle {app['apple_bundle_id']!r} -> Apple ID {apple_id}")
            as_rows = fetch_app_store_reviews(
                apple_id=apple_id,
                app_label=app_label,
                cutoff_dt=cutoff_dt,
                end_dt=end_dt,
                storefronts=config.APPLE_STOREFRONTS,
                pages_max=config.APPLE_PAGES_MAX,
                request_delay_sec=config.APPLE_REQUEST_DELAY_SEC,
                lang=config.GOOGLE_PLAY_LANG,
            )
        print(f"  App Store:   {len(as_rows)} reviews fetched (already language-filtered; dedup'd across storefronts)")

        write_csv(os.path.join(config.OUTPUT_DIR, f"reviews_{app_label.replace(' ', '_').lower()}_google_play.csv"), gp_rows)
        write_csv(os.path.join(config.OUTPUT_DIR, f"reviews_{app_label.replace(' ', '_').lower()}_app_store.csv"), as_rows)

        all_rows.extend(gp_rows)
        all_rows.extend(as_rows)

        manifest["apps"].append(
            {
                "name": app_label,
                "google_play_package": app["google_play_package"],
                "apple_bundle_id": app["apple_bundle_id"],
                "apple_id_resolved": apple_id,
                "google_play_reviews": len(gp_rows),
                "app_store_reviews": len(as_rows),
                "total": len(gp_rows) + len(as_rows),
            }
        )

    # Cross-platform duplicate check: same app, same review_id_hash should
    # never occur across the two platform-specific files since the hash
    # inputs differ by platform, but check anyway rather than assume.
    seen = set()
    duplicates = 0
    for row in all_rows:
        key = (row["app"], row["platform"], row["review_id_hash"])
        if key in seen:
            duplicates += 1
        seen.add(key)
    manifest["duplicate_ids_found"] = duplicates

    combined_path = os.path.join(config.OUTPUT_DIR, "combined_reviews.csv")
    write_csv(combined_path, all_rows)
    manifest["total_reviews"] = len(all_rows)

    manifest_path = os.path.join(config.OUTPUT_DIR, "collection_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\n=== Done ===")
    print(f"Combined corpus: {len(all_rows)} reviews -> {combined_path}")
    print(f"Manifest: {manifest_path}")
    if duplicates:
        print(f"[warn] {duplicates} duplicate (app, platform, review_id_hash) keys found — investigate before using this corpus.")


if __name__ == "__main__":
    main()
