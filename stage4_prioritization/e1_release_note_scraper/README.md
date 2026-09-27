# Company product updates and App Store version notes

A research dataset collector for Coinbase, Robinhood and Trading 212. **There is no default start-date limit.** It follows available company announcement archives and the visible Apple App Store version history through the current UTC date. Source archives are incomplete by nature, so inspect `manifest.json` before claiming historical coverage. The included example data is a checked sample, not a complete record of every update.

## Install and run

Python 3.10+ and network access to the listed public websites are required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python collect_company_updates.py --output output/company_updates
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python collect_company_updates.py --output output/company_updates
```

Optional end date for reproducible analysis, or an optional start date if you later want one:

```bash
python collect_company_updates.py --end 2026-09-24 --output output/as_of_2026_09_24
python collect_company_updates.py --start 2020-01-01 --end 2026-09-24
```

The default scans every discovered article; a full archive may require thousands of sequential HTTP requests. `--max-articles 100` is useful for a short trial but *truncates company coverage* and is recorded as an error. The program sleeps briefly between requests and retries transient responses. It writes source files under `sources/` for auditing. If a source fails, the run returns a nonzero exit status and records the URL and error in `manifest.json`; partial outputs can still be inspected.

## Sources and discovery

| App | Source | What is used |
| --- | --- | --- |
| Robinhood | [Newsroom](https://robinhood.com/us/en/newsroom/), [investor press releases](https://investors.robinhood.com/press-releases) | Visible index links, next-page links, relevant sitemap entries, dated articles. |
| Coinbase | [Blog](https://www.coinbase.com/blog/landing), [blog sitemap](https://www.coinbase.com/sitemap-blog.xml) | Company blog pages and their publication dates. |
| Trading 212 | [What's new community](https://community.trading212.com/c/whats-new/13), [help announcements](https://helpcentre.trading212.com/hc/en-us/sections/33385536291101-Platform-Announcements) | All category pages reachable via Discourse pagination; dated posts from identified company team accounts; help article metadata. |
| All three | Apple [Robinhood US](https://apps.apple.com/us/app/id938003185), [Coinbase US](https://apps.apple.com/us/app/id886427730), [Trading 212 GB](https://apps.apple.com/gb/app/id566325832) | Publicly visible version history; note text and each version's date. |

Trading 212 staff replies in old topics use **their own post dates**. A customer's later reply cannot assign a new product-launch date to an old post. A help article update is logged separately because its edit time does not prove when app behavior changed.

## Output

| File | Interpretation |
| --- | --- |
| `company_articles.csv` | Retrieved company pages and dated staff posts, with full extracted text, publication date and its basis, source URL, retrieval timestamp. |
| `feature_candidates.csv` | Sentences mentioning changes, with timing and audience hints. **Unverified machine candidates**; manually inspect the source before thesis use. |
| `apple_version_history.csv` | All visible version entries, including generic or uninformative notes, with `version_date` and source hashes. |
| `apple_feature_notes.csv` | Only notes that *appear* to name a specific change after generic text filtering. Empty means no defensible feature note was found among visible versions, not that there were no app changes. Human review still required. |
| `help_document_changes.csv` | Help page creation and edit dates; documentation revisions are distinct from feature rollout. |
| `undated_to_review.csv` | Pages for which publication date could not be established. |
| `manifest.json` | Date window, source coverage, Apple visible-history boundaries, counts and errors. |
| `sources/` | Fetched HTML/JSON, keyed by URL hash; preserve for an auditable local run. |

The package includes `verified_examples_no_start_limit_2026-09-24.csv`, with **23 manually checked source-linked examples** from 2024–2026 across all three apps; this is not the script's complete output. The `reference_snapshot_2026-09-24/` folder contains **75 Apple versions** actually obtained on 24 September 2026, spanning the public pages' visible histories. All 75 notes were generic; the accompanying Apple feature-note CSV contains only its header. The live company pages returned an unavailable placeholder to the packaging environment, so no complete company crawl is presented as if it had run. Run the collector on a network able to access those public sites for a larger corpus.

## Reading dates correctly

`publication_date` is the date of a company's article or staff post. `version_date` is the App Store's date for a particular version. `effective_date_if_stated` in the checked examples is populated only where the source explicitly ties availability to a date. These dates can differ: a feature may be announced before beta, rolled out in stages, added to web first, limited by geography or eligibility, or described retrospectively. A dated App Store version is not proof that a particular feature shipped in that version unless its note specifically identifies the change.

For final thesis coding, review candidates and create one row per discrete change with `app`, `feature_name`, `change_type`, `announcement_date`, `actual_rollout_date_if_verified`, `status`, `market`, `source_url` and `researcher_decision`. Avoid inferring a rollout date from an announcement or an undated help page. The archives and Apple visible-history lists can omit older announcements or versions; use the oldest Apple date per app in the manifest as a boundary, not as the first version ever released.

## Validation

Apple HTML parsing was exercised against a live public fetch on 24 September 2026 for all three apps, and against saved source HTML. Company article and Discourse parsing can be checked with local fixtures, but live company crawling remains unverified in this execution environment because those domains return an unavailable placeholder. Site layout, category pagination, and published-date metadata may change; inspect saved pages and the error log if results are unexpectedly sparse.
