# 4.2 Data Collection — Two-Platform Re-Run (Google Play + Apple App Store)

This re-runs data collection for the same three apps (Robinhood, Coinbase,
Trading 212), keeping every original design choice the same — a fixed
24-month trailing window, English-language only, no reviewer-identifying
fields retained — with one deliberate change: reviews are now collected
from **both** the Google Play Store and the **Apple App Store**, not
Google Play alone.

## Revision note: Google Play updated to match

The Google Play side worked from the start (it's a first-party, officially
exposed endpoint, unlike Apple's), but it only ever queried one storefront
(`country="us"`). It's now been brought in line with the Apple side:

- **`scrape_google_play.py` — rewritten.** Now loops over
  `config.GOOGLE_PLAY_STOREFRONTS` (the same five-market list as Apple:
  US/GB/DE/FR/IT) instead of a single hardcoded `"us"`, deduplicates
  reviews across storefronts by hashed ID the same way the Apple side
  does, and applies the language filter (`language_matches`) inside the
  fetch function itself rather than as a separate step in
  `collect_reviews.py` afterward.
- **`review_id_hash` is now namespaced**: `hash_id("google_play", raw_id)`
  instead of `hash_id(raw_id)` — consistent with how the Apple side already
  namespaces its hash, and possible without any caller changes since
  `hash_id` already accepts multiple parts (see the Apple revision note).
- **`app_version` now has a fallback**: reads `reviewCreatedVersion` first
  (the field current versions of `google-play-scraper` actually populate),
  falling back to `appVersion` for older library versions that used that
  key instead. Previously only `appVersion` was read.
- **`config.py`**: `GOOGLE_PLAY_COUNTRY` (singular) replaced by
  `GOOGLE_PLAY_STOREFRONTS`, sourced from the same shared `STOREFRONTS`
  list Apple uses (edit that one list to change coverage for both
  platforms at once). `GOOGLE_PLAY_BATCH_SIZE`/`GOOGLE_PLAY_MAX_BATCHES`
  renamed to `GOOGLE_PLAY_MAX_BATCHES_PER_STOREFRONT` since the cap is now
  per-storefront, not global.
- **`collect_reviews.py`**: dropped the redundant post-hoc
  `is_majority_non_ascii` filter on `gp_rows` — filtering now happens once,
  inside `fetch_google_play_reviews`, matching how the Apple fetch
  function already self-filters.

I could not live-test either scraper end-to-end from this sandbox — its
outbound proxy blocks both `play.google.com` and `itunes.apple.com`
(confirmed with a direct request to each, both returned a 403 from the
proxy itself, not from Google or Apple). Both files are syntax-checked and
the logic mirrors your confirmed-working scripts; worth a real run on your
end to confirm before trusting the output at scale.

## Revision note: the Apple side was rewritten

The first version of this script used the `app_store_scraper` PyPI
package to pull Apple reviews, and it didn't work reliably — that package
targets an unofficial endpoint that has since changed shape. It's been
replaced with an approach confirmed to actually work: plain HTTP requests
(via `requests`) against two of Apple's own endpoints —

1. **iTunes Lookup API** (`itunes.apple.com/lookup`) — documented and
   officially supported — to resolve each app's numeric Apple ID from its
   **bundle ID** (not its Android package name — those aren't always the
   same string; see below).
2. **Apple's public customer-reviews RSS feed**
   (`.../rss/customerreviews/page=N/id=.../sortBy=mostRecent/json`) —
   undocumented but a plain public JSON endpoint, no auth required.

### Everything that changed, file by file

- **`scrape_app_store.py` — fully rewritten.** No longer imports
  `app_store_scraper`. Now: resolves a numeric Apple ID from a bundle ID
  via the Lookup API (`resolve_apple_id`), then paginates the customer-
  reviews RSS feed per storefront, skipping the feed's first "entry" when
  it's the app's own metadata rather than a review (detected by the
  absence of an `im:rating` field), and stops paging a storefront once an
  entire page is older than the cutoff.
- **`config.py`** — `apple_app_id` / `apple_app_name` (hardcoded numeric
  IDs) replaced with `apple_bundle_id` per app. Robinhood and Trading 212's
  bundle IDs are close to their Android package names; **Coinbase's is
  not** — its Apple bundle ID is `com.vilcsak.bitcoin2`, a legacy string
  that looks nothing like `com.coinbase.android`. The old hardcoded-ID
  version would have gotten this wrong the moment that numeric ID ever
  drifted; resolving it live from the bundle ID avoids that. Storefront
  list also changed from an English-speaking-only set (US/GB/AU/CA/IE) to
  a broader five-market set (US/GB/DE/FR/IT) — the language filter, not
  the storefront list, is what actually enforces English-only, so this is
  a coverage choice, not a correctness one. Added `APPLE_ID_LOOKUP_COUNTRIES`,
  `APPLE_ID_LOOKUP_DELAY_SEC` (3.1s, matching Apple's documented ~20
  calls/minute guideline for this API), and `APPLE_PAGES_MAX`.
- **`hashing.py`** — `hash_id` now takes any number of arguments instead
  of exactly one (`hash_id("apple", raw_id)` instead of building the
  composite string by hand everywhere). Backward-compatible: existing
  single-argument calls are unaffected.
- **`language_filter.py`** — added `language_matches(text, lang)`, a thin
  wrapper so the Apple scraper can filter by a language code the same way
  the working script did; `lang="en"` still runs the same non-ASCII
  heuristic as before, `lang="all"` disables filtering.
- **`collect_reviews.py`** — now resolves each app's Apple ID once (via
  `resolve_apple_id`) before fetching its reviews, instead of passing a
  hardcoded ID straight through. Skips an app's App Store collection with
  a clear console warning if resolution fails, rather than failing the
  whole run. Manifest now records `apple_bundle_id` and the resolved
  `apple_id_resolved` instead of a hardcoded numeric ID.
