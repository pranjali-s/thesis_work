# stage3_summarization/ratings/

Raw, pre-merge blind adversarial rating output: `group1_ratings.json` through
`group6_ratings.json`, from a **second, independent** set of 6 LLM subagent
dispatches — with no memory of the generation step — using the same group
assignments as `../outputs/`. Each subagent read the entire sampled review set for
its assigned clusters (not just the generated title/description/quotes) and rated
faithfulness/clarity/usefulness (1-5) plus free-text notes, independently
re-deriving any stated proportion before judging faithfulness.

`../merge_ratings.py` combines these into `../stage3_ratings.json` /
`stage3_ratings_summary.json` (77 items, 0 duplicates/missing/extra). The free-text
notes in these raw files are what Section 8 of `STAGE3_RUN_LOG.md`'s
faithfulness-issue investigation was filtered down from.
