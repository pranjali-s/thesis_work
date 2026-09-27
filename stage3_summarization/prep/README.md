# stage3_summarization/prep/

77 per-cluster input files, one per Stage 2 non-noise cluster
(`<CATEGORY>__<cluster_id>.json`), produced by `../prep_clusters.py`. Each file
joins that cluster's review IDs to their full review text, sampling down to 150
reviews (fixed seed 42) for any cluster larger than that, and pre-splitting into
50-review chunks for hierarchical map-then-reduce summarization where needed.

This is the actual data the Stage 3 generation and rating subagents read — useful
for auditing any single roadmap item's title/description/quotes against its real
source reviews. `../prep_manifest.json` is the authoritative index (n_total,
n_sampled, n_chunks per file).

Verified this session: the 77 files' category-prefix counts sum to exactly 77
across all 17 taxonomy categories, matching `stage2_clustering/`'s live 77-cluster
output exactly (ACCOUNT_ACCESS_AUTH: 2, ACCOUNT_LIFECYCLE: 6,
ADVERTISING_NOTIFICATIONS: 3, APP_STABILITY_PERFORMANCE: 4, ASSET_COVERAGE: 4,
CHARTING_TOOLS: 2, CRYPTO_SPECIFIC: 5, CUSTOMER_SUPPORT: 2, FEES_SUBSCRIPTION: 7,
FUNDS_TRANSFER: 3, GENERAL_SENTIMENT: 7, ONBOARDING_BEGINNER: 5,
PREDICTION_MARKETS: 3, SECURITY_PRIVACY: 10, TRADE_EXECUTION: 2,
TRUST_FAIRNESS_REGULATORY: 4, USABILITY_NAV: 8).
