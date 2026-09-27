# output/company_updates/

Output of `../../collect_company_updates.py` — see the folder-level README two
levels up for the full picture, including the important caveat that this
scraper's output does **not** appear to be what actually fed BL2/E4 (that used
`../../../bl2_random_forest/build_e1.py`'s separate, simpler output instead).

`sources/` (this folder) holds the raw fetched HTML/JSON, one file per source URL
(keyed by URL hash), preserved for auditing a local run — e.g. tracing a row in
`company_articles.csv` or `feature_candidates.csv` back to the exact page it was
extracted from. Per the parent README, the live company-page crawl in this
packaged run returned an "unavailable placeholder" in its execution environment,
so treat any content here as needing verification against a fresh run on a network
that can actually reach these public sites before relying on it for thesis
citations.
