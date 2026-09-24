# Current validation

<!-- CURRENT_RESULT_START -->
**Working candidate; full validation in progress.** The current harness uses context-preserving source passages and a 69-document CommBank/competitor corpus. All 65 offline tests pass, including a clean checkout without credentials.

The completed focused check covered six calibration questions, twice each. It reused the recorded hosted reference:

| Observable | Custom context passages | Hosted Luna |
|---|---:|---:|
| Queries per answer | 2.75 | 3.00 |
| Opens per answer | 0.75 | 0.50 |
| Answers with an open | 50.0% | 41.7% |
| Citation domains per answer | 1.83 | 1.75 |
| CommBank mention rate | 33.3% | 33.3% |
| Completed answers | 12/12 | 12/12 |

The observed open-count distribution distance was 0.083, within the registered 0.10 tolerance. The query-count distribution distance was 0.167, slightly outside 0.15. These are encouraging calibration observations, not confidence-certified equivalence. A non-blinded critical-facts review found one contradictory ANZ withdrawal sentence among the 12 custom answers. The issue is retained in the [quality record](evidence/2026-09-24/commbank_context_quality.json).

A fresh 12-question paired calibration and a frozen 18-question experiment-domain validation are running. Their final results will replace this status; do not treat an unfinished run as a pass. The latter uses the previously authored award-study prompts before any treatment is applied. The code now also excludes link-destination words from page ranking; the focused check above preceded that index correction.

Details: [focused check](evidence/2026-09-24/commbank_context_v5.json), [corpus record](evidence/2026-09-24/commbank_corpus_final.json), [operator handoff](HANDOFF.md).
<!-- CURRENT_RESULT_END -->

The records below preserve earlier failed attempts and their original scope. They are not the current recommended configuration.

# Historical documentation pilot — 2026-09-24

**Decision: the controlled experiment platform is implemented and tested. The searching agent has NOT passed as a behavioural substitute for hosted Luna or ChatGPT.** No 95% equivalence claim is justified by these runs.

## Delivered and checked

- 49 offline tests pass, including complete mocked suite execution/resume and manual scoring-packet generation. No paid calls occur in these tests.
- Generic reference corpora, search/open/click/find tools, five award-placement arms, full evidence traces and exact pre-open audits.
- Frozen paired benchmarks, question-level repetitions, 12 scalar metrics and four distributions, category checks, live/live repeatability, missing-data gates and simultaneous interval reports.
- Persistent conservative request reservations, no hidden retries, generic excerpt ablation, and an Opus operator runbook.
- All paid runs returned the requested `gpt-5.6-luna` model name; no substitute decision model was used. The provider alias is not a guarantee of immutable weights.

## Main pilot: 48 planned runs, 48 recorded

Twelve English documentation questions across Python, SQLite and Git; two repetitions per question per mode. Both paths used Responses, the same question/instructions and medium reasoning. Custom search used an observed 13-page snapshot; the hosted reference used unrestricted `web_search_preview`. This is a convenience pilot, not a representative banking holdout.

Hosted completed 24/24; custom completed 22/24. Both custom failures were the Git fetch/pull comparison at the eight-round boundary. Behavioural comparisons below use the **11 questions with all four runs completed and uncensored**; reliability rates use all 12 questions. Missingness blocks certification.

| Metric | Custom | Hosted Luna | Prespecified tolerance |
|---|---:|---:|---:|
| search_queries | 1.500 | 1.227 | ±1.5 |
| search_actions | 1.318 | 1.091 | ±1.0 |
| open_actions | 1.545 | 0.227 | ±0.35 |
| any_open | 0.909 | 0.227 | ±0.1 |
| find_actions | 0.545 | 0.000 | ±0.35 |
| citation_domains | 1.000 | 1.000 | ±0.5 |
| target_mention | 1.000 | 1.000 | ±0.1 |
| entity_mentions | 1.364 | 1.364 | ±0.5 |
| answer_words | 180.091 | 196.955 | ±100 |
| completed | 0.917 | 1.000 | ±0.05 |
| budget_limited | 0.083 | 0.000 | ±0.05 |

| Distribution | Observed TV distance | Prespecified tolerance |
|---|---:|---:|
| search_count_distribution | 0.045 | 0.15 |
| open_count_distribution | 0.682 | 0.1 |
| citation_domain_distribution | 0.000 | 0.15 |
| entity_distribution | 0.000 | 0.15 |

The query-count, citation-domain and configured-name distributions are close in this sample. The opening behaviour is not: 90.9% of comparable custom answers open at least one page, versus 22.7% of hosted answers. Mention metrics test configured name presence, not correctness or endorsement. No systematic semantic-quality certification was performed.

The statistical verdict is **INCONCLUSIVE**, not equivalent. The 95% simultaneous bounds are very wide at this sample size; point estimates already exceed several practical tolerances. Do not interpret the absence of a statistically significant “different” verdict as evidence of similarity. See [STATISTICS.md](STATISTICS.md).

Only 15 of 185 reported hosted source URLs match a snapshot page under the diagnostic URL normalization. These are URL observations, not 185 proven reads or a complete search candidate set. The environment has substantial coverage differences, so this pilot cannot isolate the model policy from its evidence supply.

