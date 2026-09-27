# Fast human-coding tool for the 616-review reliability subsample

This is a terminal alternative to the Excel workbook (`B5_human_coding_workbook.xlsx`)
for step 3 — YOUR human coding of the 616-review reliability subsample. It
does not classify anything for you; it just removes the Excel overhead
(scrolling, clicking the right cell, hunting for a category's definition)
so your own judgment can move faster.

**If you've already coded some reviews in the Excel workbook:** tell me
how many/which ones and I'll write a 5-line script to import that progress
into this tool's format so you don't redo any work. Don't start this tool
fresh if you have existing Excel progress worth keeping.

## What's in this folder

```
human_code.py                          the tool
B4_human_reliability_subsample_v2.csv  the 616 reviews to code
README.md                              this file
```

## How to run it

```
python3 human_code.py
```

For each review it shows the app, star rating, date, and text, then asks:
```
Codes [h/s/q]:
```

- Type one or more category **numbers**, space-separated, e.g. `1 3` for
  USABILITY_NAV + APP_STABILITY_PERFORMANCE. Multi-label is expected —
  most reviews raise more than one concern.
- Add an optional note after `//`, e.g. `1 3 // ambiguous, could be 8 instead`
- `h` — reprint the 17-category legend with definitions
- `s` — skip this one for now (it'll come back around later in the same run)
- `q` — save and quit. **Every answer is written to disk immediately**, so
  quitting (or closing the terminal, or your laptop dying) never loses
  progress — just run `python3 human_code.py` again later and it picks up
  exactly where you left off.

Blinding is preserved: the tool deliberately does not show you which
reviews were randomly sampled vs. purposively boosted for a rare category
(that mapping lives separately in `B5_human_coding_BOOSTER_KEY.csv`, same
as with the Excel version) — so your judgment isn't influenced by knowing
which reviews were "supposed to" hit a given category.

## Output

`human_coding_results.csv` (created in this same folder as you go):
```
review_id_hash,labels,note,coded_at
585b13a32bf32d008b83147d,USABILITY_NAV|APP_STABILITY_PERFORMANCE,,2026-09-18T...
```

When you're done with all 616 (or however many you get through — see note
below on partial completion), send `human_coding_results.csv` back and
I'll run the AI classifier on the same 616 reviews and compute human-vs-AI
Cohen's kappa.

## If you genuinely don't have time for all 616

Coding fewer than 616 is a real option if time is tight — just tell me
where you land. If it comes to that, prioritize finishing all 160
purposively-boosted rows first (they carry the most information for the
rare-category reliability check) before doing as many of the remaining
456 random rows as time allows, and I'll be explicit in the write-up about
the actual subsample size used rather than reporting 616 if it ends up
smaller. Better to have an honestly-labeled smaller genuine sample than
either an incomplete run or one that quietly wasn't fully human-reviewed.
