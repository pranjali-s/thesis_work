"""
E1 -- real release-note dataset, live collection (this session, 2026-09-24).

REBUILT NOTICE: the original e1_final.py script and its 156-row output
(e1_release_notes.csv) no longer exist in any reachable workspace (same
loss documented for Stage 2/BL1). This is a fresh, live collection run
against the same three real sources the original methodology used:
  - Trading 212: the community forum's "What's new" category, via its
    real Discourse JSON API (community.trading212.com/c/whats-new.json,
    paginated).
  - Robinhood: the newsroom (robinhood.com/us/en/newsroom) plus targeted
    fetches of individual articles found via search, since the newsroom's
    listing page does not paginate by URL parameter in this session
    (client-side rendered) and its sitemap's <lastmod> is a crawl
    timestamp, not a publish date -- exactly the "listing pages are
    JS-paginated and unusable... plus per-article date extraction"
    limitation the original E1_status.md already disclosed.
  - Coinbase: the blog (coinbase.com/blog and its "product" landing page),
    plus targeted fetches of individual articles found via search.

Every row below was fetched live in this session; every date and
description is taken directly from the fetched page, not invented. This
collection is NOT claimed to be exhaustive -- see the disclosed coverage
notes at the bottom of this file and in E1_LIVE_RUN_LOG.md. In particular:
  - Trading 212's "What's new" category was paginated to exhaustion (page 4
    returned zero topics), so this IS the complete category: 94 topics,
    matching the original run's count exactly.
  - Robinhood and Coinbase are NOT exhaustive: only articles that surfaced
    via the newsroom/blog listing pages and a handful of targeted searches
    were collected, not a full historical crawl. This is a real, disclosed
    gap, in the same spirit as the original run's own disclosed Coinbase
    gaps (E1_status.md).
"""
import csv
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

WINDOW_START = "2024-06-01"
WINDOW_END = "2026-09-24"  # today, in this session

rows = []

def add(app, title, url, date, description, source_method):
    rows.append({
        "app": app, "title": title, "url": url, "publish_date": date,
        "description": description, "source_method": source_method,
        "in_corpus_window": WINDOW_START <= date <= WINDOW_END,
    })

