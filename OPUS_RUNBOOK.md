> **Current CommBank workflow:** use [HANDOFF.md](HANDOFF.md). This file is the longer technical reference and includes historical documentation-pilot commands. Do not use those historical settings as the current bank configuration.

# Operator runbook: fidelity validation and award experiment

**CommBank update:** Start with [COMMBANK_RUNBOOK.md](COMMBANK_RUNBOOK.md) for the Luna-informed 69-document competitor corpus, reproducible builder, six placement conditions and bank-specific calibration. The original documentation pilot below remains historical evidence; it is not a bank-domain fidelity pass.

Read `HANDOFF.md`, `README.md`, `STATISTICS.md` and `VALIDATION.md` first. Public clones include numeric evidence in `evidence/`; they do not include the original ignored `results/` directories. Generate fresh snapshots/runs or obtain those private artifacts from the owner before using commands that refer to existing results. Opus operates the repository; **the experimental decision model remains `gpt-5.6-luna`**. Switching the decision model to Opus creates a different experiment. Do not substitute models, adjust the open count by imposing a quota, or describe a pilot as a confidence-certified replica of ChatGPT.

## 1. Setup and free checks

Run from the repository directory using Python 3.11+:

```sh
python3 -m pip install -r requirements-validation.txt
python3 -m unittest discover -s tests -v
python3 suite.py
```

The core agent uses the standard library. Beautiful Soup is required for HTML snapshots and their regression tests. A local `.env` or `.env.local` holds the API key (raw key or `OPENAI_API_KEY=...`). Never print, source, stage or copy the key into reports. No API requests occur without `--allow-paid`.

Inspect the existing reports under `results/public_web_pilot_v1/` and `results/public_web_pilot_v2/` and `results/public_web_pilot_v3/`; do not overwrite them. They are ignored by Git, so transfer them separately if moving machines, without `.env`. Summary findings are in `VALIDATION.md`.

## 2. Assemble the actual evidence environment

The original 53-page bank corpus and 160 questions are **not in this repository**. Obtain those project inputs before calling anything the original award experiment. The supplied `sample_corpus.json` and `pilot_questions.json` are fictional plumbing fixtures.

Create two separate inputs:

1. **Faithful reference corpus**: actual current page text, original absolute URLs, link labels/targets and capture provenance. Use generic `reference` mode; no award role or placeholder is required. Do not remove existing awards for fidelity calibration. For HTML URLs, `benchmark.py snapshot` preserves inline text, semantic asides/footnotes and fragment-to-offset anchors. It selects main/article/body content and removes scripts, styles and navigation/form/header/footer containers; inspect excluded material if the study concerns those locations. It is a declared text extraction policy, not an exact reconstruction of hosted-search parsing. Missing pages must remain documented; never invent their contents.
2. **Experimental corpus**: copy the real corpus, designate one product and one hub, insert exactly one `{{AWARD_BLOCK}}`, and provide the exact `award_sentence`. Review surrounding award references for treatment contamination. Keep the original reference corpus unchanged. If editing text before an anchor, regenerate its offsets; stale offsets are not valid navigation metadata.

Inspect coverage against hosted consulted-source URLs. The reported overlap is only a diagnostic: same URL does not imply identical text and unseen candidate pages are not exposed. A domain-restricted `web_search` comparison is a separate declared baseline; it does not replace unrestricted `web_search_preview` as a test of the original target.

## 3. Calibrate, then freeze a genuinely new holdout

Copy `benchmarks/public_web_pilot_v3.json` into a task-specific profile. Replace scope, cases, categories, entity aliases, target aliases, citation domain groups and snapshot URLs. Keep field meanings consistent. Set `split` to `calibration` while tuning. Do not put held-out questions into calibration, including paraphrases of the same question that leak the same task.

Decide practical equivalence tolerances and the intended question population **before** outcomes. The provided defaults are provisional. Include navigational, comparison, conditions and recommendation intents relevant to the bank study, with questions that can discover awards incidentally. Avoid making every question explicitly ask about an award. Use fresh independent questions for validation; repeated calls cannot replace question diversity.

```sh
python3 benchmark.py snapshot --profile benchmarks/my_calibration.json --out results/my_reference.json
python3 benchmark.py freeze --profile benchmarks/my_calibration.json --corpus results/my_reference.json --out-dir results/my_calibration_v1
python3 benchmark.py run --run-dir results/my_calibration_v1 --budget-usd 1
```

That last command is a plan. Add `--allow-paid` only within the user's authorized API budget. The benchmark freezes profile, code and corpus hashes. Editing an implementation requires a new frozen directory; old traces cannot be silently reused as the new design. The budget ledger persists across resume. A pending/unknown request or transport failure stops execution and needs inspection; there is no hidden retry. The benchmark retains model-cutoff attempts as censored observations and proceeds to the next planned job; the award suite stops on incomplete output for inspection. Each new directory has a separate ledger, so subtract earlier study spending from the remaining user budget.

