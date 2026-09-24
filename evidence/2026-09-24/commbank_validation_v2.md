# Behavioural validation

**Verdict: INCONCLUSIVE**

Registered simultaneous confidence level: 95%. 5/72 runs recorded across 18 questions.

Confidence is coverage of registered metric bounds under the sampling assumptions; it is not a probability that two agents are identical or that results transfer to all future designs.

Scope: Unmodified-page check on the 18 previously authored award-experiment questions. Unseen by candidate paid tuning; finite task-set evidence, not representative ChatGPT population validation.

## Overall metrics

Differences are custom minus live. TV is total variation distance (0 identical, 1 disjoint). Count means are capped as registered; raw values remain in the JSON.

| Metric | Custom | Live | Difference / TV | Simultaneous interval | Tolerance | Verdict |
|---|---:|---:|---:|---|---|---|
| search_queries | — | — | — | [-20.000, 20.000] | ± 1.5 | inconclusive |
| search_actions | — | — | — | [-12.000, 12.000] | ± 1.0 | inconclusive |
| open_actions | — | — | — | [-10.000, 10.000] | ± 0.35 | inconclusive |
| any_open | — | — | — | [-1.000, 1.000] | ± 0.1 | inconclusive |
| find_actions | — | — | — | [-10.000, 10.000] | ± 0.35 | inconclusive |
| site_query_share | — | — | — | [-1.000, 1.000] | ± 0.15 | inconclusive |
| citation_domains | — | — | — | [-10.000, 10.000] | ± 0.5 | inconclusive |
| target_mention | — | — | — | [-1.000, 1.000] | ± 0.1 | inconclusive |
| entity_mentions | — | — | — | [-10.000, 10.000] | ± 0.5 | inconclusive |
| answer_words | — | — | — | [-1000.000, 1000.000] | ± 100 | inconclusive |
| completed | — | — | — | [-1.000, 1.000] | ± 0.05 | inconclusive |
| budget_limited | — | — | — | [-1.000, 1.000] | ± 0.05 | inconclusive |
| search_count_distribution | distribution | distribution | — | [0.000, 1.000] | ≤ 0.15 | inconclusive |
| open_count_distribution | distribution | distribution | — | [0.000, 1.000] | ≤ 0.1 | inconclusive |
| citation_domain_distribution | distribution | distribution | — | [0.000, 1.000] | ≤ 0.15 | inconclusive |
| entity_distribution | distribution | distribution | — | [0.000, 1.000] | ≤ 0.15 | inconclusive |
| custom_completed_quality | — | — | — | [0.000, 1.000] | minimum 0.95 | inconclusive |
| custom_budget_limited_quality | — | — | — | [0.000, 1.000] | maximum 0.05 | inconclusive |
| live_completed_quality | — | — | — | [0.000, 1.000] | minimum 0.95 | inconclusive |
| live_budget_limited_quality | — | — | — | [0.000, 1.000] | maximum 0.05 | inconclusive |

## Validity gates

- missing_metric_data:branded:answer_words
- missing_metric_data:branded:any_open
- missing_metric_data:branded:budget_limited
- missing_metric_data:branded:citation_domain_distribution
- missing_metric_data:branded:citation_domains
- missing_metric_data:branded:completed
- missing_metric_data:branded:entity_distribution
- missing_metric_data:branded:entity_mentions
- missing_metric_data:branded:find_actions
- missing_metric_data:branded:open_actions
- missing_metric_data:branded:open_count_distribution
- missing_metric_data:branded:search_actions
- missing_metric_data:branded:search_count_distribution
- missing_metric_data:branded:search_queries
- missing_metric_data:branded:site_query_share
- missing_metric_data:branded:target_mention
- missing_metric_data:comparison:answer_words
- missing_metric_data:comparison:any_open
- missing_metric_data:comparison:budget_limited
- missing_metric_data:comparison:citation_domain_distribution
- missing_metric_data:comparison:citation_domains
- missing_metric_data:comparison:completed
- missing_metric_data:comparison:entity_distribution
- missing_metric_data:comparison:entity_mentions
- missing_metric_data:comparison:find_actions
- missing_metric_data:comparison:open_actions
- missing_metric_data:comparison:open_count_distribution
- missing_metric_data:comparison:search_actions
- missing_metric_data:comparison:search_count_distribution
- missing_metric_data:comparison:search_queries
- missing_metric_data:comparison:site_query_share
- missing_metric_data:comparison:target_mention
- missing_metric_data:overall:answer_words
- missing_metric_data:overall:any_open
- missing_metric_data:overall:budget_limited
- missing_metric_data:overall:citation_domain_distribution
- missing_metric_data:overall:citation_domains
- missing_metric_data:overall:completed
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
- missing_metric_data:unbranded:answer_words
- missing_metric_data:unbranded:any_open
- missing_metric_data:unbranded:budget_limited
- missing_metric_data:unbranded:citation_domain_distribution
- missing_metric_data:unbranded:citation_domains
- missing_metric_data:unbranded:completed
- missing_metric_data:unbranded:entity_distribution
- missing_metric_data:unbranded:entity_mentions
- missing_metric_data:unbranded:find_actions
- missing_metric_data:unbranded:open_actions
- missing_metric_data:unbranded:open_count_distribution
- missing_metric_data:unbranded:search_actions
- missing_metric_data:unbranded:search_count_distribution
- missing_metric_data:unbranded:search_queries
- missing_metric_data:unbranded:site_query_share
- missing_metric_data:unbranded:target_mention
- planned_runs_missing
- representative_independent_sampling_not_declared
- too_few_independent_questions
- too_few_questions_in_category:branded
- too_few_questions_in_category:comparison
- too_few_questions_in_category:unbranded

## Point estimates needing attention

None; this alone is not evidence of equivalence.

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

## Corpus coverage diagnostic

21/91 reported hosted source URLs match a snapshot page.

URL overlap ignores query, scheme and fragment. It does not establish identical content, complete candidate coverage or actual reading.

## Sample-size planning

Optimistic precision floor assuming zero difference and zero variance (perfect reliability for quality gates). Actual variance or a gap increases sample requirements; a gap outside tolerance requires a design change. Counts are independent questions per scope, not model repetitions. This is not a power calculation.

The strictest registered check requires at least 1805 questions per evaluated scope even in this optimistic scenario. The configured minimum question count is only an eligibility floor.

## Next decision

Do not tune against held-out results or widen tolerances after seeing them. Use a calibration set to diagnose differences, then freeze a new implementation and test new held-out questions. A small or unfinished pilot cannot produce a confirmatory pass.
