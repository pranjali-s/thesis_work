"""
Configuration for the two-platform (Google Play + Apple App Store) review
collection run, per 4.2 Data Collection.

Everything here is a plain constant on purpose, so the whole run is
reproducible from one file: change an app ID, the collection timestamp, or
the window length here, not inside the scraper scripts.
"""

from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Collection anchor. The 24-month trailing window is computed FROM this
# fixed timestamp, not from whenever the script actually happens to run —
# this preserves the same review time-range documented for the original
# Google-Play-only corpus (initiated 15 Aug 2026 22:21:42 UTC), even though
# this script is being run again later to add Apple App Store data.
# ---------------------------------------------------------------------------
COLLECTION_TIMESTAMP = datetime(2026, 8, 15, 22, 21, 42, tzinfo=timezone.utc)
WINDOW_MONTHS = 24

# --- Storefronts, shared across both platforms ---------------------------
# Both Google Play and the Apple App Store partition reviews by country
# storefront, so both scrapers now query the same five-market list rather
# than Google Play using one hardcoded country ("us") while Apple used a
# different list. The English-language filter (below) is what actually
# enforces "English-language reviews only" — this list just controls where
# we look, not what we keep. These five are not a verified ranking of the
# platforms' largest user bases, just a reasonable fixed set of
# high-traffic markets, used identically for both platforms.
STOREFRONTS = ["us", "gb", "de", "fr", "it"]
APPLE_STOREFRONTS = STOREFRONTS
GOOGLE_PLAY_STOREFRONTS = STOREFRONTS

# --- Apple App Store -------------------------------------------------------
# Resolves each app's numeric Apple ID at run time from its Apple *bundle
# ID* via Apple's own documented iTunes Lookup API, then pulls reviews from
# Apple's public customer-reviews RSS feed directly with `requests`.

# Countries tried, in order, when resolving a bundle ID to a numeric Apple
# ID — the numeric ID is the same across storefronts once resolved, so this
# only needs to succeed once per app.
APPLE_ID_LOOKUP_COUNTRIES = ["us", "gb", "de", "ca", "au"]

# Apple's Lookup/Search API documents a request-rate guideline of roughly
# 20 calls/minute; 3.1s between attempts stays comfortably under that.
APPLE_ID_LOOKUP_DELAY_SEC = 3.1

# Max RSS pages to request per app per storefront (each page holds up to
# 50 reviews; Apple's feed does not go arbitrarily deep).
APPLE_PAGES_MAX = 10

# --- Google Play ------------------------------------------------------------
# The library-level language parameter passed to google-play-scraper's own
# `reviews()` call. "all" isn't a real google-play-scraper language code,
# so when GOOGLE_PLAY_LANG's *enforcement* value is "all" the request
# itself still asks for "en" — the actual all-languages behavior comes from
# not applying the language_matches() filter downstream, not from this
# request parameter.
GOOGLE_PLAY_LANG = "en"

# Be polite to both platforms' rate limits.
GOOGLE_PLAY_REQUEST_DELAY_SEC = 0.5
APPLE_REQUEST_DELAY_SEC = 0.25

# Safety cap so a runaway pagination loop can't scrape forever — the
# working scripts this project is based on rely only on natural
# termination (an empty batch, a null continuation token, or an entire
# page older than the cutoff); this cap is a defensive addition on top of
# that, not a behavior either working script needed.
GOOGLE_PLAY_BATCH_SIZE = 200
GOOGLE_PLAY_MAX_BATCHES_PER_STOREFRONT = 2000

APPS = [
    {
        "name": "Robinhood",
        "google_play_package": "com.robinhood.android",
        # Apple's bundle ID for iOS is not the same string as the Android
        # package name — confirmed via the working script.
        "apple_bundle_id": "com.robinhood.release.Robinhood",
    },
    {
        "name": "Coinbase",
        "google_play_package": "com.coinbase.android",
        # Notably different from both the Android package name and from
        # any "coinbase"-looking string — a legacy bundle ID retained by
        # the app. This would have been silently wrong under the previous
        # hardcoded-numeric-ID approach if that ID had ever drifted.
        "apple_bundle_id": "com.vilcsak.bitcoin2",
    },
    {
        "name": "Trading 212",
        "google_play_package": "com.avuscapital.trading212",
        # Here the bundle ID happens to match the Android package name —
        # a coincidence, not something to assume holds for other apps.
        "apple_bundle_id": "com.avuscapital.trading212",
    },
]

# Unified schema across both platforms. Note this is a 9-field schema, not
# the original 8-field one — "platform" is a new column, added because the
# corpus is no longer single-source. Flag this schema change wherever the
# original 4.2 write-up's field list is quoted.
OUTPUT_SCHEMA = [
    "app",
    "platform",
    "review_id_hash",
    "review_text",
    "rating",
    "review_date",
    "app_version",
    "thumbs_up_count",
    "developer_reply_present",
]

OUTPUT_DIR = "output"
