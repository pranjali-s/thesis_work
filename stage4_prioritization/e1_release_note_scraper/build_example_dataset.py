"""Merge hand checked historical examples with the previously checked 2026 examples."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'verified_starting_set_2026-09-24.csv'
OUT = ROOT / 'verified_examples_no_start_limit_2026-09-24.csv'
with SRC.open(encoding='utf-8-sig', newline='') as file:
    reader = csv.DictReader(file)
    fields = reader.fieldnames
    rows = list(reader)

def add(app, date, effective, area, change_type, summary, status, market, url):
    rows.append(dict(zip(fields, (app, date, effective, area, change_type, summary, status, market, url))))

rh = 'https://robinhood.com/us/en/newsroom/'
cb = 'https://www.coinbase.com/blog/'
t = 'https://community.trading212.com/t/'
add('robinhood','2025-03-17','','Prediction markets','New app hub','Robinhood announced a prediction markets hub within its app, initially including rate and college basketball event contracts.','announced launch; availability by account requires review','US',rh+'robinhood-prediction-markets-hub/')
add('robinhood','2025-03-27','','Managed investing','New service','Robinhood announced Strategies, offering managed portfolios and expert guidance within the app.','announced; rollout date requires review','eligible Robinhood customers',rh+'introducing-strategies-banking-and-cortex/')
add('robinhood','2025-06-17','','Charting','Mobile tools','Robinhood announced Legend charts on mobile, including expanded indicators and quick order entry via auto-send.','rolling out beginning announcement date','US',rh+'introducing-robinhood-legend-charts-on-mobile/')
add('robinhood','2025-12-16','2025-12-16','Prediction markets','New contracts','Robinhood said live pro-football player contracts could be tracked and traded starting that day.','available starting that day','eligible customers',rh+'robinhood-presents-yes-no-event/')
add('robinhood','2025-12-16','','AI features','Planned rollout','Robinhood announced a new app-wide Cortex assistant and personalized portfolio Digests for a future rollout.','prospective; launch date not verified from this announcement','Robinhood Gold',rh+'robinhood-presents-yes-no-event/')
add('robinhood','2026-03-18','2026-03-18','Social','Limited beta','Robinhood Social beta began rolling out to selected traders with verified profiles, live trade sharing, following and discussion.','limited beta; not general availability','selected traders',rh+'robinhood-social-beta/')
add('coinbase','2025-01-29','','App navigation','Redesign','Coinbase described changes to the Home, My Assets, asset details and Transactions tabs.','described as recent changes; individual rollout dates not specified','markets unspecified',cb+'building-economic-freedom-one-pixel-at-a-time')
add('coinbase','2025-07-21','2025-07-21','Derivatives','New trading products','Eligible US users could start trading regulated long-dated Bitcoin and Ether perpetual-style futures.','starting July 21','eligible US traders',cb+'perpetual-futures-have-arrived-in-the-us')
add('coinbase','2025-08-08','','DEX trading','Phased feature launch','Coinbase began rolling out in-app DEX trading for Base assets.','select-user rollout; article later amended with wider access','US excluding New York',cb+'coinbase-unlocks-millions-of-assets-with-dex-trading')
add('coinbase','2025-09-18','','USDC lending','New app integration','Coinbase announced access to lending USDC via Morpho from the Coinbase app.','starting on article date; individual eligibility may vary','eligible users',cb+'earn-competitive-yields-by-lending-your-usdc')
add('trading212','2024-06-25','','Advanced mobile charts','New chart tools','Trading 212 said its iOS and Android charts gained CFD buy charts, indicator syncing, instrument tabs and split layouts.','described as live in mobile update','iOS and Android users',t+'advanced-charts-on-mobile-just-got-better/71998')
add('trading212','2025-01-03','','Portfolio overview','Redesigned metrics','Trading 212 announced portfolio value, money-weighted return, net deposit and cash section changes.','phased rollout from Jan 3; promised wider availability within a week','unspecified',t+'improved-portfolio-screen-better-return-calculations-mwrr-cash-widget-and-more/80132')
add('trading212','2025-11-05','','CFD order entry','Redesign','Trading 212 introduced a new order layout, percent based stop controls, quick sizing and cost estimate tabs.','live for web; gradual mobile rollout','CFD users excluding AU entity',t+'cfds-have-a-new-look-a-redesigned-order-screen-cleaner-interface-and-more/88700')
rows.sort(key=lambda r: (r['announcement_date'],r['app'],r['area']))
with OUT.open('w',encoding='utf-8-sig',newline='') as file:
    writer=csv.DictWriter(file,fieldnames=fields)
    writer.writeheader()
    writer.writerows(rows)
print(f'{len(rows)} source-linked examples -> {OUT.name}')
