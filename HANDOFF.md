# Start here, Opus

## Current decision

This is a working controlled-search experiment platform. **It has not passed as a substitute for hosted GPT-5.6 Luna or the ChatGPT product.** The next job is to reduce and explain the retrieval/reading gap before claiming award findings transfer to real Luna. Do not begin by buying a larger validation sample: the observed mismatch needs engineering work first.

Read, in order:

1. `VALIDATION.md` — actual outcomes, failures, costs and scope.
2. `evidence/2026-09-24/public_web_pilot_v3.json` — public numeric evidence from the complete paired pilot.
3. `DESIGN.md` — controlled interventions and observable mechanisms.
4. `OPUS_RUNBOOK.md` — exact commands and scoring workflow.
5. `STATISTICS.md` — what the confidence bounds do and do not mean.

## What exists

Python 3.11+; custom `search`, `open`, `click`, `find`; BM25 retrieval; local page snapshots; five award-placement arms; hosted Responses reference; immutable paired benchmark profiles; repeated runs; averages and distribution comparisons; cost reservations; exact local evidence audits; and manually scored treatment contrasts. Opus operates the code; Luna remains the experimental decision model unless a new experiment explicitly changes it.

Public evidence is available in `evidence/`. Raw page snapshots, API responses and local traces are not published. Commands referring to `results/...` in the operator runbook require those original private files or freshly generated runs. Never infer that the public numeric exports are raw traces.

## Findings to preserve

On 11 questions with all repetitions measurable in the main pilot, queries averaged **1.50 custom versus 1.23 hosted**, while opens averaged **1.55 versus 0.23**. Custom completed 22/24 attempts and hosted completed 24/24. The Git fetch/pull question hit the custom round boundary twice.

Real defects found and fixed: broken inline HTML text, unsupported `site:domain/path`, lost fragment navigation, and discarded semantic-aside footnotes. The CSV explanation was absent until the footnote fix; both later repetitions completed. These were information-loss defects, not evidence of an intrinsic model preference for opening pages.

Adding Git's configuration page did **not** resolve its round-limit failures. Increasing excerpt length from 1,200 to 6,000 characters reduced opens **1.72 → 1.06** on nine common questions, but hosted remained **0.28**. The longer-excerpt trial used more tokens and stopped at its reservation boundary. It was not adopted as a validated default.

## Recommended next work

1. **Establish the real target environment.** Obtain the original bank corpus/questions. The fictional fixtures and documentation pilot are not the original 53-page/160-question experiment. Build an unmodified reference snapshot separately from award treatments.
2. **Audit extraction and useful passage selection.** Check hidden menus, version histories, tables, footnotes, cross-page references and important link labels. Keep source-to-text provenance and known-answer passage checks. Our current extractor emits cleaned text with Markdown-style links, not a full semantic Markdown conversion. Git page snapshots contain substantial navigation/version text.
3. **Improve evidence retrieval, one change at a time.** Evaluate paragraph/section retrieval that surfaces complementary evidence rather than one keyword-dense character window. Preserve nearby headings, caveats and links. Audit coverage of pages actually needed to answer the target questions. A richer search provider is a possible later option if a bounded local corpus cannot approximate the intended search environment; it is not implemented here.
4. **Calibrate against a matched hosted reference.** Measure completion, failed opens, query counts, any-open probability, open-count distribution, mentions/citations and answer correctness. Audit the new evidence obtained by each open. Native search payloads are not observable in our trace, so equal action counts cannot prove equal reading. Never impose an open quota to match a target mean.
5. **Freeze a new holdout only after improvement.** Prespecify representative question sampling and practical margins. Include new questions, not paraphrases leaked from tuning. Budget units differ between custom model rounds and native tool calls; report censoring. The conservative interval method can require many independent questions; do not reinterpret its sample-size floor as a purchase recommendation.
6. **Then run the award arms and score correctness.** Use the human rubric, paired question-level comparisons and predefined sensitivity settings. Until applicable fidelity validation passes, describe effects as effects inside this harness.

## Free acceptance checks

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-validation.txt
python -m unittest discover -s tests -v
python search_lab.py demo --out results/handoff-demo.json
python report.py results/handoff-demo.json --out results/handoff-demo.md
python suite.py
```

The suite command is plan-only. The mocked suite tests and scripted demo do not constitute agent behaviour. The publication pass spends no additional API credit. The prior US$2 allowance was for the recorded pilot work; agree a new budget before new paid trials. Never request a key in chat or publish `.env`.

## A prompt the owner can give the next agent

> Read HANDOFF.md, VALIDATION.md, the public evidence, and OPUS_RUNBOOK.md. Continue this controlled-search harness without claiming it already reproduces hosted Luna. First run the offline checks and audit extraction, source coverage and passage usefulness against the actual bank corpus I provide. Propose and implement one evidence-delivery improvement at a time, preserve all failed runs, and measure the same registered metrics on matched questions. Keep the experimental model as GPT-5.6 Luna. Do not force the number of opens or tune on the holdout. Request a new explicit API budget before paid trials. Once fidelity is adequate for the intended scope, run the five award-placement arms and use the documented correctness rubric and paired analysis.
