# Current navigation result — 25 September 2026

**The artificial missing-corpus failure is fixed. The harness is executable for a controlled exploratory experiment, but page-opening similarity to hosted Luna has not been demonstrated.** Use [HANDOFF.md](HANDOFF.md) and the navigation-v2 release. Do not claim a fidelity pass.

The fetcher can open previously unseen public URLs without a URL whitelist. It follows real redirects, captures untreated responses in a shared cache, and applies the local experiment condition before returning any controlled page. The search index remains the same frozen 69-document seed. All six URLs that previously failed now fetch successfully and reproduce the same text in cached replay. **79 automated tests pass**, including every treatment condition, redirect interception, absent hubs, cache isolation and saved trace provenance.

A newly frozen diagnostic completed **24/24 answers: six navigation-focused questions × two repetitions × two modes**, using GPT-5.6 Luna. Questions were informed by the earlier failures; this is a convenience diagnostic, not an independent representative holdout. Model behavior was not tuned after seeing its results.

| Observable | Custom | Hosted Luna |
|---|---:|---:|
| Queries per answer | 6.50 | 6.75 |
| Search batches per answer | 4.00 | 2.17 |
| Open attempts per answer | 2.33 | 0.00 |
| Answers with an open | 75% | 0% |
| Cited domains per answer | 2.58 | 2.50 |
| CommBank mention rate | 100% | 83.3% |
| Named providers per answer | 2.58 | 2.00 |

Custom made **28 opens, all successful**, with zero missing-corpus failures or actual HTTP 404s. Two opens used an unexposed Westpac budget-planner URL, which was fetched successfully without adding it to the corpus. Seven distinct public-response records were read, including redirects. Hosted recorded no explicit opens; that does not mean it received no page content through search.

Average queries and cited domains are close on these questions, but opening behavior and search batching differ substantially. The open-count distribution distance is 0.75, above the prespecified 0.10 tolerance; the query-count distance is 0.333, above 0.15 despite close averages. The formal simultaneous-equivalence verdict is **INCONCLUSIVE**. These data support a functioning URL fix, not behavioral equivalence. A plausible remaining cause is different information returned through search; the current data do not isolate that cause.

Estimated usage was **US$0.44**, with **US$0.88** conservatively accounted/reserved. Neither is an invoice. No model run hit the configured budget limit. Some answers exceeded the analysis word-count cap.

All 76 recorded custom tool actions (including the 28 opens) replayed with identical outputs under the final code and cached responses, with no network fetching or model calls. [Replay evidence](evidence/2026-09-25/commbank_navigation_replay.json).

The final handoff adds a logging-only correction: a dedicated navigation-read field now persists in partial/final traces, and reports can derive record counts from the hop hashes already emitted by the pilot. The frozen pilot code, original reports and unmodified traces remain bundled. This correction did not alter model inputs, tool outputs, parsing or decisions.

Evidence: [navigation pilot metrics](evidence/2026-09-25/commbank_navigation_pilot_v1.json), [statistical report](evidence/2026-09-25/commbank_navigation_pilot_v1.md), [six-URL regression](evidence/2026-09-25/commbank_navigation_regression.json). The full 216-answer award study remains unrun. Its effects would describe this harness; transfer to hosted Luna remains unestablished.

---

# Historical offline comparison

This section records the previous offline design. Its point estimates must not be inherited by the changed navigation implementation.

The locked comparison completed **72 answers: 18 questions × two repetitions × two modes**. Both used GPT-5.6 Luna, medium reasoning and the same questions/instructions. Custom used the frozen 69-document corpus; hosted used unrestricted API web search. The candidate was selected before reviewing this validation and was not changed in response to it.

| Observable | Custom | Hosted Luna | Preset tolerance on difference |
|---|---:|---:|---:|
| Queries per answer | 6.47 | 7.06 | ±1.50 |
| Search batches per answer | 4.03 | 2.25 | ±1.00 |
| Opens per answer | 0.50 | 0.33 | ±0.35 |
| Answers with an open | 16.7% | 33.3% | ±10 percentage points |
| Cited domains per answer | 3.25 | 3.61 | ±0.50 |
| CommBank mention rate | 80.6% | 88.9% | ±10 percentage points |
| Named providers per answer | 3.08 | 2.92 | ±0.50 |
| Answer words, capped at 1,000 | 709.53 | 730.81 | ±100 |

