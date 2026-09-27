"""
Config for Stage 1 (LLM-based classification) — direct Anthropic API version.

This file only holds constants: the taxonomy definition block (identical to
the one used for batches 1-15 in the earlier agent-orchestrated run), the
model ID, batch size, and file paths. Nothing here should need to change
for a normal run — the only things you are likely to edit are the paths at
the bottom, to point at your own local copy of the corpus.
"""

import os

# ---------------------------------------------------------------------------
# Model + run parameters
# ---------------------------------------------------------------------------

# Confirmed against https://platform.claude.com/docs/en/about-claude/models/overview
# on 2026-09-18. This is the SAME model used for batches 1-15, so switching to
# the direct-API path does not change which model performs the classification
# — only how the calls are made.
MODEL_ID = "claude-sonnet-5"

# Reviews per API request. Matches the batch size already used for batches
# 1-15 (batches/batch_001.csv ... batch_015.csv), so batch numbering and the
# existing manifest.json stay valid.
BATCH_SIZE = 300

# Must match the seed used by the original prep_batches.py exactly, or the
# batch numbering will not line up with the already-completed batches 1-15.
SHUFFLE_SEED = 42

# Generous output cap — NOT a cost driver (Anthropic bills only for tokens
# actually generated, not the max_tokens ceiling), just a safety margin so a
# verbose response is never truncated mid-batch.
MAX_TOKENS = 8192

# ---------------------------------------------------------------------------
# Taxonomy — identical to the block used throughout this study
# ---------------------------------------------------------------------------

TAXONOMY_BLOCK = """USABILITY_NAV - Ease or difficulty of learning and operating the interface: layout clarity, findability of features, navigation flow.
ACCOUNT_ACCESS_AUTH - Logging in, password reset, identity verification, device-change lockouts, two-factor friction.
APP_STABILITY_PERFORMANCE - Crashes, freezes, lag, slow loading, or failure to open/respond, independent of any specific feature.
FUNDS_TRANSFER - Linking a bank account, moving money in or out, withdrawal limits or holds, delayed or blocked access to funds.
TRADE_EXECUTION - Accuracy and reliability of order fulfillment: execution price vs quoted price, partial fills, order types, trading restrictions.
CRYPTO_SPECIFIC - Issues or requests specific to crypto trading/custody: transfer failures, staking terms, wallet restrictions, coverage of specific coins.
TRUST_FAIRNESS_REGULATORY - Perceived market manipulation, self-dealing, or unfair treatment framed at the business-model level, not as a discrete bug.
CUSTOMER_SUPPORT - Access to and quality of human support: wait times, chatbot-only loops, unresolved tickets.
CHARTING_TOOLS - Depth and quality of charts, technical indicators, historical data, tools for active/advanced traders.
ONBOARDING_BEGINNER - Suitability for first-time investors: guided experience, explanatory content, learning curve.
FEES_SUBSCRIPTION - Subscription paywalling of features, transfer/withdrawal fees, perceived hidden costs, non-consensual enrollment.
ADVERTISING_NOTIFICATIONS - In-app upsell messaging, marketing notifications, cross-sell prompts, perceived ad density.
PREDICTION_MARKETS - Reactions to the prediction-market/event-contract feature, including "gambling" framing and requests to hide/remove it.
SECURITY_PRIVACY - Account takeover, unauthorized access, or concerns about collection/exposure of personal or biometric data.
ACCOUNT_LIFECYCLE - Opening an account and, separately, closing/deactivating one, including unwanted continuation of an account believed closed.
ASSET_COVERAGE - Requests for additional tradable assets/markets, or complaints about jurisdictional access restrictions.
GENERAL_SENTIMENT - Praise or complaint with no identifiable specific concern (includes garbled/uninterpretable text). Use this when NONE of the 16 substantive categories above apply."""

VALID_CODES = {
    "USABILITY_NAV", "ACCOUNT_ACCESS_AUTH", "APP_STABILITY_PERFORMANCE", "FUNDS_TRANSFER",
    "TRADE_EXECUTION", "CRYPTO_SPECIFIC", "TRUST_FAIRNESS_REGULATORY", "CUSTOMER_SUPPORT",
    "CHARTING_TOOLS", "ONBOARDING_BEGINNER", "FEES_SUBSCRIPTION", "ADVERTISING_NOTIFICATIONS",
    "PREDICTION_MARKETS", "SECURITY_PRIVACY", "ACCOUNT_LIFECYCLE", "ASSET_COVERAGE",
    "GENERAL_SENTIMENT",
}

# ---------------------------------------------------------------------------
# Paths — EDIT THESE to match your machine
# ---------------------------------------------------------------------------

HERE = os.path.dirname(os.path.abspath(__file__))

# Your local copy of the 52,392-row combined corpus from the 4.2 data
# collection step (columns: review_id_hash, app, platform, review_text, ...).
# If you ran the original collect_reviews.py yourself, point this at that
# output file.
CORPUS_CSV = os.path.join(HERE, "combined_reviews.csv")

BATCHES_DIR = os.path.join(HERE, "batches")      # rebuilt locally by the script
RESULTS_DIR = os.path.join(HERE, "results")      # ships with batches 1-15 already in it
MANIFEST_PATH = os.path.join(HERE, "manifest.json")
COMBINED_OUTPUT_CSV = os.path.join(HERE, "stage1_full_corpus_labels.csv")
