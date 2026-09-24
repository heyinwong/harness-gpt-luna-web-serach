# Behavioural validation

**Verdict: INCONCLUSIVE**

Registered simultaneous confidence level: 95%. 48/48 runs recorded across 12 questions.

Confidence is coverage of registered metric bounds under the sampling assumptions; it is not a probability that two agents are identical or that results transfer to all future designs.

Scope: Authored Australian savings calibration questions across selected providers; unrestricted hosted web search versus a bounded observed corpus. Not a representative holdout or ChatGPT product validation.

## Overall metrics

Differences are custom minus live. TV is total variation distance (0 identical, 1 disjoint). Count means are capped as registered; raw values remain in the JSON.

| Metric | Custom | Live | Difference / TV | Simultaneous interval | Tolerance | Verdict |
|---|---:|---:|---:|---|---|---|
| search_queries | 3.000 | 2.727 | 0.273 | [-20.000, 20.000] | ± 1.5 | inconclusive |
| search_actions | 2.818 | 1.318 | 1.500 | [-12.000, 12.000] | ± 1.0 | inconclusive |
| open_actions | 2.773 | 0.409 | 2.364 | [-10.000, 10.000] | ± 0.35 | inconclusive |
| any_open | 0.909 | 0.409 | 0.500 | [-1.000, 1.000] | ± 0.1 | inconclusive |
| find_actions | 0.227 | 0.091 | 0.136 | [-10.000, 10.000] | ± 0.35 | inconclusive |
| site_query_share | 0.790 | 0.920 | -0.130 | [-1.000, 1.000] | ± 0.15 | inconclusive |
| citation_domains | 1.545 | 1.636 | -0.091 | [-10.000, 10.000] | ± 0.5 | inconclusive |
| target_mention | 0.455 | 0.455 | 0.000 | [-1.000, 1.000] | ± 0.1 | inconclusive |
| entity_mentions | 1.364 | 1.364 | 0.000 | [-10.000, 10.000] | ± 0.5 | inconclusive |
| answer_words | 356.909 | 375.227 | -18.318 | [-1000.000, 1000.000] | ± 100 | inconclusive |
| completed | 0.958 | 1.000 | -0.042 | [-1.000, 1.000] | ± 0.05 | inconclusive |
| budget_limited | 0.042 | 0.000 | 0.042 | [-1.000, 1.000] | ± 0.05 | inconclusive |
| search_count_distribution | distribution | distribution | 0.182 | [0.000, 1.000] | ≤ 0.15 | inconclusive |
| open_count_distribution | distribution | distribution | 0.818 | [0.000, 1.000] | ≤ 0.1 | inconclusive |
| citation_domain_distribution | distribution | distribution | 0.083 | [0.000, 1.000] | ≤ 0.15 | inconclusive |
| entity_distribution | distribution | distribution | 0.000 | [0.000, 1.000] | ≤ 0.15 | inconclusive |
| custom_completed_quality | — | — | 0.958 | [0.000, 1.000] | minimum 0.95 | inconclusive |
| custom_budget_limited_quality | — | — | 0.042 | [0.000, 1.000] | maximum 0.05 | inconclusive |
| live_completed_quality | — | — | 1.000 | [0.000, 1.000] | minimum 0.95 | inconclusive |
| live_budget_limited_quality | — | — | 0.000 | [0.000, 1.000] | maximum 0.05 | inconclusive |

## Validity gates

- exploratory_split_not_confirmatory
- missing_metric_data:lookup:answer_words
- missing_metric_data:lookup:any_open
- missing_metric_data:lookup:citation_domain_distribution
- missing_metric_data:lookup:citation_domains
- missing_metric_data:lookup:entity_distribution
- missing_metric_data:lookup:entity_mentions
- missing_metric_data:lookup:find_actions
- missing_metric_data:lookup:open_actions
- missing_metric_data:lookup:open_count_distribution
- missing_metric_data:lookup:search_actions
- missing_metric_data:lookup:search_count_distribution
- missing_metric_data:lookup:search_queries
- missing_metric_data:lookup:site_query_share
- missing_metric_data:lookup:target_mention
- missing_metric_data:overall:answer_words
- missing_metric_data:overall:any_open
- missing_metric_data:overall:citation_domain_distribution
- missing_metric_data:overall:citation_domains
- missing_metric_data:overall:entity_distribution
- missing_metric_data:overall:entity_mentions
- missing_metric_data:overall:find_actions
- missing_metric_data:overall:open_actions
- missing_metric_data:overall:open_count_distribution
- missing_metric_data:overall:search_actions
- missing_metric_data:overall:search_count_distribution
- missing_metric_data:overall:search_queries
- missing_metric_data:overall:site_query_share
- missing_metric_data:overall:target_mention
- representative_independent_sampling_not_declared
- too_few_independent_questions
- too_few_questions_in_category:comparison
- too_few_questions_in_category:conditions
- too_few_questions_in_category:lookup

## Point estimates needing attention

- search_actions
- open_actions
- any_open
- search_count_distribution
- open_count_distribution

## Category checks

| Category | Equivalent | Different | Inconclusive |
|---|---:|---:|---:|
| comparison | 0 | 0 | 20 |
| conditions | 0 | 0 | 20 |
| lookup | 0 | 0 | 20 |

## Live baseline repeatability

Repeated runs of hosted Luna are compared with each other; no assumption of deterministic answers is made.

| Metric | Mean absolute live/live repeat difference | Questions |
|---|---:|---:|
| search_queries | 1.167 | 12 |
| search_actions | 0.417 | 12 |
| open_actions | 0.500 | 12 |
| any_open | 0.417 | 12 |
| find_actions | 0.167 | 12 |
| site_query_share | 0.090 | 12 |
| citation_domains | 0.167 | 12 |
| target_mention | 0.000 | 12 |
| entity_mentions | 0.000 | 12 |
| answer_words | 38.500 | 12 |
| completed | 0.000 | 12 |
| budget_limited | 0.000 | 12 |

## Corpus coverage diagnostic

80/334 reported hosted source URLs match a snapshot page.

URL overlap ignores query, scheme and fragment. It does not establish identical content, complete candidate coverage or actual reading.

## Sample-size planning

Optimistic precision floor assuming zero difference and zero variance (perfect reliability for quality gates). Actual variance or a gap increases sample requirements; a gap outside tolerance requires a design change. Counts are independent questions per scope, not model repetitions. This is not a power calculation.

The strictest registered check requires at least 1805 questions per evaluated scope even in this optimistic scenario. The configured minimum question count is only an eligibility floor.

## Next decision

Do not tune against held-out results or widen tolerances after seeing them. Use a calibration set to diagnose differences, then freeze a new implementation and test new held-out questions. A small or unfinished pilot cannot produce a confirmatory pass.
