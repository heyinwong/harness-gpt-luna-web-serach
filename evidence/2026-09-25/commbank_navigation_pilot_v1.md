# Behavioural validation

**Verdict: INCONCLUSIVE**

Registered simultaneous confidence level: 95%. 24/24 runs recorded across 6 questions.

Confidence is coverage of registered metric bounds under the sampling assumptions; it is not a probability that two agents are identical or that results transfer to all future designs.

Scope: Newly authored navigation-focused pilot after discovering missing-corpus errors. Failure intents informed question selection. This is a diagnostic convenience sample, not a representative holdout or inherited equivalence pass.

## Overall metrics

Differences are custom minus live. TV is total variation distance (0 identical, 1 disjoint). Count means are capped as registered; raw values remain in the JSON.

| Metric | Custom | Live | Difference / TV | Simultaneous interval | Tolerance | Verdict |
|---|---:|---:|---:|---|---|---|
| search_queries | 6.500 | 6.750 | -0.250 | [-20.000, 20.000] | ± 1.5 | inconclusive |
| search_actions | 4.000 | 2.167 | 1.833 | [-12.000, 12.000] | ± 1.0 | inconclusive |
| open_actions | 2.333 | 0.000 | 2.333 | [-10.000, 10.000] | ± 0.35 | inconclusive |
| any_open | 0.750 | 0.000 | 0.750 | [-1.000, 1.000] | ± 0.1 | inconclusive |
| find_actions | 0.000 | 0.000 | 0.000 | [-10.000, 10.000] | ± 0.35 | inconclusive |
| site_query_share | 0.796 | 1.000 | -0.204 | [-1.000, 1.000] | ± 0.15 | inconclusive |
| citation_domains | 2.583 | 2.500 | 0.083 | [-10.000, 10.000] | ± 0.5 | inconclusive |
| target_mention | 1.000 | 0.833 | 0.167 | [-1.000, 1.000] | ± 0.1 | inconclusive |
| entity_mentions | 2.583 | 2.000 | 0.583 | [-10.000, 10.000] | ± 0.5 | inconclusive |
| answer_words | 732.083 | 665.333 | 66.750 | [-1000.000, 1000.000] | ± 100 | inconclusive |
| completed | 1.000 | 1.000 | 0.000 | [-1.000, 1.000] | ± 0.05 | inconclusive |
| budget_limited | 0.000 | 0.000 | 0.000 | [-1.000, 1.000] | ± 0.05 | inconclusive |
| search_count_distribution | distribution | distribution | 0.333 | [0.000, 1.000] | ≤ 0.15 | inconclusive |
| open_count_distribution | distribution | distribution | 0.750 | [0.000, 1.000] | ≤ 0.1 | inconclusive |
| citation_domain_distribution | distribution | distribution | 0.113 | [0.000, 1.000] | ≤ 0.15 | inconclusive |
| entity_distribution | distribution | distribution | 0.077 | [0.000, 1.000] | ≤ 0.15 | inconclusive |
| custom_completed_quality | — | — | 1.000 | [0.000, 1.000] | minimum 0.95 | inconclusive |
| custom_budget_limited_quality | — | — | 0.000 | [0.000, 1.000] | maximum 0.05 | inconclusive |
| live_completed_quality | — | — | 1.000 | [0.000, 1.000] | minimum 0.95 | inconclusive |
| live_budget_limited_quality | — | — | 0.000 | [0.000, 1.000] | maximum 0.05 | inconclusive |

## Validity gates

- exploratory_split_not_confirmatory
- representative_independent_sampling_not_declared
- too_few_independent_questions
- too_few_questions_in_category:branded
- too_few_questions_in_category:comparison
- too_few_questions_in_category:unbranded
- values_exceed_registered_caps

## Point estimates needing attention

- search_actions
- open_actions
- any_open
- site_query_share
- target_mention
- entity_mentions
- search_count_distribution
- open_count_distribution

## Category checks

| Category | Equivalent | Different | Inconclusive |
|---|---:|---:|---:|
| branded | 0 | 0 | 20 |
| comparison | 0 | 0 | 20 |
| unbranded | 0 | 0 | 20 |

## Live baseline repeatability

Repeated runs of hosted Luna are compared with each other; no assumption of deterministic answers is made.

| Metric | Mean absolute live/live repeat difference | Questions |
|---|---:|---:|
| search_queries | 1.500 | 6 |
| search_actions | 0.333 | 6 |
| open_actions | 0.000 | 6 |
| any_open | 0.000 | 6 |
| find_actions | 0.000 | 6 |
| site_query_share | 0.000 | 6 |
| citation_domains | 0.000 | 6 |
| target_mention | 0.000 | 6 |
| entity_mentions | 0.000 | 6 |
| answer_words | 77.667 | 6 |
| completed | 0.000 | 6 |
| budget_limited | 0.000 | 6 |

## Corpus coverage diagnostic

62/297 reported hosted source URLs match a snapshot page.

URL overlap ignores query, scheme and fragment. It does not establish identical content, complete candidate coverage or actual reading.

## Sample-size planning

Optimistic precision floor assuming zero difference and zero variance (perfect reliability for quality gates). Actual variance or a gap increases sample requirements; a gap outside tolerance requires a design change. Counts are independent questions per scope, not model repetitions. This is not a power calculation.

The strictest registered check requires at least 1805 questions per evaluated scope even in this optimistic scenario. The configured minimum question count is only an eligibility floor.

## Next decision

Do not tune against held-out results or widen tolerances after seeing them. Use a calibration set to diagnose differences, then freeze a new implementation and test new held-out questions. A small or unfinished pilot cannot produce a confirmatory pass.

## Navigation diagnostics

Custom: 28 open attempts, 28 successful reads. Failure types: {}. Unexposed URL attempts: 2. Actual HTTP 404s: 0.

Open-attempt equivalence is not successful-read equivalence. The search seed is fixed; live navigation can grow the shared untreated cache. Hosted HTTP success is not assumed from tool completion.