- **`requirements.txt`** — dropped `app-store-scraper` (no longer used)
  and `python-dateutil` (was listed but never actually imported anywhere
  in the code); added `requests`.
- **One field disclosure improved, not worsened**: `app_version` **is**
  available from this RSS feed (`im:version`) — the previous version
  incorrectly assumed it wasn't and always wrote null for Apple rows. That
  limitation is gone. `thumbs_up_count` and `developer_reply_present`
  are still genuinely unavailable via this feed and remain null.
- **One thing kept deliberately, not inherited by accident**: the working
  script you shared always collects "up to now" (only a lower-bound
  cutoff). This project fixes a specific historical window instead, to
  stay comparable to the original Google-Play-only corpus, so
  `fetch_app_store_reviews` also enforces an upper bound (`end_dt`) that
  the source script didn't need.

## Setup

```bash
python -m venv venv
source venv\Scripts\activate 
pip install -r requirements.txt
```

No Apple-specific package is needed anymore — just `requests`.

## Configuration

Everything reproducible about the run lives in `config.py`:

- `COLLECTION_TIMESTAMP` — fixed at **2026-08-15T22:21:42 UTC**, matching
  the original collection's documented initiation time, so the 24-month
  window covers the same review time-range as before even though this
  script is being run again later. If you want a *fresh* window anchored
  to today instead, change this to `datetime.now(timezone.utc)`.
- `WINDOW_MONTHS` — 24, unchanged.
- `APPLE_STOREFRONTS` — which Apple storefronts to pull reviews from
  (default: US, GB, DE, FR, IT).
- `APPLE_ID_LOOKUP_COUNTRIES` / `APPLE_ID_LOOKUP_DELAY_SEC` — used only
  once per app, to resolve a numeric Apple ID from its bundle ID.
- `APPS` — Google Play package name and Apple bundle ID for all three
  apps. Worth a quick spot-check against each app's real App Store/Play
  Store listing before a long run.

## Running it

```bash
python collect_reviews.py
```

This prints, per app: the resolved Apple numeric ID (or a skip warning if
resolution failed), and review counts for each platform. It writes:

