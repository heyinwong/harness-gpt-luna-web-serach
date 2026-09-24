# Behavioural validation

**Verdict: INCONCLUSIVE**

Registered simultaneous confidence level: 95%. 72/72 runs recorded across 18 questions.

Confidence is coverage of registered metric bounds under the sampling assumptions; it is not a probability that two agents are identical or that results transfer to all future designs.

Scope: Unmodified-page check on the 18 previously authored award-experiment questions. Unseen by candidate paid tuning; finite task-set evidence, not representative ChatGPT population validation.

## Overall metrics

Differences are custom minus live. TV is total variation distance (0 identical, 1 disjoint). Count means are capped as registered; raw values remain in the JSON.

| Metric | Custom | Live | Difference / TV | Simultaneous interval | Tolerance | Verdict |
|---|---:|---:|---:|---|---|---|
| search_queries | 7.278 | 7.278 | 0.000 | [-20.000, 20.000] | ± 1.5 | inconclusive |
| search_actions | 5.111 | 2.306 | 2.806 | [-12.000, 12.000] | ± 1.0 | inconclusive |
| open_actions | 1.083 | 0.306 | 0.778 | [-10.000, 10.000] | ± 0.35 | inconclusive |
| any_open | 0.278 | 0.278 | 0.000 | [-1.000, 1.000] | ± 0.1 | inconclusive |
| find_actions | 0.000 | 0.028 | -0.028 | [-10.000, 10.000] | ± 0.35 | inconclusive |
| site_query_share | 0.740 | 0.943 | -0.204 | [-1.000, 1.000] | ± 0.15 | inconclusive |
| citation_domains | 3.306 | 3.639 | -0.333 | [-10.000, 10.000] | ± 0.5 | inconclusive |
| target_mention | 0.833 | 0.833 | 0.000 | [-1.000, 1.000] | ± 0.1 | inconclusive |
| entity_mentions | 3.111 | 2.917 | 0.194 | [-10.000, 10.000] | ± 0.5 | inconclusive |
| answer_words | 726.944 | 738.917 | -11.972 | [-1000.000, 1000.000] | ± 100 | inconclusive |
| completed | 1.000 | 1.000 | 0.000 | [-1.000, 1.000] | ± 0.05 | inconclusive |
| budget_limited | 0.000 | 0.000 | 0.000 | [-1.000, 1.000] | ± 0.05 | inconclusive |
| search_count_distribution | distribution | distribution | 0.222 | [0.000, 1.000] | ≤ 0.15 | inconclusive |
| open_count_distribution | distribution | distribution | 0.250 | [0.000, 1.000] | ≤ 0.1 | inconclusive |
| citation_domain_distribution | distribution | distribution | 0.173 | [0.000, 1.000] | ≤ 0.15 | inconclusive |
| entity_distribution | distribution | distribution | 0.057 | [0.000, 1.000] | ≤ 0.15 | inconclusive |
| custom_completed_quality | — | — | 1.000 | [0.000, 1.000] | minimum 0.95 | inconclusive |
| custom_budget_limited_quality | — | — | 0.000 | [0.000, 1.000] | maximum 0.05 | inconclusive |
| live_completed_quality | — | — | 1.000 | [0.000, 1.000] | minimum 0.95 | inconclusive |
| live_budget_limited_quality | — | — | 0.000 | [0.000, 1.000] | maximum 0.05 | inconclusive |

## Validity gates

- representative_independent_sampling_not_declared
- too_few_independent_questions
- too_few_questions_in_category:branded
- too_few_questions_in_category:comparison
- too_few_questions_in_category:unbranded
- values_exceed_registered_caps

## Point estimates needing attention

- search_actions
- open_actions
- site_query_share
- search_count_distribution
- open_count_distribution
- citation_domain_distribution

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
| search_queries | 2.333 | 18 |
| search_actions | 0.833 | 18 |
| open_actions | 0.278 | 18 |
| any_open | 0.222 | 18 |
| find_actions | 0.056 | 18 |
| site_query_share | 0.052 | 18 |
| citation_domains | 0.611 | 18 |
| target_mention | 0.111 | 18 |
| entity_mentions | 0.500 | 18 |
| answer_words | 76.222 | 18 |
| completed | 0.000 | 18 |
| budget_limited | 0.000 | 18 |

## Corpus coverage diagnostic

97/705 reported hosted source URLs match a snapshot page.

URL overlap ignores query, scheme and fragment. It does not establish identical content, complete candidate coverage or actual reading.

## Sample-size planning

Optimistic precision floor assuming zero difference and zero variance (perfect reliability for quality gates). Actual variance or a gap increases sample requirements; a gap outside tolerance requires a design change. Counts are independent questions per scope, not model repetitions. This is not a power calculation.

The strictest registered check requires at least 1805 questions per evaluated scope even in this optimistic scenario. The configured minimum question count is only an eligibility floor.

## Next decision

Do not tune against held-out results or widen tolerances after seeing them. Use a calibration set to diagnose differences, then freeze a new implementation and test new held-out questions. A small or unfinished pilot cannot produce a confirmatory pass.
