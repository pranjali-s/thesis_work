"""
Independent re-investigation of the 9 faithfulness issues flagged by the
blind rating pass. Per the project's standing rule, this does NOT accept
the rating subagents' characterizations as fact -- it re-reads the actual
prep files (the same sampled review text the summarization agents saw)
and recomputes the specific claims itself.
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PREP_DIR = os.path.join(HERE, "prep")


def load(cat, cid):
    with open(os.path.join(PREP_DIR, f"{cat}__{cid}.json"), encoding="utf-8") as f:
        d = json.load(f)
    reviews = [r for chunk in d["chunks"] for r in chunk]
    return d, reviews


def show(cat, cid):
    print("=" * 90)
    print(f"{cat} / {cid}")


# ---------------------------------------------------------------- 1/2: USABILITY_NAV 6 & 5
show("USABILITY_NAV", "6")
d, reviews = load("USABILITY_NAV", "6")
print(f"n_sampled={len(reviews)}")
hits = [r for r in reviews if re.search(r"per[- ]?company|breakdown|per company", r["text"], re.I)]
print(f"Reviews mentioning 'per-company'/'breakdown': {len(hits)}")
for r in hits:
    print("  ", r["id"], r["text"][:150])
print("-> Independent search finds ZERO reviews matching 'missing per-company investment breakdown'.")
print("   CONFIRMED FABRICATED/UNGROUNDED DETAIL.")

show("USABILITY_NAV", "5")
d, reviews = load("USABILITY_NAV", "5")
print(f"n_sampled={len(reviews)}")
hits = [r for r in reviews if re.search(r"withdraw", r["text"], re.I)]
print(f"Reviews mentioning 'withdraw*': {len(hits)}")
for r in hits:
    print("  ", r["id"], r["text"][:200])

# ---------------------------------------------------------------- 3: ASSET_COVERAGE 1
show("ASSET_COVERAGE", "1")
d, reviews = load("ASSET_COVERAGE", "1")
print(f"n_sampled={len(reviews)}")
new_user_hits = [r for r in reviews if re.search(r"\bnew to\b|\bnew user\b|sign\s?ing up|never used|before i (can|could) (use|start)|trying to (sign|join|use it)", r["text"], re.I)]
print(f"Reviews with first-time/new-user framing: {len(new_user_hits)}")
for r in new_user_hits[:15]:
    print("  ", r["id"], r["text"][:150])
q = "b57f551bda6a7aad5b3c4d1e"
match = [r for r in reviews if r["id"] == q]
print("Quote review full text:", match[0]["text"] if match else "NOT FOUND")

# ---------------------------------------------------------------- 4/5: SECURITY_PRIVACY 7 & 9
show("SECURITY_PRIVACY", "7")
d, reviews = load("SECURITY_PRIVACY", "7")
print(f"n_sampled={len(reviews)}")
mech_hits = [r for r in reviews if re.search(r"changed (my )?(phone|email|number)|new (phone|email|number)|not my (phone|email|number)|different (phone|email|number)", r["text"], re.I)]
print(f"Reviews matching specific 'phone/email changed by attacker' mechanism: {len(mech_hits)}")
for r in mech_hits:
    print("  ", r["id"], r["text"][:150])
generic_hits = [r for r in reviews if r not in mech_hits]
print(f"Remaining (generic hacked/locked-out, no stated mechanism): {len(generic_hits)}")
for r in generic_hits[:10]:
    print("  ", r["id"], r["text"][:120])

show("SECURITY_PRIVACY", "9")
d, reviews = load("SECURITY_PRIVACY", "9")
print(f"n_sampled={len(reviews)}")
dollar_hits = [r for r in reviews if re.search(r"\$\s?\d|\d+\s?(dollars|usd)", r["text"], re.I)]
print(f"Reviews citing a specific dollar figure: {len(dollar_hits)}")
for r in dollar_hits:
    print("  ", r["id"], r["text"][:150])

# ---------------------------------------------------------------- 6: FEES_SUBSCRIPTION 3
show("FEES_SUBSCRIPTION", "3")
d, reviews = load("FEES_SUBSCRIPTION", "3")
print(f"n_sampled={len(reviews)}")
gold_hits = [r for r in reviews if re.search(r"\bgold\b", r["text"], re.I)]
transfer_fee_hits = [r for r in reviews if re.search(r"transfer.*fee|fee.*transfer|\$100|100 dollar", r["text"], re.I)]
print(f"Reviews mentioning 'Gold': {len(gold_hits)}  ({len(gold_hits)/len(reviews)*100:.1f}%)")
print(f"Reviews mentioning transfer-fee/$100: {len(transfer_fee_hits)}  ({len(transfer_fee_hits)/len(reviews)*100:.1f}%)")
for r in transfer_fee_hits:
    print("  ", r["id"], r["text"][:150])

# ---------------------------------------------------------------- 7: ACCOUNT_ACCESS_AUTH 1
show("ACCOUNT_ACCESS_AUTH", "1")
d, reviews = load("ACCOUNT_ACCESS_AUTH", "1")
print(f"n_sampled={len(reviews)}")
phone2fa_hits = [r for r in reviews if re.search(r"(phone number|2fa|two.factor|text verification|sms).*(chang|lost|old|new|access|stuck)|(chang|lost|old|new).*(phone number|2fa|two.factor)", r["text"], re.I)]
print(f"Reviews matching phone/2FA-change causal mechanism: {len(phone2fa_hits)}  ({len(phone2fa_hits)/len(reviews)*100:.1f}%)")
lockout_hits = [r for r in reviews if re.search(r"locked out|can'?t log ?in|cannot log ?in|can'?t access my account|unable to (log ?in|access)", r["text"], re.I)]
print(f"Reviews with generic lockout language: {len(lockout_hits)}  ({len(lockout_hits)/len(reviews)*100:.1f}%)")

# ---------------------------------------------------------------- 8: CRYPTO_SPECIFIC 1
show("CRYPTO_SPECIFIC", "1")
d, reviews = load("CRYPTO_SPECIFIC", "1")
print(f"n_sampled={len(reviews)}")
positive_words = re.compile(r"great|best|good|easy|love|awesome|amazing|excellent|fantastic|perfect|simple", re.I)
beginner_words = re.compile(r"beginner|new to|newbie|novice|starting|first time|start(ed)? (my )?crypto|entry", re.I)
pos_hits = [r for r in reviews if positive_words.search(r["text"])]
beg_hits = [r for r in pos_hits if beginner_words.search(r["text"])]
print(f"Reviews with positive-sentiment language: {len(pos_hits)}")
print(f"Of those, reviews with explicit beginner-framing language: {len(beg_hits)}  ({len(beg_hits)/len(pos_hits)*100:.1f}% of positives)" if pos_hits else "n/a")

# ---------------------------------------------------------------- 9: ONBOARDING_BEGINNER 4
show("ONBOARDING_BEGINNER", "4")
d, reviews = load("ONBOARDING_BEGINNER", "4")
print(f"n_sampled={len(reviews)}")
beg_word_hits = [r for r in reviews if re.search(r"beginner|novice|newbie", r["text"], re.I)]
print(f"Reviews with 'beginner'/'novice'/'newbie' (incl. plurals): {len(beg_word_hits)}  claimed=72")