- `output/reviews_<app>_google_play.csv`
- `output/reviews_<app>_app_store.csv`
- `output/combined_reviews.csv` — all apps, both platforms, the new corpus
- `output/collection_manifest.json` — run metadata (timestamp, cutoff
  date, resolved Apple IDs, per-app/per-platform counts, duplicate-ID
  check result) for citing in the thesis text, the same role the original
  collection manifest played for 4.2.2/4.2.3.

Then verify it, the same way the original corpus was verified in 4.2.3:

```bash
python verify_corpus.py output/combined_reviews.csv
```

This reports duplicate IDs, per-app/per-platform composition, missing-value
rates by field, residual non-English content, exact-text-duplication rate,
and rating distributions — the same checks 4.2.3 already reports for the
original corpus, so the two are directly comparable.

## Output schema

| Field | Type | Notes |
|---|---|---|
| `app` | string | Robinhood / Coinbase / Trading 212 |
| `platform` | string | `google_play` or `app_store` — **new column vs. the original 8-field schema** |
| `review_id_hash` | string | Pseudonymous; derivation differs by platform (Google Play hashes the API's native review ID; Apple hashes `("apple", feed entry id)`, since the feed exposes no native stable ID) |
| `review_text` | string | Apple's feed returns a single combined content field, so no title/body split is needed on that side |
| `rating` | int | 1–5 |
| `review_date` | ISO 8601 datetime, UTC | |
| `app_version` | string or null | Available for both platforms now — populated for Apple via `im:version` |
| `thumbs_up_count` | int or null | **Always null for `app_store` rows** — not exposed by Apple's feed |
| `developer_reply_present` | bool or null | **Always null for `app_store` rows** — not exposed by Apple's feed |

No reviewer name, username, or profile identifier is retained in either
platform's output, consistent with 4.2.4's ethical/compliance stance.

## Known limitations to carry into the write-up

- **Cross-platform field asymmetry.** `thumbs_up_count` and
  `developer_reply_present` are structural nulls for every Apple row, not
  a missingness *rate* the way the original Google Play `app_version`
  nulls were. Any analysis using those two fields should filter to
  `platform == "google_play"` first, or explicitly note the Apple gap.
- **Apple pseudo-ID basis.** The Apple `review_id_hash` is derived from
  the RSS feed's own `id` field, which is stable across re-fetches for the
  same review but is not a documented, guaranteed-unique Apple identifier
  the way Google Play's `reviewId` is.
- **Apple storefront coverage is a design choice, not a complete
  enumeration.** Five storefronts are queried by default; an
  English-speaking reviewer posting from a non-listed storefront would be
  missed. This mirrors the same kind of scope limitation already disclosed
  for the Google Play collection's self-selection issue in 4.2.5.
- **Window-boundary discrepancy, inherited, not introduced.** The original
  corpus's documented earliest reviews (~2024-08-25/26) land a few days
  after this script's exact calendar cutoff (24 months back from the
  collection timestamp is 2024-08-15). That gap predates this script —
  it's flagged loudly in `collect_reviews.py`'s console output so it gets
  checked against this run's actual results rather than silently
  overwritten either direction.
- **Both endpoints are outside Apple's/Google's stable, versioned public
  API surface** (the Lookup API is documented and stable; the customer-
  reviews RSS feed is not). Expect occasional breakage if Apple changes
  the feed's response format.


#output
  (venv) PS C:\Users\pranj\AI Projects\PranjaliThesis> pip install -r requirements.txt
Collecting google-play-scraper==1.2.7 (from -r requirements.txt (line 1))
  Using cached google_play_scraper-1.2.7-py3-none-any.whl.metadata (50 kB)
Collecting requests==2.32.3 (from -r requirements.txt (line 2))
  Downloading requests-2.32.3-py3-none-any.whl.metadata (4.6 kB)
Collecting charset-normalizer<4,>=2 (from requests==2.32.3->-r requirements.txt (line 2))
  Using cached charset_normalizer-3.5.1-cp314-cp314-win_amd64.whl.metadata (46 kB)
Collecting idna<4,>=2.5 (from requests==2.32.3->-r requirements.txt (line 2))
  Downloading idna-3.20-py3-none-any.whl.metadata (7.2 kB)
