"""Google Play Store review collection — updated in this revision to match
the multi-storefront pattern from the confirmed-working Apple script,
since Google Play reviews are also partitioned by country storefront (the
original single-platform collection queried only `country="us"`, which
under-covers reviewers browsing a different regional Play Store).

`google_play_scraper` talks to Google's own review-listing endpoint, which
is officially exposed to the Play Store app itself (not a documented
public API with a stability guarantee, but a first-party endpoint, unlike
the two unofficial ones the Apple side depends on).
"""

from __future__ import annotations

import time
from datetime import timezone

from google_play_scraper import Sort, reviews

from hashing import hash_id
from language_filter import language_matches


def _as_utc(dt):
    if dt is None:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def fetch_google_play_reviews(
    package_name,
    app_label,
    cutoff_dt,
    end_dt,
    storefronts,
    lang="en",
    batch_size=200,
    max_batches_per_storefront=2000,
    request_delay_sec=0.5,
):
    """Fetch reviews for one app across the given storefronts, newest
    first per storefront, stopping a storefront's pagination as soon as an
    entire page is older than the cutoff (reviews are sorted newest-first,
    so once that's true, every later page for that storefront will be too).

    `end_dt` is a deliberate addition beyond what the working script this
    is based on needed: that script always collects "up to now," so it
    only enforced a lower-bound cutoff. This project fixes a specific
    historical window (matching the original single-platform collection's
    documented timestamp), so both bounds are enforced here.

    Reviews are deduplicated across storefronts by their hashed ID, the
    same way the Apple side deduplicates across its own storefront list —
    Google Play reviews are generally storefront-local, but this guards
    against the rare case of the same review surfacing from more than one
    query rather than assuming it can't happen.

    Returns a list of dicts already in the unified 9-field output schema,
    already filtered to English (or whatever `lang` resolves to via
    `language_matches`) — callers don't need to filter again.
    """
    collected = []
    seen_ids = set()

    # "all" isn't a real google-play-scraper language code, so the actual
    # request always asks for "en"; the enforcement of `lang` happens via
    # language_matches() below, not via this request parameter.
    request_lang = "en" if lang == "all" else lang

    for country in storefronts:
        continuation_token = None
        stop_storefront = False

        for batch_num in range(max_batches_per_storefront):
            try:
                result, continuation_token = reviews(
                    package_name,
                    lang=request_lang,
                    country=country,
                    sort=Sort.NEWEST,
                    count=batch_size,
                    continuation_token=continuation_token,
                )
            except Exception as exc:
                print(f"[warn] Google Play fetch failed for {app_label}/{country} on batch {batch_num}: {exc}")
                break

            if not result:
                break

            page_dates = [_as_utc(r.get("at")) for r in result]

            for r, at in zip(result, page_dates):
                if at is None or at > end_dt or at < cutoff_dt:
                    continue

                text = (r.get("content") or "").strip()
                if not language_matches(text, lang):
                    continue

                raw_id = str(r.get("reviewId") or "")
                if not raw_id:
                    continue
                rid = hash_id("google_play", raw_id)
                if rid in seen_ids:
                    continue
                seen_ids.add(rid)

                collected.append(
                    {
                        "app": app_label,
                        "platform": "google_play",
                        "review_id_hash": rid,
                        "review_text": text,
                        "rating": r.get("score"),
                        "review_date": at.isoformat(),
                        # `reviewCreatedVersion` is the field this library
                        # actually populates in current versions;
                        # `appVersion` is kept as a fallback for older
                        # library versions that used that key instead.
                        "app_version": r.get("reviewCreatedVersion") or r.get("appVersion"),
                        "thumbs_up_count": r.get("thumbsUpCount"),
                        "developer_reply_present": bool(r.get("replyContent")),
                    }
                )

            if continuation_token is None or (
                page_dates and all(d and d < cutoff_dt for d in page_dates)
            ):
                stop_storefront = True

            if stop_storefront:
                break

            time.sleep(request_delay_sec)

    return collected
