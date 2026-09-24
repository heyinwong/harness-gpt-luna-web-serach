# Exploratory calibration

One-factor snippet-length calibration; same frozen corpus and recorded hosted responses.

Reuses a recorded hosted reference. Selected after seeing pilot results; not a new holdout, confidence test or proof of transfer. Each row uses questions with all repetitions measurable in all three groups. Reliability rows include failures.

Candidate statuses: {'failed': 1, 'completed': 12}

| Metric | Original custom | Candidate custom | Hosted | Matched questions |
|---|---:|---:|---:|---:|
| search_queries | 4.375 | 2.750 | 2.625 | 4 |
| search_actions | 4.000 | 2.750 | 1.250 | 4 |
| open_actions | 1.875 | 0.750 | 0.625 | 4 |
| any_open | 0.750 | 0.625 | 0.625 | 4 |
| find_actions | 0.000 | 0.125 | 0.000 | 4 |
| site_query_share | 0.615 | 0.698 | 0.781 | 4 |
| citation_domains | 1.500 | 1.625 | 1.625 | 4 |
| target_mention | 0.250 | 0.250 | 0.250 | 4 |
| entity_mentions | 1.250 | 1.250 | 1.250 | 4 |
| answer_words | 338.000 | 352.875 | 354.000 | 4 |
| completed | 1.000 | 0.900 | 1.000 | 5 |
| budget_limited | 0.000 | 0.000 | 0.000 | 5 |