# ============================================================ TRADING 212
# Live-fetched from community.trading212.com/c/whats-new.json, paginated
# page=0..4 (page=4 returned an empty topics array -- confirmed exhaustive).
# Dates are the topic's created_at from the Discourse API, truncated to date.
T212_TOPICS = [
    # (title, slug, created_at) -- page 0
    ("Trading 212 API Update \U0001F6E0️", "trading-212-api-update", "2025-10-01"),
    ("Introducing the new AI Chatbot \U0001F916", "introducing-the-new-ai-chatbot", "2026-04-03"),
    ("Portfolio transfers", "portfolio-transfers", "2023-12-29"),
    ("\U0001F1E9\U0001F1EA Big news for German residents!", "big-news-for-german-residents", "2025-01-13"),
    ("100,000 reviews on Trustpilot \U0001F389", "100-000-reviews-on-trustpilot", "2026-08-12"),
    ("\U0001F4B3 The 212 card spending pot is here!", "the-212-card-spending-pot-is-here", "2025-03-07"),
    ("\U0001F1EC\U0001F1E7 130+ new AIM stocks now available", "130-new-aim-stocks-now-available", "2026-01-21"),
    ("\U0001F5D3️ Single-stock AutoInvest is here", "single-stock-autoinvest-is-here", "2026-05-22"),
    ("The Trading 212 SIPP is now live for everyone in the UK \U0001F4BC", "the-trading-212-sipp-is-now-live-for-everyone-in-the-uk", "2026-06-24"),
    ("Ready for takeoff? SpaceX has launched on Trading 212! \U0001F680", "ready-for-takeoff-spacex-has-launched-on-trading-212", "2026-06-12"),
    ("Trading 212's API can now integrate with AI \U0001F916", "trading-212s-api-can-now-integrate-with-ai", "2026-02-04"),
    ("Investing in newly listed IPOs just got easier!", "investing-in-newly-listed-ipos-just-got-easier", "2026-06-10"),
    ("We revolutionised investing. Now it's time for pensions!", "we-revolutionised-investing-now-its-time-for-pensions", "2026-05-15"),
    ("\U0001F4B3 Introducing the 212 Card", "introducing-the-212-card", "2024-02-12"),
    ("Introducing Privacy Mode \U0001F440", "introducing-privacy-mode", "2026-04-07"),
    ("The old new portfolio look is now live!", "the-old-new-portfolio-look-is-now-live", "2026-01-12"),
    ("The 212 card is now available to all UK residents!", "the-212-card-is-now-available-to-all-uk-residents", "2024-04-23"),
    ("New Equity Trading API in Beta - Try it Out in Practice Mode!", "new-equity-trading-api-in-beta-try-it-out-in-practice-mode", "2023-04-28"),
    ("Portfolio Redesign Update", "portfolio-redesign-update", "2025-12-24"),
    ("Fund your account via Open Banking \U0001F4B8", "fund-your-account-via-open-banking", "2020-10-09"),
    ("\U0001F3E0 Your home screen just got a new look!", "your-home-screen-just-got-a-new-look", "2025-09-23"),
    ("Introducing 212 Crypto!", "introducing-212-crypto", "2025-10-06"),
    ("⚠️ Cloudflare outage", "cloudflare-outage", "2025-12-05"),
    ("\U0001F30A Earn 1.5% cashback this summer!", "earn-1-5-cashback-this-summer", "2024-05-07"),
    ("CFDs have a new look - a redesigned order screen, cleaner interface, and more…", "cfds-have-a-new-look-a-redesigned-order-screen-cleaner-interface-and-more", "2025-11-05"),
    ("⚙️ Upcoming crypto maintenance", "upcoming-crypto-maintenance", "2025-10-23"),
    ("Introducing multi-currency support to Trading 212 Invest", "introducing-multi-currency-support-to-trading-212-invest", "2023-06-16"),
    ("A new layer of growth. Figma goes public!", "a-new-layer-of-growth-figma-goes-public", "2025-07-31"),
    ("\U0001F4C8 Improved pie performance metrics (MWRR & more)", "improved-pie-performance-metrics-mwrr-more", "2024-10-24"),
    ("About the \U0001F4F0 What's new category", "about-the-whats-new-category", "2020-02-06"),
    # page 1
    ("Improved portfolio screen - Better return calculations (MWRR), Cash widget, and more!", "improved-portfolio-screen-better-return-calculations-mwrr-cash-widget-and-more", "2025-01-03"),
    ("\U0001F4CA Introducing our brand new Sankey diagrams", "introducing-our-brand-new-sankey-diagrams", "2024-10-03"),
    ("Huge milestone achieved! \U0001F31F", "huge-milestone-achieved", "2025-05-22"),
    ("\U0001F4E2 Value orders for CFDs are here", "value-orders-for-cfds-are-here", "2025-04-29"),
    ("\U0001F967 Ready-made pies are here!", "ready-made-pies-are-here", "2024-07-10"),
    ("Asset allocation update - now a Treemap", "asset-allocation-update-now-a-treemap", "2024-10-24"),
    ("In-specie transfer \U0001F468‍\U0001F52C", "in-specie-transfer", "2022-04-15"),
    ("Introducing Privacy mode - now available on Web", "introducing-privacy-mode-now-available-on-web", "2021-11-03"),
    ("\U0001F967 Introducing spare change and cashback investing!", "introducing-spare-change-and-cashback-investing", "2024-12-17"),
    ("\U0001F4B3 Goodbye FX fee", "goodbye-fx-fee", "2024-12-02"),
    ("\U0001F4B3 Apple Pay is now available to all EU clients!", "apple-pay-is-now-available-to-all-eu-clients", "2024-12-10"),
    ("Withdrawal process - redesigned", "withdrawal-process-redesigned", "2022-02-18"),
    ("\U0001F4B3 Introducing Apple Pay", "introducing-apple-pay", "2024-05-28"),
    ("The 212 Cash ISA is now live! \U0001F525", "the-212-cash-isa-is-now-live", "2024-05-21"),
    ("\U0001F525 Extended hours trading is going 24/5!", "extended-hours-trading-is-going-24-5", "2024-02-14"),
    ("\U0001F998 Australia, we are here!", "australia-we-are-here", "2024-02-20"),
    ("Trading 212 now features the world's most advanced charts - TradingView", "trading-212-now-features-the-world-s-most-advanced-charts-tradingview", "2022-08-05"),
    ("\U0001F680 Complete overhaul of General info, Stats and Financials!", "complete-overhaul-of-general-info-stats-and-financials", "2024-08-30"),
    ("2023 in review: Everything we delivered! \U0001F381", "2023-in-review-everything-we-delivered", "2023-12-28"),
    ("\U0001F4F1 Advanced charts on mobile just got better", "advanced-charts-on-mobile-just-got-better", "2024-06-25"),
    ("Introducing Logged-in Devices", "introducing-logged-in-devices", "2022-03-11"),
    ("New feature - View-only Instruments", "new-feature-view-only-instruments", "2023-04-28"),
    ("\U0001F4B3 Introducing Google Pay", "introducing-google-pay", "2024-07-01"),
    ("\U0001F4B0 Introducing daily interest on cash!", "introducing-daily-interest-on-cash", "2023-06-06"),
    ("\U0001F4C8 Earn 5.2% APY on your pounds!", "earn-5-2-apy-on-your-pounds", "2024-02-28"),
    ("The 212 Cash ISA is coming in May", "the-212-cash-isa-is-coming-in-may", "2024-04-08"),
    ("New feature - Export your investing history", "new-feature-export-your-investing-history", "2021-01-08"),
    ("New Web App (Beta)", "new-web-app-beta", "2024-03-13"),
    ("New Community Layout", "new-community-layout", "2023-02-21"),
    ("\U0001F4C8 Now available: EVEN higher interest on uninvested cash!", "now-available-even-higher-interest-on-uninvested-cash", "2023-12-22"),
    # page 2
    ("\U0001F680 Reddit IPO - now available", "reddit-ipo-now-available", "2024-03-21"),
    ("\U0001F1E8\U0001F1E6 Toronto Stock Exchange is live", "toronto-stock-exchange-is-live", "2023-12-20"),
    ("New Stock Exchange: Euronext Lisbon \U0001F1F5\U0001F1F9", "new-stock-exchange-euronext-lisbon", "2022-11-04"),
    ("Birkenstock IPO - now available \U0001F463", "birkenstock-ipo-now-available", "2023-10-11"),
    ("Arm Holdings IPO - now available \U0001F9BE", "arm-holdings-ipo-now-available", "2023-09-14"),
    ("Extended market hours prices now available", "extended-market-hours-prices-are-now-available-on-invest-and-isa", "2023-03-23"),
    ("Instacart IPO - now available for trading \U0001F955", "instacart-ipo-now-available-for-trading", "2023-09-19"),
    ("2-Factor Authentication Released!", "2-factor-authentication-released", "2020-10-13"),
    ("Get free shares by sharing your pies", "get-free-shares-by-sharing-your-pies", "2020-10-29"),
    ("Invest & ISA - Account Funding Conditions Update", "invest-isa-account-funding-conditions-update", "2020-12-23"),
    ("Live Chat Maintenance", "live-chat-maintenance", "2023-06-02"),
    ("New feature - Annual statement export", "new-feature-annual-statement-export", "2023-04-03"),
    ("New feature - AutoInvest now works with bank transfers!", "new-feature-autoinvest-now-works-with-bank-transfers", "2022-05-20"),
    ("Introducing - Last Trade Price", "introducing-last-trade-price", "2022-11-09"),
    ("UK registrations - OPEN", "uk-registrations-open", "2022-08-30"),
    ("AutoInvest - Join the BETA", "autoinvest-join-the-beta", "2020-05-18"),
    ("New \"System theme\" \U0001F4F2", "new-system-theme", "2023-01-11"),
    ("Warrants are now here \U0001F4DC", "warrants-are-now-here", "2022-06-23"),
    ("Stock distribution is Now Available", "stock-distribution-is-now-available", "2021-10-22"),
    ("Leaked Password - Proactive Checking", "leaked-password-proactive-checking", "2022-03-29"),
    ("Pies - Import / Export investments", "pies-import-export-investments", "2020-08-26"),
    ("Web App - Advanced View", "web-app-advanced-view", "2021-01-22"),
    ("New Web App for Invest & ISA", "new-web-app-for-invest-isa", "2020-09-08"),
    ("Company fundamentals", "company-fundamentals", "2020-02-06"),
    ("Introducing Communities", "introducing-communities", "2021-04-16"),
    ("Introducing Linked Pies", "introducing-linked-pies", "2021-03-10"),
    ("Become a beta tester of the Trading 212 iOS app", "become-a-beta-tester-of-the-trading-212-ios-app", "2020-08-26"),
    ("Searching Stocks by ISIN now possible!", "searching-stocks-by-isin-now-possible", "2020-11-17"),
    ("Investment Return Breakdown", "investment-return-breakdown", "2020-08-14"),
    ("No more minimum pending distance requirements", "no-more-minimum-pending-distance-requirements", "2020-08-10"),
    # page 3 (final page -- page 4 was empty)
    ("View sell price before buying", "view-sell-price-before-buying", "2020-07-10"),
    ("Sell price on Invest accounts", "sell-price-on-invest-accounts", "2020-03-02"),
    ("Value orders - Launched \U0001F680", "value-orders-launched", "2020-06-01"),
    ("Value orders - join the BETA", "value-orders-join-the-beta", "2020-05-07"),
]
for title, slug, date in T212_TOPICS:
    add("Trading 212", title, f"https://community.trading212.com/t/{slug}", date,
        title, "discourse_json_api_paginated")

