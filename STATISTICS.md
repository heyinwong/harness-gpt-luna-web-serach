# What the confidence statement means

The validator asks whether **every registered observable metric** lies within a practically acceptable difference, overall and within each registered question category. It never reports “95% probability this is ChatGPT.” A future passing report supports similarity for the tested model/configuration, question population, information environment and metrics, under the stated sampling assumptions. It does not recover the hidden search payload or establish the same internal decision policy.

## Sampling and intervals

Use independently sampled, representative **new questions** for confirmation. Average repetitions within each question before computing paired custom-minus-hosted differences. Two repetitions of 12 questions remain 12 question clusters. The pilot's hand-written convenience questions deliberately cannot yield a confirmatory pass. Merely changing its `split` label is not a new holdout.

`validation/statistics.py` uses the finite-sample empirical Bernstein bound from [Maurer and Pontil (2009), Theorem 4](https://arxiv.org/pdf/0907.3740). For bounded observations with support width R and sample variance v, the two-sided radius is:

`sqrt(2*v*log(4/alpha)/n) + 7*R*log(4/alpha)/(3*(n-1))`.

Bonferroni divides the total error probability among every scalar, distribution coordinate and absolute reliability check, for overall and every category. Their dependence does not invalidate the union bound. Independent, identically distributed question clusters are an assumption; data files cannot verify representativeness or independence. The overall calculation assumes the declared sample represents the intended overall mixture; purposive fixed quotas need a separate stratified estimator before population claims.

This method is deliberately conservative and works with discrete, zero-inflated counts. Identical small samples still have uncertainty. The report includes an optimistic precision floor; substantial numbers of independent questions may be required. The floor assumes zero variance and zero gap and is **not** a power guarantee, a recommended purchase or a promise that another run will pass. A less conservative method would require its own prespecified assumptions, implementation and validation; never select one after seeing which produces a pass.

## Mean and distribution checks

Count means use registered upper caps. Actual cap exceedances block certification, so clipping cannot hide a mismatch. The cap does not limit the agent's actions. Distribution bins retain an overflow category. Scalar bounds wholly inside ±margin pass; wholly outside are different; overlapping are inconclusive. Distribution checks use total variation (TV), half the sum of absolute differences in bin probability. Simultaneous bin-difference intervals propagate into TV bounds. Equal means can conceal different distributions, so both are required.

Default practical tolerances are provisional design choices: 1.5 individual queries, 0.35 opens, 10 percentage points for opening/target mention, and 0.10–0.15 TV. They are fixed before the pilot, not inferred from its results. Review their business meaning before freezing a new study. They are not validated universal thresholds. The previously reported 2.2-open gap would greatly exceed the 0.35-open tolerance.

## Observable metrics

- Search queries versus search batches; missing hosted query lists are missing, not zero.
- Open/click attempts, any-open probability, find counts, count distributions and within-answer `site:` query fraction.
- Unique cited hosts (`www` stripped), fractional citation-domain distribution with OTHER/NONE. A citation is not proof of a read; hosted `sources` is not a complete ranked search result list.
- Case-target mention, distinct configured entity names, fractional entity distribution with NONE. Aliases use case-insensitive word boundaries; link targets are excluded, link labels remain. These are names, not semantic relevance or endorsement judgments.
- Approximate alphanumeric answer length; completion and budget-boundary rates over all recorded attempts.
- Descriptive live/live repeat differences, latency, estimated spend, local open failures and explicit product-to-hub clicks.

Absolute reliability gates also require high completion and low budget censoring. Equal failure rates cannot certify two broken agents. Failure/censored answers are excluded from behavioural means with explicit missing-data flags, which block an overall pass; their reliability outcomes remain counted. Every paired repetition must be present. No silent complete-case certification.

`award_report.py` separately summarizes manually scored award correctness and unsupported product claims across prespecified treatment contrasts. It uses the same question-cluster interval method. The scoring packet hides arm labels but answer wording may reveal treatment; it is partial blinding, not guaranteed blinding. Have reviewers judge against the actual award source, not only the intervention sentence. Behavioural similarity is necessary evidence for transfer, not a substitute for checking answer correctness or treatment robustness.

## Validation of the validator

Offline tests exercise zero-variance small samples, missing data, tampered/duplicate traces, cap exceedance, censored runs, query batching, equal means with disjoint distributions, large matching/mismatching synthetic samples through the complete validator, a seeded Bernoulli coverage simulation, and budget reservations. The mathematical coverage guarantee comes from the bound and its assumptions; a simulation/test pass alone does not prove it for all settings.
