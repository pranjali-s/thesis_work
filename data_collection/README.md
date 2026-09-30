# data_collection/

Stage 0 of the thesis pipeline (Section 4.2, Data Collection). This folder
scrapes user reviews of three trading/investing apps (**Robinhood**,
**Coinbase**, **Trading 212**) from **Google Play** and the **Apple App
Store**, then filters, pseudonymizes, and writes them to CSV. It covers a
fixed 24-month window and keeps English-language reviews only.

The output, `output/combined_reviews.csv` (52,392 reviews), is the corpus
that every later stage of the thesis reads.

---

## AI model used

**None.** This stage does not use an AI model, LLM, or ML classifier. It
only does the following:

- HTTP scraping: the `google-play-scraper` library for Google Play, and
  plain `requests` calls for Apple.
- Rule-based filtering: date window checks and an ASCII-letter heuristic
  for English (see `language_filter.py`).
- SHA-256 hashing to pseudonymize review IDs.

AI models are used only in later stages (for example Stage 1 classification
and Stage 2 clustering). They are not used here.

---

## Files in this folder

| File | Purpose | Run it directly? |
|---|---|---|
| `collect_reviews.py` | **Main entry point.** For each app it runs both scrapers, writes the per-app/per-platform CSVs, the combined CSV and the run manifest. | ✅ Yes |
| `verify_corpus.py` | Checks data quality after collection: duplicate IDs, app × platform composition, missing values per field, leftover non-English text, exact-text duplicates, and rating distribution. | ✅ Yes |
| `config.py` | **All settings for the run** (timestamp, window, apps, storefronts, rate limits, schema, output folder). Change settings here, not in the scrapers. | No (imported) |
| `scrape_google_play.py` | `fetch_google_play_reviews()` pulls reviews newest-first from each storefront through `google-play-scraper`, then applies the date window, English filter and dedup. | No (imported) |
| `scrape_app_store.py` | `resolve_apple_id()` turns a bundle ID into Apple's numeric app ID using the iTunes Lookup API. `fetch_app_store_reviews()` pages through Apple's public customer-reviews RSS JSON feed for each storefront. | No (imported) |
| `language_filter.py` | English heuristic. A review is dropped if more than 50% of its letters are non-ASCII. `language_matches(text, "en")` wraps this check. | No (imported) |
| `hashing.py` | `hash_id(*parts)` joins the parts with `\|`, takes the SHA-256 hash and keeps the first 24 hex characters. Both scrapers use it to pseudonymize review IDs. | No (imported) |
| `requirements.txt` | Pinned dependencies: `google-play-scraper==1.2.7` and `requests==2.32.3`. | — |
| `bk_README.md` | Backup of an earlier README. It holds the revision history (why the Apple scraper was rewritten, and so on) and a full console log of the real run. | — |
| `output/` | Generated data. See [Output](#output) below. | — |

---

## How to run

### 1. Set up the environment (once)

Tested with Python 3.14 on Windows (PowerShell).

```powershell
cd "data_collection"
python -m venv venv
.\venv\Scripts\Activate.ps1        # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

### 2. Collect the reviews

> **Run from inside `data_collection/`.** `OUTPUT_DIR = "output"` in
> `config.py` is a relative path. If you run the script from another
> folder, it creates a new `output/` folder there.

```powershell
python collect_reviews.py
```

The full run takes several minutes because of the request delays. The
console shows the fixed timestamp and cutoff, and for each app it shows the
Google Play count, the resolved Apple ID and the App Store count. If an
app's Apple ID cannot be resolved, the script skips that app's App Store
reviews with a warning and does not fail the whole run.

**Warning:** running it again **overwrites** everything in `output/`. The
data comes from live stores, so a new run will not reproduce the exact
52,392 rows. Stores delete reviews, and Apple's RSS feed only reaches back
a limited number of pages. Back up `output/` before you run it again.

### 3. Verify the corpus

```powershell
python verify_corpus.py                                # defaults to output/combined_reviews.csv
python verify_corpus.py path\to\other_reviews.csv      # or pass any CSV with the same schema
```

This only prints to the console. It does not write any files.

---

## Default configuration (`config.py`)

| Setting | Default | Meaning |
|---|---|---|
| `COLLECTION_TIMESTAMP` | `2026-08-15 22:21:42 UTC` | Fixed end of the window. It matches the start time of the original Google-Play-only collection, so a re-run covers the same time range. Set it to `datetime.now(timezone.utc)` if you want a fresh window. |
| `WINDOW_MONTHS` | `24` | Window length, counted back in calendar months, so the cutoff is **2024-08-15 22:21:42 UTC**. |
| `STOREFRONTS` | `["us", "gb", "de", "fr", "it"]` | Country storefronts searched, the same for **both** platforms. This controls where the scripts look for reviews. The English filter decides which reviews are kept. |
| `GOOGLE_PLAY_LANG` | `"en"` | Language sent in the request and used by the filter. `"all"` turns the English filter off. |
| `GOOGLE_PLAY_BATCH_SIZE` | `200` | Reviews per Google Play request. |
| `GOOGLE_PLAY_MAX_BATCHES_PER_STOREFRONT` | `2000` | Safety cap. Pagination normally stops sooner, when a whole page is older than the cutoff or there is no continuation token. |
| `GOOGLE_PLAY_REQUEST_DELAY_SEC` | `0.5` | Pause between Google Play requests. |
| `APPLE_PAGES_MAX` | `10` | Maximum RSS pages per storefront, with up to 50 reviews per page. Apple's feed does not go deeper than this. |
| `APPLE_REQUEST_DELAY_SEC` | `0.25` | Pause between Apple RSS requests. |
| `APPLE_ID_LOOKUP_COUNTRIES` | `["us", "gb", "de", "ca", "au"]` | Countries tried in order when resolving a bundle ID. |
| `APPLE_ID_LOOKUP_DELAY_SEC` | `3.1` | Keeps requests under Apple's guideline of about 20 Lookup calls per minute. |
| `OUTPUT_DIR` | `"output"` | Folder the CSVs and manifest are written to, relative to the working directory. |

### Apps

| App | Google Play package | Apple bundle ID | Resolved Apple ID |
|---|---|---|---|
| Robinhood | `com.robinhood.android` | `com.robinhood.release.Robinhood` | 938003185 |
| Coinbase | `com.coinbase.android` | `com.vilcsak.bitcoin2` (legacy bundle ID) | 886427730 |
| Trading 212 | `com.avuscapital.trading212` | `com.avuscapital.trading212` | 566325832 |

---

## Processing steps (per app, per platform)

1. **Fetch** reviews newest-first from each storefront.
2. **Window filter:** keep a review only if `cutoff ≤ review date ≤ COLLECTION_TIMESTAMP`. A storefront stops paging once a whole page is older than the cutoff.
3. **English filter:** drop reviews where more than 50% of the letters are non-ASCII.
4. **Pseudonymize:** `review_id_hash = hash_id("google_play", reviewId)` or `hash_id("apple", feed_entry_id)`.
5. **Deduplicate** across storefronts using that hash.
6. **Drop reviewer-identifying fields.** No username, profile or avatar is kept.
7. After all apps are done, **check for duplicate** `(app, platform, review_id_hash)` keys and record the count in the manifest.

---

## Output

Everything is written to **`data_collection/output/`**:

| File | Size | Contents |
|---|---|---|
| `combined_reviews.csv` | ~10.4 MB | **The corpus.** All 3 apps × both platforms, 52,392 rows. Used by every downstream stage. |
| `collection_manifest.json` | ~1 KB | Run metadata: collection timestamp, window, cutoff date, and for each app the package or bundle ID, resolved Apple ID and review counts per platform, plus `duplicate_ids_found` and `total_reviews`. Cite it in the thesis write-up. |
| `reviews_robinhood_google_play.csv` | ~3.7 MB | 18,351 rows |
| `reviews_robinhood_app_store.csv` | ~27 KB | 91 rows |
| `reviews_coinbase_google_play.csv` | ~4.8 MB | 25,158 rows |
| `reviews_coinbase_app_store.csv` | ~338 KB | 1,494 rows |
| `reviews_trading_212_google_play.csv` | ~1.3 MB | 6,572 rows |
| `reviews_trading_212_app_store.csv` | ~210 KB | 726 rows |
| `README.md` | — | Short description of the output folder. |

Per-app file names follow `reviews_<app name, lowercase, spaces → _>_<platform>.csv`.

### Current corpus at a glance (from `collection_manifest.json` and `verify_corpus.py`)

| App | Google Play | App Store | Total |
|---|---:|---:|---:|
| Robinhood | 18,351 | 91 | 18,442 |
| Coinbase | 25,158 | 1,494 | 26,652 |
| Trading 212 | 6,572 | 726 | 7,298 |
| **All** | **50,081** | **2,311** | **52,392** |

- Duplicate IDs: **0**
- Leftover non-English reviews: **0**
- Reviews whose exact text also appears in another review of the same app: 8,306 (15.9%), mostly short texts such as "good app".
- Review dates run from 2024-08-15 to 2026-08-15. The earliest App Store review is later for each app: Robinhood 2024-08-28, Coinbase 2024-08-19, Trading 212 2024-08-16.

### CSV schema (all 8 CSVs, 9 columns)

| Column | Type | Notes |
|---|---|---|
| `app` | string | `Robinhood`, `Coinbase` or `Trading 212` |
| `platform` | string | `google_play` or `app_store` |
| `review_id_hash` | string (24 hex) | Pseudonymous ID. The hash input includes the platform name. |
| `review_text` | string | Review body. Apple's feed has one content field, so there is no separate title. |
| `rating` | int | 1–5 stars |
| `review_date` | ISO 8601 datetime | Google Play dates are UTC (`+00:00`). **App Store dates keep Apple's feed offset** (for example `-07:00`). Convert to UTC before comparing across platforms. |
| `app_version` | string / empty | Google Play: `reviewCreatedVersion`. Apple: `im:version`. Empty for 7,227 rows (13.8%). |
| `thumbs_up_count` | int / empty | **Always empty for `app_store` rows** because Apple's feed does not provide it. |
| `developer_reply_present` | bool / empty | **Always empty for `app_store` rows** because Apple's feed does not provide it. |

---

## Known limitations

- **Field gaps between platforms:** `thumbs_up_count` and
  `developer_reply_present` exist only for Google Play. Filter to
  `platform == "google_play"` before analysing them.
- **App Store coverage is thin**, about 4% of the corpus. Apple's RSS feed
  only returns about 10 pages × 50 reviews per storefront, and it reaches
  back only so far.
- **Apple ID basis:** the Apple hash comes from the RSS feed's own entry
  `id`. That value is stable, but Apple does not document it as a review
  identifier.
- **The English filter is a heuristic**, not a language classifier. Text in
  other Latin-script languages that is mostly ASCII (for example French or
  Italian without many accents) can get through.
- **Storefront list is a design choice:** only 5 storefronts are queried.
  English reviews posted in other storefronts are missed.
- **Endpoint stability:** Apple's customer-reviews RSS feed is undocumented,
  and `google-play-scraper` uses Google's internal endpoint. Either can
  break without notice.

The console log of the real run are in
`real_run_output.txt`.
