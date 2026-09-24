# Exploratory calibration

New-design calibration on the same frozen corpus and questions, reusing hosted responses. Implementation and runner settings may change; this is not a one-factor causal ablation.

Reuses a recorded hosted reference. Selected after seeing pilot results; not a new holdout, confidence test or proof of transfer. Each row uses questions with all repetitions measurable in all three groups. Reliability rows include failures.

Candidate statuses: {'completed': 23, 'round_limit_reached': 1}

| Metric | Original custom | Candidate custom | Hosted | Matched questions |
|---|---:|---:|---:|---:|
| search_queries | 2.182 | 2.591 | 2.409 | 11 |
| search_actions | 1.864 | 1.773 | 1.273 | 11 |
| open_actions | 1.636 | 0.909 | 0.455 | 11 |
| any_open | 0.682 | 0.409 | 0.455 | 11 |
| find_actions | 0.000 | 0.000 | 0.000 | 11 |
| site_query_share | 0.818 | 0.818 | 0.970 | 11 |
| citation_domains | 1.545 | 1.591 | 1.591 | 11 |
| target_mention | 0.364 | 0.364 | 0.364 | 11 |
| entity_mentions | 1.364 | 1.364 | 1.364 | 11 |
| answer_words | 363.591 | 352.955 | 340.409 | 11 |
| completed | 1.000 | 0.958 | 1.000 | 12 |
| budget_limited | 0.000 | 0.042 | 0.000 | 12 |
