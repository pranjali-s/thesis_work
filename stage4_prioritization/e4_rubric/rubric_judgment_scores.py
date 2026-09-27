"""
Stage 4 rubric -- live rerun. Actionability + overall_priority + justification,
genuine per-cluster judgment (not a fixed formula), grounded in each cluster's
real title/description/quotes/features. The five other dimensions (reach,
severity, engagement, recency, cross_platform) were computed programmatically
via disclosed percentile/linear formulas in the prior step
(stage4_input_items_live.json) -- this file supplies only the two dimensions
that genuinely require reading the cluster content: actionability, and the
holistic overall_priority judgment (consistent with the original run's
disclosed methodology: overall_priority is a holistic judgment informed by,
not mechanically derived from, the six dimension scores).
"""

# key: (category, cluster_id) -> (actionability, overall_priority, justification)
JUDGMENT = {
("ACCOUNT_ACCESS_AUTH","0"): (9,7,"Specific, severe KYC-waitlist bottleneck that fully blocks trading and withdrawal; fixable via a verification-process change, but reach is modest relative to the largest clusters."),
("ACCOUNT_ACCESS_AUTH","1"): (8,10,"This run's single largest cluster (4,170 reviews), severely rated, and login lockouts are a concrete, fixable authentication-flow problem -- high reach plus high severity plus real actionability."),
("ACCOUNT_LIFECYCLE","0"): (1,1,"Pure positive praise for sign-up speed; no actionable content."),
("ACCOUNT_LIFECYCLE","1"): (8,8,"Specific, severe verification-failure blocker at sign-up; a concrete process fix, sizable reach."),
("ACCOUNT_LIFECYCLE","2"): (9,8,"Severe and highly specific -- accounts closed with no explanation while funds remain trapped; directly actionable as a policy/communication fix."),
("ACCOUNT_LIFECYCLE","3"): (9,8,"Same pattern as /2 for Robinhood -- severe, specific, funds-trapping account restrictions."),
("ACCOUNT_LIFECYCLE","4"): (9,9,"Most severe average rating in this category (1.10); trapped funds plus continued billing is a compounding, clearly fixable failure."),
("ACCOUNT_LIFECYCLE","5"): (8,7,"Missing self-service account deletion is a concrete, scoped feature gap, not just a complaint -- straightforward to action."),
("ADVERTISING_NOTIFICATIONS","0"): (8,7,"Specific, severe complaint about misleading bonus marketing and upsell pressure -- actionable as a marketing/UX policy change."),
("ADVERTISING_NOTIFICATIONS","1"): (6,5,"Real but more diffuse ad/notification frustration, tempered by a minority who like the promos -- moderate severity and actionability."),
("ADVERTISING_NOTIFICATIONS","2"): (8,6,"Concrete request: a reliable notification opt-out. Small reach limits overall priority despite clear actionability."),
("APP_STABILITY_PERFORMANCE","0"): (1,1,"Pure positive praise for stability; no actionable content."),
("APP_STABILITY_PERFORMANCE","1"): (1,1,"Pure positive praise for stability/speed; no actionable content."),
("APP_STABILITY_PERFORMANCE","2"): (9,10,"Severe, specific, high-reach crash/freeze/slowness cluster occurring specifically during active trading -- high-stakes timing makes this urgent and clearly actionable as a performance fix."),
("APP_STABILITY_PERFORMANCE","3"): (9,10,"Severe, specific, high-reach crash-on-launch/post-update breakage -- a concrete regression-testing and stability target."),
("ASSET_COVERAGE","0"): (6,5,"Legitimate but open-ended feature request (broader asset/account coverage); moderate rating means it's a growth opportunity more than a crisis."),
("ASSET_COVERAGE","1"): (8,7,"Specific and severe -- existing users geo-blocked out of accounts they already hold; a concrete policy/eligibility fix."),
("ASSET_COVERAGE","2"): (5,3,"Prospective (non-)users requesting country expansion; real signal but very small reach and speaks to unrealized market, not existing users' pain."),
("ASSET_COVERAGE","3"): (8,6,"Specific sign-up blocker tied to country-of-residence selection; a concrete, scoped fix."),
("CHARTING_TOOLS","0"): (7,4,"Specific, named bug class (chart/graph rendering after updates) but this run's smallest cluster by reach (24 reviews) -- real but low-priority given scale."),
("CHARTING_TOOLS","1"): (8,7,"Specific, sizable cluster -- charts failing to load or freezing is a concrete, testable defect with real reach."),
("CRYPTO_SPECIFIC","0"): (9,9,"Severe, specific, sizable -- funds locked, frozen, or delayed is a core-functionality failure with direct financial impact."),
("CRYPTO_SPECIFIC","1"): (2,1,"Broad positive reception with a beginner-friendly sub-theme; essentially praise, no fix implied."),
("CRYPTO_SPECIFIC","2"): (1,1,"General satisfaction with ease/speed of crypto trading; no actionable content."),
("CRYPTO_SPECIFIC","3"): (2,1,"Loyalty/trust praise driven by an existing rewards program; positive sentiment, not a gap."),
("CRYPTO_SPECIFIC","4"): (2,1,"Praise for the existing Learn-and-Earn program; positive sentiment, not a gap."),
("CUSTOMER_SUPPORT","0"): (8,7,"Specific, severe -- long verification waits and unreachable support, concentrated in Coinbase; concrete staffing/process target, moderate reach."),
("CUSTOMER_SUPPORT","1"): (8,10,"This run's largest single-app-spanning support cluster (4,357 reviews) and severely rated; broad but genuinely actionable via support-process investment (queue times, bot-gating)."),
("FEES_SUBSCRIPTION","0"): (1,1,"Pure positive praise for low/zero commissions; no actionable content."),
("FEES_SUBSCRIPTION","1"): (3,2,"Mostly favorable framing of Coinbase's fee/subscription tradeoff; limited actionable complaint."),
("FEES_SUBSCRIPTION","2"): (9,9,"Severe, specific, sizable -- hidden/stacked fees is a concrete transparency and pricing-disclosure fix, concentrated in Coinbase."),
("FEES_SUBSCRIPTION","3"): (9,7,"Very specific and severe -- unauthorized subscription enrollment is close to a billing-integrity violation, clearly actionable, but smaller reach."),
("FEES_SUBSCRIPTION","4"): (9,8,"Severe, specific -- hidden fees and unauthorized charges spanning two apps; a concrete billing-transparency fix with real reach."),
("FEES_SUBSCRIPTION","5"): (1,1,"Pure positive praise for low fees; no actionable content."),
("FEES_SUBSCRIPTION","6"): (4,3,"Mostly positive coverage of competitive ISA rates, with a minority complaint about post-signup rate cuts; limited scope."),
("FUNDS_TRANSFER","0"): (9,10,"Severe, specific, and this run's largest Funds Transfer cluster by far (3,235 reviews) -- withdrawal holds/freezes/verification loops block access to users' own money, a critical, fixable process failure."),
("FUNDS_TRANSFER","1"): (7,6,"Specific deposit/withdrawal blocking pattern, but scoped to non-English-speaking markets -- real and actionable, narrower reach."),
("FUNDS_TRANSFER","2"): (1,1,"Pure positive praise for fast, hassle-free transfers; no actionable content."),
("GENERAL_SENTIMENT","0"): (1,1,"Terse one-word positive reviews; no actionable content."),
("GENERAL_SENTIMENT","1"): (1,1,"Terse one-word positive reviews; no actionable content."),
("GENERAL_SENTIMENT","2"): (1,1,"Emoji-only positive reactions; no actionable content."),
("GENERAL_SENTIMENT","3"): (2,3,"This run's single largest cluster by review count (7,740), but generic and majority mildly positive -- reach alone doesn't create actionable signal."),
("GENERAL_SENTIMENT","4"): (1,1,"Generic loyalty praise; no actionable content."),
("GENERAL_SENTIMENT","5"): (1,1,"Generic loyalty praise; no actionable content."),
("GENERAL_SENTIMENT","6"): (1,1,"Generic praise for investing success; no actionable content."),
("ONBOARDING_BEGINNER","0"): (2,1,"Praise for Coinbase's educational onboarding; positive sentiment, not a gap."),
("ONBOARDING_BEGINNER","1"): (2,1,"Praise for Robinhood's beginner accessibility; a growth/marketing opportunity, not a pain point."),
("ONBOARDING_BEGINNER","2"): (2,1,"Cross-platform praise for onboarding ease; positive sentiment, not a gap."),
("ONBOARDING_BEGINNER","3"): (2,1,"Praise for the Learn-and-Earn onboarding feature; positive sentiment, not a gap."),
("ONBOARDING_BEGINNER","4"): (1,1,"Broad terse praise for beginner-friendliness; no actionable content."),
("PREDICTION_MARKETS","0"): (5,4,"Genuine split opinion (fun feature vs. gambling concern) -- a real product-positioning question, but moderate severity and this run's smallest-reach prediction-markets cluster relative to /1 and /2."),
("PREDICTION_MARKETS","1"): (9,8,"Severe (1.11 rating) and highly specific -- accusations of rigged or withheld payouts strike at trust in the product's core mechanic; small reach but this run's most recency-skewed cluster (frac_recent_third=1.0), suggesting an emerging, not fading, issue."),
("PREDICTION_MARKETS","2"): (9,7,"Very specific and directly actionable -- forced home-screen placement with no opt-out is a concrete UI/settings fix; small reach but high engagement and recency."),
("SECURITY_PRIVACY","0"): (1,1,"General positive security sentiment; no actionable content."),
("SECURITY_PRIVACY","1"): (6,4,"Mostly positive, but carries a real, specific embedded ask (auto-logout, passkey/authenticator support) worth noting even though the cluster reads positive overall."),
("SECURITY_PRIVACY","2"): (9,8,"Severe and specific -- hacked accounts combined with unresponsive support is a critical security-response gap."),
("SECURITY_PRIVACY","3"): (7,6,"Specific trust friction around onboarding data requests (SSN/ID/bank login); more a policy/communication issue than a single bug, but real and actionable."),
("SECURITY_PRIVACY","4"): (8,7,"Specific verification-flow failure (mandatory face/video selfie locking users out); a concrete fix to the KYC flow."),
("SECURITY_PRIVACY","5"): (9,9,"Severe, specific, and real reach -- drained accounts with no reimbursement is a critical security/fraud-response failure."),
("SECURITY_PRIVACY","6"): (9,6,"The single lowest-rated cluster of all 77 (1.07) -- maximally severe and specific (no support path once locked out or hacked), but this run's smallest Security cluster by reach (30 reviews), which caps its overall priority despite the extreme severity."),
("SECURITY_PRIVACY","7"): (8,6,"Severe and specific -- account recovery blocked after a changed phone/email on file; concrete account-recovery-flow fix, small reach."),
("SECURITY_PRIVACY","8"): (6,6,"Severe but more terse/less-detailed hacked/scam complaints plus a minority phantom-install pattern; real but harder to action from the aggregate description alone."),
("SECURITY_PRIVACY","9"): (9,6,"Severe and specific -- unauthorized withdrawals with no refund path, concentrated in Coinbase; small reach caps overall priority despite the severity."),
("TRADE_EXECUTION","0"): (5,4,"Mostly positive execution experience with open-ended requests for more order types; a feature request, not a fix."),
("TRADE_EXECUTION","1"): (9,10,"Severe, highly specific, and large reach -- blocked trades, slippage, and unreliable stop-losses are core-function failures with direct financial consequences for users."),
("TRUST_FAIRNESS_REGULATORY","0"): (1,1,"Widely positive trust/regulatory sentiment; no actionable content."),
("TRUST_FAIRNESS_REGULATORY","1"): (3,3,"A specific historical grievance (the 2021 GameStop trading restriction) that cannot be fixed prospectively -- real but not actionable as a forward-looking product change."),
("TRUST_FAIRNESS_REGULATORY","2"): (6,7,"Serious, sizable complaint about perceived market manipulation and unfair restrictions, but diffuse -- harder to action with one concrete change than a bug or billing fix."),
("TRUST_FAIRNESS_REGULATORY","3"): (7,8,"Severe, large, and specific enough (scam/theft accusations concentrated on Coinbase) to be actionable via fraud-prevention and communication improvements, even though the underlying trust problem is broad."),
("USABILITY_NAV","0"): (1,1,"Generic 'easy to use' praise; no actionable content."),
("USABILITY_NAV","1"): (1,1,"Generic 'easy to use' praise (lowercase variant); no actionable content."),
("USABILITY_NAV","2"): (1,1,"This run's second-largest cluster by review count (5,239), but pure short praise for overall usability -- reach alone does not create actionable signal."),
("USABILITY_NAV","3"): (9,9,"Severe, specific, and large reach -- a UI/UX update that broke navigation and hid features is directly traceable to a specific release and concretely fixable."),
("USABILITY_NAV","4"): (1,1,"Praise for Coinbase's beginner-friendly usability; no actionable content."),
("USABILITY_NAV","5"): (1,1,"Praise for ease of crypto trading; no actionable content."),
("USABILITY_NAV","6"): (1,1,"Praise for ease of investing/trading across apps; no actionable content."),
("USABILITY_NAV","7"): (1,1,"Praise for Robinhood's usability; no actionable content."),
}

if __name__ == "__main__":
    import json
    with open("/home/claude/fullwriteup/stage4_input_items_live.json") as f:
        items = json.load(f)
    assert len(items) == 77
    missing = []
    for it in items:
        key = (it["category"], it["cluster_id"])
        if key not in JUDGMENT:
            missing.append(key)
    print("missing judgment keys:", missing)
    print("total judged:", len(JUDGMENT))
