# Current result

**Ready to hand over for an exploratory, controlled award-placement experiment. The harness has measured similarities to hosted Luna, but has not passed overall behavioral equivalence.** Use the single configuration in [HANDOFF.md](HANDOFF.md).

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

These are descriptive point estimates, not confidence-certified passes. The query-count, citation-domain and provider-mention distribution distances were **0.056, 0.105 and 0.046**, each below its registered 0.15 tolerance. The **open-count distribution distance was 0.306**, above its 0.10 tolerance.

The remaining opening difference is concrete: hosted opened exactly one page in 12/36 answers and none in 24/36. Custom opened pages in only 6/36 answers, with counts of 1, 2, 3, 3, 3 and 6. Similar average opens therefore conceal different opening patterns. Custom also split its queries into more search batches.

**Do not generalize the pooled result to every question type.** In unbranded questions the custom-minus-hosted CommBank mention gap was −25 percentage points and the any-open gap was −50 points. Several other category-level estimates also exceeded tolerance. Corpus coverage remains different: hosted can recommend providers and cite sources outside the frozen collection.

## Claim this evidence supports

> On a fixed set of 18 Australian savings questions, the custom harness produced similar observed average query counts, page-open counts, citation counts and provider mentions to GPT-5.6 Luna with hosted API web search, within our predefined average-difference tolerances. Query, citation-domain and provider-mention distributions were also close. Search batching, opening frequency and the open-count distribution differed; some question categories differed more substantially.

The formal **95% simultaneous equivalence verdict is INCONCLUSIVE**. There are only 18 authored question clusters, six per category; they are not a representative population sample. The conservative intervals are wide, and some answers exceeded the registered word-count cap. This is not “95% confidence we copied ChatGPT,” nor evidence of identical hidden sources or ChatGPT UI orchestration. Changing corpus, model, instructions, tool behavior or question mix requires a new comparison.

## Experiment readiness and quality

- All **68 offline tests pass**, including a clean code export without credentials. Rebuilding from the saved source cache reproduces both corpus files byte-for-byte.
- All **six award conditions** completed a paid operational smoke test; scoring and effect-report generation completed without pipeline flags. That single-question smoke test is not an award-effect result.
- The **216-answer award study is planned and has not been executed**. Opus can run it using the private frozen bundle and [HANDOFF.md](HANDOFF.md). Interpret effects as effects within this harness; transfer to hosted Luna remains unestablished.
- A preselected, non-blinded 12-answer spot check found two custom-answer issues: one misstated the smallest minimum deposit; another misread a graphical PDF withdrawal table and used that error in its ranking. Hosted also disagreed with captured NAB rates and used sources outside the corpus. This review is diagnostic, not an accuracy certificate. Scoring must check original evidence, particularly PDF tables.

There were 72 completed comparison answers **after recovery**, plus one retained earlier network-failed hosted attempt. First attempts completed 36/36 custom and 35/36 hosted. The retry reused four completed answers unchanged and preserved the failed attempt and possible charge. Combined conservative accounting/reservations were **US$2.99**; reported usage for the 72 answers estimates **US$1.34**. Neither is an invoice.

Evidence: [full metrics and paired numeric observations](evidence/2026-09-24/commbank_validation_v3.json), [readable statistical report](evidence/2026-09-24/commbank_validation_v3.md), [quality review](evidence/2026-09-24/commbank_validation_quality.json), [six-condition smoke test](evidence/2026-09-24/commbank_operational_smoke.json), [corpus provenance](evidence/2026-09-24/commbank_corpus_final.json).

Historical trials and failures remain in [evidence/](evidence/README.md) and [HISTORICAL_VALIDATION.md](HISTORICAL_VALIDATION.md). They are not alternative recommended configurations.