Collecting urllib3<3,>=1.21.1 (from requests==2.32.3->-r requirements.txt (line 2))
  Downloading urllib3-2.8.0-py3-none-any.whl.metadata (7.4 kB)
Collecting certifi>=2017.4.17 (from requests==2.32.3->-r requirements.txt (line 2))
  Using cached certifi-2026.7.22-py3-none-any.whl.metadata (2.5 kB)
Using cached google_play_scraper-1.2.7-py3-none-any.whl (28 kB)
Downloading requests-2.32.3-py3-none-any.whl (64 kB)
Using cached charset_normalizer-3.5.1-cp314-cp314-win_amd64.whl (204 kB)
Downloading idna-3.20-py3-none-any.whl (69 kB)
Downloading urllib3-2.8.0-py3-none-any.whl (135 kB)
Using cached certifi-2026.7.22-py3-none-any.whl (136 kB)
Installing collected packages: urllib3, idna, google-play-scraper, charset-normalizer, certifi, requests
Successfully installed certifi-2026.7.22 charset-normalizer-3.5.1 google-play-scraper-1.2.7 idna-3.20 requests-2.32.3 urllib3-2.8.0
(venv) PS C:\Users\pranj\AI Projects\PranjaliThesis> python collect_reviews.py
Collection timestamp (fixed): 2026-08-15T22:21:42+00:00
Window: 24 months -> cutoff 2024-08-15T22:21:42+00:00
Note: the originally documented Google-Play-only corpus reports earliest reviews around 2024-08-25/26, a few days after this window's exact calendar cutoff of 2024-08-15. That's a real, pre-existing gap between the two — sanity-check it against this run's actual earliest review dates rather than assuming either number is wrong.

=== Robinhood ===
  Google Play: 18351 reviews fetched (already language-filtered; dedup'd across storefronts)
  App Store:   resolved bundle 'com.robinhood.release.Robinhood' -> Apple ID 938003185
  App Store:   91 reviews fetched (already language-filtered; dedup'd across storefronts)
=== Coinbase ===
  Google Play: 25158 reviews fetched (already language-filtered; dedup'd across storefronts)
  App Store:   resolved bundle 'com.vilcsak.bitcoin2' -> Apple ID 886427730
  App Store:   1494 reviews fetched (already language-filtered; dedup'd across storefronts)
=== Trading 212 ===
  Google Play: 6572 reviews fetched (already language-filtered; dedup'd across storefronts)
  App Store:   resolved bundle 'com.avuscapital.trading212' -> Apple ID 566325832
  App Store:   726 reviews fetched (already language-filtered; dedup'd across storefronts)

=== Done ===
Combined corpus: 52392 reviews -> output\combined_reviews.csv
Manifest: output\collection_manifest.json
(venv) PS C:\Users\pranj\AI Projects\PranjaliThesis> python verify_corpus.py output/combined_reviews.csv
Loaded 52392 rows from output/combined_reviews.csv

Duplicate (app, platform, review_id_hash) keys: 0

Composition by app x platform:
  Coinbase       app_store      1494  (  2.9%)
  Coinbase       google_play   25158  ( 48.0%)
  Robinhood      app_store        91  (  0.2%)
  Robinhood      google_play   18351  ( 35.0%)
  Trading 212    app_store       726  (  1.4%)
  Trading 212    google_play    6572  ( 12.5%)

Missing-value counts by field:
  app_version                7227 missing ( 13.8%)
  thumbs_up_count            2311 missing (  4.4%)
  developer_reply_present    2311 missing (  4.4%)

Residual majority-non-ASCII reviews after filtering: 0 (0.000% of corpus)

Reviews sharing exact text with another review from the same app: 8306 (15.9%)

Rating distribution by app:
  Coinbase       {'1': 7529, '2': 1089, '3': 856, '4': 1154, '5': 16024}
  Robinhood      {'1': 4745, '2': 778, '3': 952, '4': 1953, '5': 10014}
  Trading 212    {'1': 1328, '2': 335, '3': 449, '4': 856, '5': 4330}
(venv) PS C:\Users\pranj\AI Projects\PranjaliThesis> 