Use `report.py` for the open audit:

```sh
python3 report.py results/my_calibration_v1/traces/*.json --out results/my_calibration_v1/open-audit.md
python3 benchmark.py report --run-dir results/my_calibration_v1
```

Read actual excerpts before diagnosing opens. Check page coverage, query semantics, snippet sufficiency, anchor navigation, broken links, duplicate reads and whitespace. Change the diagnosed cause, never a metric quota. Preserve failed trials.

For a cheaper **exploratory** one-factor excerpt-length comparison, `calibrate.py` reuses the recorded hosted responses and changes only custom excerpt length on the exact same corpus/code. It rejects a validation split and reports no confidence certificate:

```sh
python3 calibrate.py --baseline-dir results/public_web_pilot_v3 --out-dir results/my_excerpt_trial --snippet-chars 6000 --budget-usd 0.25
```

This is plan-only until `--allow-paid` is added within an authorized budget. Do not assume 6,000 characters is better: inspect the recorded `results/excerpt_calibration_v5/` findings. Existing study budgets do not authorize new spending automatically. A targeted coverage diagnostic is recorded under `results/git_coverage_diagnostic_v4/`; it must not replace the full pilot or be pooled as a new holdout.

After fixing the implementation, register new independently sampled held-out cases with `split: "validation"` and a truthful `sampling: "independent_representative_holdout"` declaration. Supply the real selection procedure in profile metadata. A label cannot establish those assumptions. Freeze and run once; do not repeatedly peek and keep collecting until it passes. The sample-size report gives a conservative optimistic floor, not guaranteed power. Get a separate budget for a larger study; the original US$2 authorization was only for the first pilot and its corrective rerun.

A confirmatory pass requires every registered overall/category interval inside tolerance, all repetitions observed, no metric gaps/censoring/cap exceedances, and absolute reliability gates. A failed or inconclusive result remains failed/inconclusive. If unsuitable for transfer, award results must be described as effects within the controlled harness.

## 4. Run the five-arm award experiment

Keep fidelity tuning separate from treatment outcomes. Prespecify primary outcome (correct, product-relevant award representation), secondary mechanism outcomes, practical non-inferiority margin and contrasts. Do not use raw brand mention as award correctness.

Create real questions as a JSON array of `{ "id": "q01", "category": "conditions", "question": "..." }`. First inspect the full plan:

```sh
python3 suite.py --corpus my_award_corpus.json --questions my_award_questions.json --repeats 3 --max-runs 1000 --budget-usd 1 --stop-after-estimated-usd 1 --out-dir results/award_v1
```

After authorizing the actual study budget, set both dollar values to that amount and add `--allow-paid`. The reservation budget is checked before each request; the extra estimated-spend stop is checked between runs. Settings must match the validated configuration. Fresh state is used for each question/arm/repetition; job order is shuffled. `--include-live` adds a current reference per question/repetition, but hosted search cannot receive local arm treatments.

No need to introduce another model for automatic grading. Prepare a human-review packet:

```sh
python3 award_report.py prepare --suite-dir results/award_v1 --corpus my_award_corpus.json --out results/award_v1/scores.json
```

Review the answer against the real award source. Fill `correct_relevant_award` and `unsupported_product_claim` with 0 or 1, plus reviewer and evidence. The packet omits arm labels; keep trace-to-arm mappings away from reviewers and use two reviewers/adjudication where feasible. Answer content may reveal the arm, so blinding is imperfect. Null is unreviewed, never a zero. Preserve the answer and question verbatim.

```sh
python3 award_report.py analyze --suite-dir results/award_v1 --scores results/award_v1/scores.json --out results/award_v1/effects.json
```

The analysis reports paired question-level rates and simultaneous intervals for inline–baseline, no_link–baseline, and each hub arm–inline. It flags missing/failed/censored runs and does not silently approve non-inferiority. Consult the trace metrics and open audit for explicit navigation: direct opening a hub is not proof of following its product link; descriptive link text may expose the award before any opening.

## 5. Report what was actually established

Deliver corpus and code hashes, questions/categories, configuration, all trials including failures, completion and censoring rates, averages **and** distributions, interval/tolerance decisions, live/live variability, coverage limits, reviewer rubric, treatment contrasts and costs. Preselect plausible retrieval/snippet sensitivity settings and check whether award contrasts change; use a separately authorized budget. If the conclusion reverses, report it.

Do not claim all future designs are validated by one pass. The framework is reusable; changing corpus, task population, model, tool semantics or retrieval settings requires a new applicable validation. API hosted Luna is the observable reference here. Matching it does not establish equivalence to every ChatGPT product configuration.
