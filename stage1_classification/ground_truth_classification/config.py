"""
Config for Step 6 — AI classifier on the remaining ~5,544 ground-truth
reviews (the 6,160-review B4 ground-truth frame minus the 616 already
covered by the reliability subsample in steps 4-5).

This reuses the exact same, already-fixed classify_reviews.py from the
Stage 1 full-corpus run: same model, same taxonomy, same multi-label
format, same verification, and — importantly — the same
"thinking": {"type": "disabled"} fix that was needed after the incident
where Claude Sonnet 5's default-on adaptive thinking silently ate the
entire token budget on batches 1-15's rerun. Nothing about that logic
needed to change; only the input file (this one, not the full corpus) and
output paths differ.
"""

import os

MODEL_ID = "claude-sonnet-5"
BATCH_SIZE = 300
SHUFFLE_SEED = 42
MAX_TOKENS = 8192

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

HERE = os.path.dirname(os.path.abspath(__file__))

# The 5,544 remaining ground-truth reviews (already prepared — this file
# ships with the package, unlike Stage 1 where you pointed it at your own
# corpus copy).
CORPUS_CSV = os.path.join(HERE, "remaining_ground_truth.csv")

BATCHES_DIR = os.path.join(HERE, "batches")
RESULTS_DIR = os.path.join(HERE, "results")
MANIFEST_PATH = os.path.join(HERE, "manifest.json")
COMBINED_OUTPUT_CSV = os.path.join(HERE, "step6_ground_truth_labels.csv")
