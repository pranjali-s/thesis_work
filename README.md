# AI-Assisted App-Review Analysis for Product Roadmap Decision Support

**A Pipeline for Identifying, Organizing, and Prioritizing User Needs in Retail Trading Applications**

Master's Thesis submitted for the attainment of a Master of Science (M.Sc.)
at **RWTH Aachen University**.

**Author:** Pranjali Srivastav

**Institute / Chair:** Rheinisch-Westfälischen Technischen Hochschule Aachen , 
Chair of the TIME Research Area

**Supervisor(s):** Prof. Dr. Stefanie Paluch
**Submission date:** 30.09.2026

---

## What this repository is

This repository contains the full technical pipeline behind the thesis: an
AI-assisted system that mines app-store reviews of retail trading apps
(Robinhood, Coinbase, Trading 212), classifies and clusters the user needs
raised in them, summarizes each cluster into a structured "roadmap item,"
and prioritizes those items using several competing methods — comparing a
rule-based baseline, a trained classifier, and an LLM-applied rubric against
each app's own real, published release notes.

Every stage below is executed code and real data, not illustrative/toy
examples: review collection from live app stores, LLM-based classification
via the Anthropic API, embedding-based clustering, LLM-generated structured
summaries with independent grounding checks, and a prioritization
evaluation chain benchmarked against each company's actual shipped
changelog. Each stage folder contains its own scripts, raw/intermediate
data, run logs, and a `README.md` (plus, for most stages, a fuller
`*_Full_Documentation.md`) documenting exactly what was run, what was
independently verified, and what limitations or gaps are disclosed.

## Repository structure

| Folder | Pipeline stage | What it holds |
|---|---|---|
| `data_collection/` | §4.2 — Data collection | Scrapers for Google Play + Apple App Store reviews; the resulting multi-platform review corpus. |
| `taxonomy/` | §4.3 — Taxonomy development (B3) | Stratified sampling and supporting material for the category taxonomy used throughout classification. |
| `stage1_classification/` | §4.4.1 / §5.1 — Classification | LLM-based multi-label classification of the full review corpus against the taxonomy, plus the reliability-check material (keyword-baseline concordance, test-retest consistency). |
| `stage2_clustering/` | §4.4.2 — Clustering | Embedding (instructor-large) and per-category UMAP/HDBSCAN clustering of classified reviews into fine-grained topic clusters. |
| `stage3_summarization/` | §4.4.3 — Summarization | LLM-generated structured "roadmap items" (title, description, representative quotes) per cluster, with independent grounding verification and blind adversarial rating. |
| `stage4_prioritization/` | §4.4.4 / RQ4b — Prioritization | Three competing prioritization methods (a rule-based baseline, a trained Random Forest baseline, and an LLM-applied rubric), evaluated against each app's real release notes via candidate matching and rank-agreement metrics. |

Each subfolder is self-contained: it includes the scripts used to produce
its output, the output data itself, a run log describing the actual
execution, and a README explaining how to reproduce it. Several stages also
include a `*_reproduction_prompt.md` / `*_redo_package_README.md` pair
intended to let a fresh session (human or AI-assisted) rerun that stage
end-to-end from the included scripts and documented configuration.

## Pipeline overview

```
data_collection  →  taxonomy (B3)  →  stage1_classification
                                            │
                                            ▼
                                     stage2_clustering
                                            │
                                            ▼
                                    stage3_summarization
                                            │
                                            ▼
                                   stage4_prioritization
```

Each arrow represents one stage's verified output feeding the next stage's
input (e.g., Stage 1's labeled corpus is what Stage 2 clusters; Stage 2's
clusters are what Stage 3 summarizes into roadmap items; Stage 3's roadmap
items are what Stage 4 scores and ranks).

## Reproducibility

- Every stage discloses its exact model/configuration (model ID, prompts,
  seeds, batch sizes) in that stage's own README and run log.
- Stages using an LLM (classification, summarization, parts of
  prioritization) are **not bit-for-bit reproducible** across reruns —
  this is disclosed explicitly wherever it applies, rather than implied
  away. Where a stage depends on non-deterministic clustering (Stage 2) or
  live web data (Stage 4's release-note collection), this is stated in
  that stage's own documentation together with what *should* reproduce
  (the general pattern of findings) versus what won't (exact per-cluster
  numbers).
- No script output is accepted purely on its own printed summary —
  every stage's numbers were independently recomputed from the underlying
  raw data files as part of this project's verification discipline.

## Data and privacy

The review corpus consists of publicly posted app-store reviews (Google
Play and Apple App Store), collected via each platform's public interfaces.
No private, account-linked, or personally identifying data beyond what a
reviewer chose to make public in their review text is collected or stored.

## Citation

If referencing this work, please cite the thesis directly:

> Srivastav, P. (2026). *AI-Assisted App-Review Analysis for Product
> Roadmap Decision Support: A Pipeline for Identifying, Organizing, and
> Prioritizing User Needs in Retail Trading Applications* [Master's thesis,
> RWTH Aachen University].

## Contact

Pranjali Srivastav — pranjalisrivastav1@gmail.com
