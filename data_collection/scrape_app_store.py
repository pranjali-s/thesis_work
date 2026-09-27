"""Apple App Store review collection — rewritten in this revision.

The previous version used the `app_store_scraper` PyPI package, which
targets an unofficial endpoint that no longer works reliably. This version
instead uses two things Apple actually serves reliably over plain HTTP:

1. The **iTunes Lookup API** (`itunes.apple.com/lookup`) — documented,
   officially supported — to resolve an app's numeric Apple ID from its
   bundle ID. Apple's App Store IDs are numeric and platform-internal;
   the bundle ID (e.g. `com.robinhood.release.Robinhood`) is the stable,
   developer-facing identifier, and is not always the same string as the
   app's Android package name — Coinbase's Apple bundle ID in particular
   (`com.vilcsak.bitcoin2`) looks nothing like `com.coinbase.android`.
2. Apple's **public customer-reviews RSS feed**
   (`itunes.apple.com/{country}/rss/customerreviews/page={page}/id={id}/
   sortBy=mostRecent/json`) — unofficial in the sense that it's undocumented,
   but a plain public JSON endpoint with no auth, which is what actually
   worked for collecting this data.

Two structural facts about this feed carry over from before and are
disclosed, not glossed over:
  - There's no native, stable review ID in the feed. The pseudonymous ID
    here is `hash_id("apple", entry_id)`, where `entry_id` is the feed's
    own `id` field for that entry — stable across pages/re-fetches for the
    same review, but not a documented Apple identifier.
  - `thumbs_up_count` and `developer_reply_present` are not exposed by this
    feed at all and stay null/False. One thing that *did* change for the
    better: `app_version` **is** available here (the feed's `im:version`
    field) — the previous `app_store_scraper`-based version had this as an
    always-null limitation; that limitation no longer applies.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

import requests

from hashing import hash_id
from language_filter import language_matches

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "academic-review-collector/1.0"})


def resolve_apple_id(bundle_id: str, lookup_countries, delay_sec: float) -> int | None:
    """Resolve a bundle ID to Apple's numeric App Store ID via the iTunes
    Lookup API. The numeric ID is the same across every storefront once
    resolved, so this only needs to succeed against one storefront.
    """
    for country in lookup_countries:
        try:
            response = SESSION.get(
                "https://itunes.apple.com/lookup",
                params={"bundleId": bundle_id, "country": country, "entity": "software"},
                timeout=30,
            )
            response.raise_for_status()
            results = response.json().get("results", [])
        except (requests.RequestException, ValueError) as exc:
            print(f"[warn] Apple ID lookup failed for {bundle_id} ({country}): {exc}")
            results = []

        if results:
            return int(results[0]["trackId"])

        time.sleep(delay_sec)

    return None


def _label(entry: dict, key: str, default=""):
    """Apple's RSS JSON wraps most scalar values as {"label": value}."""
    if not isinstance(entry, dict):
        return default
    value = entry.get(key, default)
    return value.get("label", default) if isinstance(value, dict) else value


def _normalize_entries(value) -> list:
    """The feed's `entry` field is a dict when there's exactly one entry,
    a list when there are several, and can be absent entirely — normalize
    all three into a plain list."""
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [entry for entry in value if isinstance(entry, dict)]
    return []


def _parse_date(value: str):
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def fetch_app_store_reviews(
    apple_id,
    app_label,
    cutoff_dt,
    end_dt,
    storefronts,
    pages_max=10,
    request_delay_sec=0.25,
    lang="en",
):
    """Fetch reviews for one already-resolved Apple numeric ID, across the
    given storefronts, filtered to [cutoff_dt, end_dt] and deduplicated.

    The upper bound `end_dt` is a deliberate addition beyond what the
    original working script needed: that script always collected "up to
    now," so it only needed a lower-bound cutoff. This project fixes a
    specific historical window (matching the original Google-Play-only
    collection's documented timestamp), so both bounds are enforced here.

    Returns a list of dicts in the unified output schema.
    """
    collected = []
    seen_ids = set()

    for country in storefronts:
        for page in range(1, pages_max + 1):
            url = (
                f"https://itunes.apple.com/{country}/rss/customerreviews/"
                f"page={page}/id={apple_id}/sortBy=mostRecent/json"
            )
            try:
                response = SESSION.get(url, timeout=30)
            except requests.RequestException as exc:
                print(f"[warn] App Store fetch failed for {app_label}/{country} page {page}: {exc}")
                break

            if response.status_code == 404:
                break
            try:
                response.raise_for_status()
                payload = response.json()
            except (requests.RequestException, ValueError) as exc:
                print(f"[warn] App Store fetch failed for {app_label}/{country} page {page}: {exc}")
                break

            feed = payload.get("feed", {}) if isinstance(payload, dict) else {}
            entries = _normalize_entries(feed.get("entry", []) if isinstance(feed, dict) else [])
            # The feed's first "entry" is often the app's own metadata, not
            # a review — real reviews are the ones carrying a rating.
            review_entries = [e for e in entries if "im:rating" in e]
            if not review_entries:
                break

            page_dates = []
            for entry in review_entries:
                raw_id = str(_label(entry, "id"))
                date = _parse_date(_label(entry, "updated"))
                page_dates.append(date)
                if not raw_id or date is None:
                    continue
                if date < cutoff_dt or date > end_dt:
                    continue

                text = str(_label(entry, "content"))
                if not language_matches(text, lang):
                    continue

                rid = hash_id("apple", raw_id)
                if rid in seen_ids:
                    continue
                seen_ids.add(rid)

                collected.append(
                    {
                        "app": app_label,
                        "platform": "app_store",
                        "review_id_hash": rid,
                        "review_text": text,
                        "rating": int(_label(entry, "im:rating", 0) or 0),
                        "review_date": date.isoformat(),
                        "app_version": _label(entry, "im:version") or None,
                        "thumbs_up_count": None,  # not exposed by this feed
                        "developer_reply_present": None,  # not exposed by this feed
                    }
                )

            # Reviews are sorted most-recent-first; once an entire page is
            # older than the cutoff, every later page will be too.
            if page_dates and all(d and d < cutoff_dt for d in page_dates):
                break

            time.sleep(request_delay_sec)

    return collected
