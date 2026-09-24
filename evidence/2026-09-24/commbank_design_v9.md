# Exploratory calibration

New-design calibration on the same frozen corpus and questions, reusing hosted responses. Implementation and runner settings may change; this is not a one-factor causal ablation.

Reuses a recorded hosted reference. Selected after seeing pilot results; not a new holdout, confidence test or proof of transfer. Each row uses questions with all repetitions measurable in all three groups. Reliability rows include failures.

Candidate statuses: {'failed': 1, 'completed': 9}

| Metric | Original custom | Candidate custom | Hosted | Matched questions |
|---|---:|---:|---:|---:|
| search_queries | 1.250 | 3.000 | 2.000 | 2 |
| search_actions | 1.250 | 2.250 | 1.250 | 2 |
| open_actions | 2.000 | 1.000 | 0.500 | 2 |
| any_open | 0.500 | 0.500 | 0.500 | 2 |
| find_actions | 0.000 | 0.000 | 0.000 | 2 |
| site_query_share | 0.750 | 0.667 | 1.000 | 2 |
| citation_domains | 1.000 | 1.000 | 1.500 | 2 |
| target_mention | 0.000 | 0.000 | 0.000 | 2 |
| entity_mentions | 1.000 | 1.000 | 1.000 | 2 |
| answer_words | 319.750 | 278.500 | 281.500 | 2 |
| completed | 1.000 | 1.000 | 1.000 | 2 |
| budget_limited | 0.000 | 0.000 | 0.000 | 2 |
