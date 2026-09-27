# stage3_summarization/outputs/

Raw, pre-merge generation output: `group1.json` through `group6.json`, one file per
independent LLM subagent dispatch. Each of the 77 clusters was assigned to one of
6 groups (balanced by chunk count, not just cluster count), and each subagent
received only its assigned clusters' full prep data plus instructions to never
state an uncounted proportion, quote only verbatim text with real review IDs, and
disclose ambiguity/redundancy with neighboring clusters.

`../merge_outputs.py` combines these six files into the authoritative
`../stage3_roadmap_items.json` (77 items, 0 duplicates, 0 missing, 0 extra — a
clean completeness-check pass this run). Kept here, unmerged, for audit — to see
exactly what each subagent produced before any cross-cluster correction was
applied in `STAGE3_RUN_LOG.md` §8.