# ============================================================ ROBINHOOD
# Live-fetched: newsroom listing (10 most recent) + targeted article
# fetches found via search, each individually confirmed for real
# publish date and content.
ROBINHOOD_ITEMS = [
    ("Robinhood Ventures Fund I (RVI) Invests $25M in Crusoe", "https://robinhood.com/us/en/newsroom/rvi-crusoe", "2026-09-17",
     "Robinhood Ventures Fund I announced a $25M investment in Crusoe."),
    ("Robinhood Canada Celebrates the Opening of its Toronto Office", "https://robinhood.com/us/en/newsroom/robinhood-canada-celebrates-opening-of-toronto-office", "2026-09-16",
     "Robinhood Canada opened a new office in Toronto."),
    ("Robinhood Teams Up With Crypto.com and OG.com to Expand Access to Prediction Markets", "https://robinhood.com/us/en/newsroom/robinhood-cryptocom", "2026-09-08",
     "Robinhood partnered with Crypto.com and OG.com to expand prediction-markets access ahead of the fall."),
    ("Robinhood Ventures Fund II (RVII) Announces Pricing of Initial Public Offering", "https://robinhood.com/us/en/newsroom/rvii-final-pricing", "2026-08-13",
     "Robinhood Ventures Fund II priced its IPO."),
    ("Robinhood Launches Crypto Trading for UK Investors", "https://robinhood.com/us/en/newsroom/robinhood-launches-crypto-trading-for-uk-investors", "2026-08-10",
     "Robinhood launched crypto trading for UK-based investors."),
    ("Robinhood Presents: HOOD Summit '26 - Engines of Creation", "https://robinhood.com/us/en/newsroom/robinhood-presents-hood-summit-26-engines-of-creation", "2026-08-10",
     "Robinhood previewed its HOOD Summit 2026 event."),
    ("Robinhood Ventures Fund I (RVI) Invests $30 Million in Whatnot", "https://robinhood.com/us/en/newsroom/RVI-Whatnot", "2026-08-07",
     "Robinhood Ventures Fund I invested $30M in Whatnot."),
    ("Introducing Robinhood Ventures Fund II (RVII)", "https://robinhood.com/us/en/newsroom/introducing-rvii", "2026-08-03",
     "Robinhood announced its second Ventures Fund."),
    ("Robinhood Reports Second Quarter 2026 Results", "https://robinhood.com/us/en/newsroom/robinhood-reports-second-quarter-2026-results", "2026-07-29",
     "Robinhood's Q2 2026 earnings report."),
    ("The Robinhood Ventures Fund II (RVII) IPO Roadshow Begins August 3", "https://robinhood.com/us/en/newsroom/rvii-roadshow", "2026-07-27",
     "Announcement of the RVII IPO roadshow start date."),
    ("Robinhood Unveils Powerful New Tools for Active Traders at HOOD Summit 2025", "https://robinhood.com/us/en/newsroom/hood-summit-2025-news/", "2025-09-10",
     "Robinhood Social (verified trading community), AI-powered custom indicators/scanners, futures trading on Legend, and enhanced mobile trading (short selling, overnight Index Options)."),
    ("Introducing Robinhood Strategies, Robinhood Banking, and Robinhood Cortex", "https://robinhood.com/us/en/newsroom/introducing-strategies-banking-and-cortex/", "2025-03-27",
     "Robinhood Strategies (capped-fee advisor service), Robinhood Banking (premium banking features), and a preview of Robinhood Cortex (AI market-analysis tool)."),
    ("The Legend Awakens: Introducing Robinhood Legend, Futures Trading, and Index Options", "https://robinhood.com/us/en/newsroom/the-legend-awakens/", "2024-10-16",
     "Robinhood Legend (desktop platform), futures trading, and index options support for active traders."),
    ("Introducing the Presidential Election Market", "https://robinhood.com/us/en/newsroom/introducing-the-presidential-election-market/", "2024-10-28",
     "Presidential election event contracts on Robinhood's derivatives platform, priced $0.02-$0.99."),
    ("Robinhood Launches the Lowest Margin Rates Among Leading Brokerages", "https://robinhood.com/us/en/newsroom/new-robinhood-margin-rates/", "2024-05-21",
     "Tiered margin rate structure, 5.7%-6.75%, adjusting automatically with account margin balance."),
    ("Introducing Robinhood Advanced Charts", "https://robinhood.com/us/en/newsroom/introducing-robinhood-advanced-charts/", "2022-08-17",
     "Advanced charting tools with technical indicators for all users (pre-window; included for completeness)."),
]
for title, url, date, desc in ROBINHOOD_ITEMS:
    add("Robinhood", title, url, date, desc, "newsroom_listing_plus_targeted_search")