**Open attempts versus successful reads:** The 18 custom attempts included nine `not_in_corpus` errors in two digital-feature answers. Eight failed URLs were previously exposed links; one was unexposed. Successful opens averaged **0.25 per answer**, while the table’s registered attempt metric remains **0.50**. No live HTTP request was made for those missing URLs, so they are not verified 404s. This coverage defect limits the apparent agreement in average attempts and should be repaired and revalidated before claiming opening fidelity. [Detailed audit](evidence/2026-09-24/commbank_open_audit.json).

These are descriptive point estimates, not confidence-certified passes. The query-count, citation-domain and provider-mention distribution distances were **0.056, 0.105 and 0.046**, each below its registered 0.15 tolerance. The **open-count distribution distance was 0.306**, above its 0.10 tolerance.

The remaining opening difference is concrete: hosted opened exactly one page in 12/36 answers and none in 24/36. Custom opened pages in only 6/36 answers, with counts of 1, 2, 3, 3, 3 and 6. Similar average opens therefore conceal different opening patterns. Custom also split its queries into more search batches.

**Do not generalize the pooled result to every question type.** In unbranded questions the custom-minus-hosted CommBank mention gap was −25 percentage points and the any-open gap was −50 points. Several other category-level estimates also exceeded tolerance. Corpus coverage remains different: hosted can recommend providers and cite sources outside the frozen collection.

## Historical claim for the offline design only

> On a fixed set of 18 Australian savings questions, the custom harness produced similar observed average query counts, page-open counts, citation counts and provider mentions to GPT-5.6 Luna with hosted API web search, within our predefined average-difference tolerances. Query, citation-domain and provider-mention distributions were also close. Search batching, opening frequency and the open-count distribution differed; some question categories differed more substantially.

The formal **95% simultaneous equivalence verdict is INCONCLUSIVE**. There are only 18 authored question clusters, six per category; they are not a representative population sample. The conservative intervals are wide, and some answers exceeded the registered word-count cap. This is not “95% confidence we copied ChatGPT,” nor evidence of identical hidden sources or ChatGPT UI orchestration. Changing corpus, model, instructions, tool behavior or question mix requires a new comparison.

## Experiment readiness and quality

- All **68 offline tests pass**, including a clean code export without credentials. Rebuilding from the saved source cache reproduces both corpus files byte-for-byte.
- All **six award conditions** completed a paid operational smoke test; scoring and effect-report generation completed without pipeline flags. That single-question smoke test is not an award-effect result.
- The **216-answer award study is planned and has not been executed**. Opus can run it using the public release bundle and [HANDOFF.md](HANDOFF.md). Interpret effects as effects within this harness; transfer to hosted Luna remains unestablished.
- A preselected, non-blinded 12-answer spot check found two custom-answer issues: one misstated the smallest minimum deposit; another misread a graphical PDF withdrawal table and used that error in its ranking. Hosted also disagreed with captured NAB rates and used sources outside the corpus. This review is diagnostic, not an accuracy certificate. Scoring must check original evidence, particularly PDF tables.

There were 72 completed comparison answers **after recovery**, plus one retained earlier network-failed hosted attempt. First attempts completed 36/36 custom and 35/36 hosted. The retry reused four completed answers unchanged and preserved the failed attempt and possible charge. Combined conservative accounting/reservations were **US$2.99**; reported usage for the 72 answers estimates **US$1.34**. Neither is an invoice.

Evidence: [full metrics and paired numeric observations](evidence/2026-09-24/commbank_validation_v3.json), [readable statistical report](evidence/2026-09-24/commbank_validation_v3.md), [quality review](evidence/2026-09-24/commbank_validation_quality.json), [six-condition smoke test](evidence/2026-09-24/commbank_operational_smoke.json), [corpus provenance](evidence/2026-09-24/commbank_corpus_final.json).

Historical trials and failures remain in [evidence/](evidence/README.md) and [HISTORICAL_VALIDATION.md](HISTORICAL_VALIDATION.md). They are not alternative recommended configurations.