## Diagnosed defects and retained failed trials

1. **v1: 10/48 jobs recorded.** The CSV question exhausted its rounds. The initial HTML extraction broke inline syntax, path-specific `site:` queries were unsupported, and URL fragments did not navigate to captured page anchors. Those mechanics were corrected and regression-tested.
2. **v2: 10/48 jobs recorded.** CSV still failed. Inspection of the official HTML identified decisive explanatory footnotes inside semantic `aside` elements that the extractor had removed. Asides/footnotes are now retained. The real CSV footnote was checked in the corrected snapshot, and both v3 CSV repetitions completed and cited it.
3. **v3: 48/48 jobs recorded.** This is the full pilot above. Failed and censored attempts remain visible; they are not silently replaced or pooled with later trials.
4. **v4: 4/4 targeted Git jobs recorded.** A 14-page corpus added the requested Git configuration page. Both hosted answers completed; both custom attempts still reached the round boundary. Coverage alone therefore did not resolve that question. This targeted diagnostic is not a new holdout.

## Excerpt-length ablation

The exploratory v5 runner changed only custom excerpt length from 1,200 to 6,000 characters, retaining v3 code, corpus, instructions and questions. It reused the existing hosted responses and cannot produce a fresh validation certificate. Twenty-two of 24 jobs were attempted: 20 completed, one hit the round limit, and one stopped before a request because its reservation exceeded the remaining local trial budget. Two jobs were unattempted. There are no unknown billing outcomes.

Nine questions have every repetition measurable in all three groups:

| Metric | Original custom | 6,000-character custom | Same hosted reference |
|---|---:|---:|---:|
| search_queries | 1.500 | 1.389 | 1.278 |
| open_actions | 1.722 | 1.056 | 0.278 |
| any_open | 0.944 | 0.778 | 0.278 |
| find_actions | 0.500 | 0.222 | 0.000 |
| answer_words | 194.611 | 203.389 | 216.556 |

Longer excerpts reduced opens on the common subset, but the remaining 0.778-open mean gap still exceeds the registered 0.35 tolerance. The answer-level any-open gap is 0.50, above the 0.10 tolerance. Longer excerpts also increased request costs. This setting was **not adopted as a validated default**. The 13-page environment still lacks pages requested by the agent, and Git documentation contains substantial navigation/version text. More snippet characters are not a complete solution.

## Paid usage and artifacts

Public clones include allowlisted numeric measurements and all five report summaries under [evidence/](evidence/README.md). The raw-artifact links below refer to files available only on the original machine, not files included in the public repository.

| Trial | Recorded jobs | Conservative accounted USD | Usage-based estimated USD |
|---|---:|---:|---:|
| public_web_pilot_v1 | 10 | 0.201871 | 0.099816 |
| public_web_pilot_v2 | 10 | 0.207845 | 0.101710 |
| public_web_pilot_v3 | 48 | 0.789907 | 0.401231 |
| git_coverage_diagnostic_v4 | 4 | 0.127870 | 0.051682 |
| excerpt_calibration_v5 | 22 | 0.542535 | 0.111619 |
| **Total** | **94** | **1.870027** | **0.766058** |

Both measures are below the authorized US$2 pilot budget. Conservative accounting uses higher token rates and ignores cache discounts; the usage estimate uses the documented short-context rates and reported cached tokens. Neither is an invoice. Earlier, separate API smoke tests had an estimated total of US$0.026128; even including that estimate the total remains below US$2. No purchase or account setting was changed.

All raw snapshots, manifests, traces, budget ledgers and reports are under their named `results/` directories, excluded from Git. The main reports are [v3 validation](results/public_web_pilot_v3/report.md), [v3 open audit](results/public_web_pilot_v3/open-audit.md), [Git coverage diagnostic](results/git_coverage_diagnostic_v4/report.md) and [excerpt ablation](results/excerpt_calibration_v5/report.md). Credentials are neither committed nor included in results.

## Suitability and remaining requirements

**Usable now:** reproducible controlled-corpus studies, five treatment arms, exposure/navigation audits, manual correctness scoring, paired effect estimates and honest fidelity evaluation. This is an experimental platform, not a validated ChatGPT replica.

**Required before claims about real Luna in the award experiment:** supply the original real bank corpus/questions; build a faithful current-page reference separate from manipulated arms; improve retrieval/content coverage on calibration cases; then freeze genuinely new representative holdout questions and evaluate all registered gates. The original 53-page bank corpus and 160-question set were not supplied, so that bank-specific study was not run. A larger study alone will not fix the observed open-rate gap.

The next engineering work should investigate what evidence each search response delivers, its useful passage selection and its coverage of relevant pages. Do not impose an open quota or widen tolerances to manufacture a match. Hosted raw search payloads remain unobservable; matching exposed actions cannot establish identical internal reading behaviour. A higher-fidelity search provider may be needed if local BM25 and a restricted corpus cannot pass task-specific validation.

Use [OPUS_RUNBOOK.md](OPUS_RUNBOOK.md) for executable steps and scoring rules. Opus is the operator; replacing Luna with Opus as the decision model would be a new experiment. Findings before a fidelity pass must be described as effects inside this controlled harness.
