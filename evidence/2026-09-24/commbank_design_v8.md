# Exploratory calibration

New-design calibration on the same frozen corpus and questions, reusing hosted responses. Implementation and runner settings may change; this is not a one-factor causal ablation.

Reuses a recorded hosted reference. Selected after seeing pilot results; not a new holdout, confidence test or proof of transfer. Each row uses questions with all repetitions measurable in all three groups. Reliability rows include failures.

Candidate statuses: {'completed': 24}

| Metric | Original custom | Candidate custom | Hosted | Matched questions |
|---|---:|---:|---:|---:|
| search_queries | 2.083 | 1.875 | 2.542 | 12 |
| search_actions | 1.792 | 1.875 | 1.292 | 12 |
| open_actions | 1.958 | 0.875 | 0.500 | 12 |
| any_open | 0.708 | 0.542 | 0.500 | 12 |
| find_actions | 0.208 | 0.125 | 0.042 | 12 |
| site_query_share | 0.833 | 0.903 | 0.972 | 12 |
| citation_domains | 1.500 | 1.542 | 1.542 | 12 |
| target_mention | 0.417 | 0.417 | 0.417 | 12 |
| entity_mentions | 1.333 | 1.333 | 1.333 | 12 |
| answer_words | 375.750 | 348.292 | 356.292 | 12 |
| completed | 1.000 | 1.000 | 1.000 | 12 |
| budget_limited | 0.000 | 0.000 | 0.000 | 12 |