# ============================================================ COINBASE
# Live-fetched: blog listing + "product" landing page + targeted article
# fetches for two feature-relevant items found via search.
COINBASE_ITEMS = [
    ("You can now participate in IPOs on Coinbase", "https://www.coinbase.com/blog", "2026-09-21", "IPO participation feature on Coinbase.", "blog_listing"),
    ("Consumer Protection Tuesday: Taking Down Evil Tokens", "https://www.coinbase.com/blog", "2026-09-22", "Consumer-protection blog series entry.", "blog_listing"),
    ("Autopilot: engineering an agentic quality loop for support automation", "https://www.coinbase.com/blog", "2026-09-21", "Engineering post on an AI support-automation tool.", "blog_listing"),
    ("Coinbase and Stablecore bring stablecoin and digital asset services to community and regional banks and credit unions", "https://www.coinbase.com/blog", "2026-09-16", "Partnership expanding stablecoin services to community/regional banks.", "blog_listing"),
    ("We're lowering fees for many active traders on Coinbase Advanced", "https://www.coinbase.com/blog", "2026-09-16", "Fee reduction for active traders on Coinbase Advanced.", "blog_listing"),
    ("Consumer Protection Tuesday: AI-Powered Continuous Adversarial Testing at Coinbase", "https://www.coinbase.com/blog", "2026-09-15", "Security/testing blog post.", "blog_listing"),
    ("Coinbase brings stablecoin payments and custody to community banks and credit unions, in partnership with Moov", "https://www.coinbase.com/blog", "2026-09-10", "Stablecoin payments/custody partnership with Moov.", "blog_listing"),
    ("Coinbase and Morpho bring USDC earning to Brazil and Canada", "https://www.coinbase.com/blog", "2026-09-09", "USDC-earning feature expansion to Brazil and Canada.", "blog_listing"),
    ("How Coinbase Design Systems Are Powering the AI Prototyping Era", "https://www.coinbase.com/blog", "2026-09-09", "Design-systems engineering post.", "blog_listing"),
    ("Getting paid in crypto just got a lot more powerful with Coinbase Business", "https://www.coinbase.com/blog", "2026-08-11", "Coinbase Business payment features.", "blog_listing"),
    ("Coinbase launches a new matching engine, upgrading its derivatives platform with ultra-low latency and deep liquidity", "https://www.coinbase.com/blog/landing/product", "2026-08-12", "New low-latency matching engine for Coinbase's derivatives platform.", "blog_product_landing"),
    ("Coinbase Q2 Earnings: Everything Exchange Drives 3rd Consecutive Quarter of Record Crypto Trading Volume", "https://www.coinbase.com/blog", "2026-07-30", "Q2 2026 earnings report.", "blog_listing"),
    ("Pre-IPOs Are Launching on Coinbase, Starting with SpaceX", "https://www.coinbase.com/blog", "2026-06-03", "Pre-IPO trading feature launch, starting with SpaceX.", "blog_listing"),
    ("Coinbase Partners with MassPay to Unlock Cross-Border Stablecoin Payouts for Global Enterprises", "https://www.coinbase.com/blog/landing/product", "2026-06-11", "Cross-border stablecoin payout partnership with MassPay.", "blog_product_landing"),
    ("Coinbase Payments: A Complete Solution for Stablecoin Payments", "https://www.coinbase.com/blog/landing/product", "2026-06-09", "Launch of Coinbase Payments product.", "blog_product_landing"),
    ("Coinbase Brings Global Crypto Derivatives to US Market", "https://www.coinbase.com/blog", "2026-05-29", "Global crypto derivatives now available in the US.", "blog_listing"),
    ("Coming June 14: Perpetual-Style Equity Index Futures", "https://www.coinbase.com/blog", "2026-05-21", "Announcement of upcoming perpetual-style equity index futures.", "blog_listing"),
    ("Coinbase powers USDF: Flipcash's Custom Stablecoin", "https://www.coinbase.com/blog/landing/product", "2026-05-20", "Infrastructure partnership for a third-party stablecoin.", "blog_product_landing"),
    ("Coinbase Q1 Financial Results Show Resilient Financial Performance", "https://www.coinbase.com/blog", "2026-05-07", "Q1 2026 earnings report.", "blog_listing"),
    ("Coinbase Powers the First Crypto-Backed, Conforming Mortgages by Better", "https://www.coinbase.com/blog", "2026-03-26", "Crypto-backed mortgage product partnership with Better.", "blog_listing"),
    ("Coinbase Australia Receives AFSL Licence", "https://www.coinbase.com/blog", "2026-04-07", "Regulatory licensing news for Coinbase Australia.", "blog_listing"),
    ("Coinbase Receives Conditional OCC Approval: Building the Future of Finance", "https://www.coinbase.com/blog", "2026-04-02", "Regulatory approval news (OCC).", "blog_listing"),
    ("System Update: Take Control of Your Money with Coinbase", "https://www.coinbase.com/blog/system-update-take-control-of-your-money-with-coinbase", "2026-06-16", "Product-update event announcement."),
    ("System Update: The future of finance is on Coinbase", "https://www.coinbase.com/blog/system-update-the-future-of-finance-is-on-coinbase", "2025-12-17",
     "Major platform expansion: stock trading, prediction markets, simplified futures trading, Solana DEX integration, an AI-powered advisor tool, Coinbase Business general availability, and global Base App availability (140+ countries)."),
    ("How We Are Making Coinbase Easier to Use", "https://www.coinbase.com/blog/how-we-are-making-coinbase-easier-to-use", "2025-08-14",
     "Four account-restriction/verification improvements rolling out Q3/Q4 2025: automated in-app Enhanced Due Diligence, voice support with activity logs, compliance automation, and new security options (Consensus 2FA, Time Delay) to reduce false-positive lockouts."),
    ("Create your own stablecoin with Coinbase", "https://www.coinbase.com/blog", "2025-12-18", "Stablecoin-creation tooling for businesses.", "blog_listing"),
    ("The next wave of Coinbase One onchain benefits", "https://www.coinbase.com/blog/landing/product", "2025-09-10", "New Coinbase One subscription benefits.", "blog_product_landing"),
    ("Coinbase unlocks millions of assets with DEX trading", "https://www.coinbase.com/blog/landing/product", "2025-08-08", "DEX trading integration expanding available assets.", "blog_product_landing"),
    ("Earn up to 4% bitcoin back on every purchase with the new Coinbase One Card", "https://www.coinbase.com/blog/landing/product", "2025-06-12", "Launch of the Coinbase One Card with bitcoin rewards.", "blog_product_landing"),
    ("Introducing Coinbase Business: The All-in-One Financial Platform for Modern Companies", "https://www.coinbase.com/blog/landing/product", "2025-06-12", "Launch of Coinbase Business platform.", "blog_product_landing"),
    ("Powering the future of ecommerce: Introducing Coinbase Payments", "https://www.coinbase.com/blog/landing/product", "2025-06-18", "Coinbase Payments product launch for ecommerce.", "blog_product_landing"),
    ("Canadians Can Now Earn up to 4.5% Rewards on Their USDC Balance", "https://www.coinbase.com/blog/landing/product", "2025-09-16", "USDC rewards rate increase for Canadian users.", "blog_product_landing"),
    ("Earn competitive yields by lending your USDC", "https://www.coinbase.com/blog/landing/product", "2025-09-18", "USDC lending feature launch.", "blog_product_landing"),
    ("A Guide to the Digital Asset Listing Process at Coinbase", "https://www.coinbase.com/blog/landing/product", "2025-09-10", "Explainer on Coinbase's asset-listing process.", "blog_product_landing"),
    ("The ideal way to launch – introducing token sales on Coinbase", "https://www.coinbase.com/blog/landing/product", "2025-11-10", "Token-sale feature launch.", "blog_product_landing"),
    ("Kalshi prediction markets powered by USDC and safeguarded by Coinbase Custody", "https://www.coinbase.com/blog/landing/product", "2025-11-13", "Prediction-markets integration with Kalshi.", "blog_product_landing"),
    ("Introducing a Powerful Suite of Business Payment Tools on Coinbase Business", "https://www.coinbase.com/blog/landing/product", "2025-10-16", "Business payment tools launch.", "blog_product_landing"),
]
for item in COINBASE_ITEMS:
    if len(item) == 5:
        title, url, date, desc, method = item
    else:
        title, url, date, desc = item
        method = "targeted_article_fetch"
    add("Coinbase", title, url, date, desc, method)

# ---------------------------------------------------------------- write out
OUT_CSV = os.path.join(HERE, "e1_release_notes.csv")
fieldnames = ["app", "title", "url", "publish_date", "description", "source_method", "in_corpus_window"]
with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames)
    w.writeheader()
    for r in rows:
        w.writerow(r)

by_app = {}
for r in rows:
    by_app.setdefault(r["app"], {"total": 0, "in_window": 0})
    by_app[r["app"]]["total"] += 1
    if r["in_corpus_window"]:
        by_app[r["app"]]["in_window"] += 1

print(f"Wrote {len(rows)} rows to {OUT_CSV}")
for app, c in by_app.items():
    print(f"  {app}: {c['total']} total, {c['in_window']} within corpus window [{WINDOW_START}, {WINDOW_END}]")
