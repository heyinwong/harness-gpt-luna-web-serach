# Start here, Opus

Operate this repository; keep **GPT-5.6 Luna** as the experimental model. The owner wants one usable search harness with measured similarity, not a reconstruction of ChatGPT internals.

**Open-failure audit:** In the locked comparison, 18 custom open attempts included nine `not_in_corpus` failures: eight followed exposed links and one URL was unexposed. The reported 0.50 opens/answer counts attempts; successful opens were 0.25. These are corpus misses, not verified HTTP 404s. Repair linked-page coverage in a new corpus and rerun the comparison before treating page-opening similarity as established. See [the audit](evidence/2026-09-24/commbank_open_audit.json).

## One setup

Use `context` retrieval, 6,000-character search excerpts, five results per query, 32,000-character open windows, eight model rounds and medium reasoning. Search selects source passages with their adjacent question/heading and qualifying bullets. Page ranking uses readable link labels rather than URL tracking text. `open`, `click` and `find` remain available whenever Luna needs them. Never force an open count.

The current corpus has **69 documents**, including CommBank and competitors. `reference.json` preserves the captured pages. `experiment.json` supplies the six award-placement conditions. The target is the existing **Canstar 2024 Digital Banking Bank of the Year** footnote, a bank-level award. It is visible after scrolling; this is a text-retrieval experiment, not a visual-attention experiment.

The completed 72-answer comparison found 6.47 versus 7.06 queries and 0.50 versus 0.33 opens per answer (custom versus hosted). Opening patterns and search batching still differ, and category results are less similar. Use the scoped claim in [VALIDATION.md](VALIDATION.md); formal equivalence remains inconclusive. The experiment is ready to run as a controlled exploratory study.

## Get the inputs

Install and check the code:

```sh
python3 -m pip install -r requirements-validation.txt
python3 -m unittest discover -s tests -q
```

Download **commbank-handoff.zip** from the [handover release](https://github.com/heyinwong/harness-gpt-luna-web-serach/releases/tag/handover). Extract it and work inside `luna-harness/`; the ZIP includes code, the exact corpus and raw evidence. Cloning is optional for running this frozen version. If you already cloned the repository at the handover version, copy the extracted `results/` directory into its root. GitHub’s automatic “Source code” archives do not include these inputs.

`BUNDLE_MANIFEST.json` lists file hashes. The ZIP’s SHA-256 is `0bbf5a508ea223fde1532b6b2327459d56805b069dccf9f760e19876cc47bcff`. It contains no API key. References to a “private bundle” inside the unchanged archive predate the owner’s request to publish the release download.

If the release download is unavailable, build a new corpus:

```sh
python3 commbank_setup.py --cache results/commbank-cache --out-dir results/commbank-new
```

Building needs Node/npm and Chrome for selected dynamic pages, but spends no model-API credit. A fresh capture is a new corpus: rerun the comparison below. Do not inherit the old similarity result when corpus, model, retrieval, instructions or question mix changes. For an exact offline rebuild from a transferred raw cache, add `--offline` and use the cache path in the bundle.

## Repeat the comparison when inputs change

The frozen bundle already includes the completed comparison, so there is no need to buy the same check again merely to hand over. The following assumes the frozen inputs are at `results/commbank_final`. Change that path if you made a fresh build. Keep the key in an ignored `.env`; never paste it into chat.

```sh
python3 benchmark.py freeze --profile results/commbank_final/validation.json --corpus results/commbank_final/reference.json --out-dir results/my-comparison
python3 benchmark.py run --run-dir results/my-comparison --budget-usd 4 --allow-paid
python3 benchmark.py report --run-dir results/my-comparison
```

This compares 18 previously authored experiment questions, twice per mode: 72 answers. The dollar cap is a per-directory conservative request budget. Use only an owner-authorized budget. A failed or unfinished attempt stays in the evidence; do not delete or retry it silently. The report covers means, distributions, mentions, citations and reliability. The questions are a fixed convenience set, so population-wide claims remain limited.

## Run the award experiment

Use the same corpus version and retrieval configuration as the comparison:

```sh
python3 suite.py --corpus results/commbank_final/experiment.json --questions results/commbank_final/award_questions.json --arms baseline inline no_link link_vague link_descriptive current_footnote --repeats 2 --retrieval context --snippet-chars 6000 --page-chars 32000 --top-k 5 --max-rounds 8 --out-dir results/my-awards
```

The six-condition operational smoke test has completed and the scoring pipeline has been exercised. The full award study has not been run. This is plan-only: 216 custom answers. Add `--allow-paid`, an authorized `--budget-usd`, `--stop-after-estimated-usd` and `--max-runs` to execute. Start with a small operational batch. The same command resumes completed jobs; changing the configuration requires a new directory. Hosted web search cannot see the local treatments.

```sh
python3 award_report.py prepare --suite-dir results/my-awards --corpus results/commbank_final/experiment.json --out results/my-awards/scoring.json
```

Review each answer using the embedded rubric, fill the scores, then run:

```sh
python3 award_report.py analyze --suite-dir results/my-awards --scores results/my-awards/scoring.json --out results/my-awards/effects.json
```

A mention is not necessarily an endorsement or correct award use. Other awards remain in background pages. The separate award hub is an explicitly counterfactual local page. [COMMBANK_RUNBOOK.md](COMMBANK_RUNBOOK.md) documents the exact arms and contrasts if needed.

When scoring, check PDF-dependent claims against the cached original: one validation answer misread the GoalSaver withdrawal table. Do not treat hosted answers as factual ground truth either; source versions can disagree. Preserve these errors in the quality report.
