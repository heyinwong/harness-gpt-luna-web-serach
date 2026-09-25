# Start here, Opus

Operate this repository; keep **GPT-5.6 Luna** as the experimental model. The owner wants one usable search harness with measured similarity, not a reconstruction of ChatGPT internals.

**Use the navigation-v2 release below.** The old offline harness treated URLs outside its corpus as failures, even when the pages existed. Public navigation now fetches those URLs on demand, follows redirects and caches the untreated responses. All six previously failing URLs pass a real-fetch/cache-replay regression. See [NAVIGATION.md](NAVIGATION.md) for the short contract and [VALIDATION.md](VALIDATION.md) for the new diagnostic pilot. The new 24-answer pilot had 28/28 successful custom opens but 2.33 versus 0.00 opens per answer (custom versus hosted). Overall Luna equivalence remains unestablished.

## One setup

Use `--navigation live` with `context` retrieval, 6,000-character search excerpts, five results per query, 32,000-character open windows, eight model rounds and medium reasoning. Search selects source passages with their adjacent question/heading and qualifying bullets. Page ranking uses readable link labels rather than URL tracking text. `open`, `click` and `find` remain available whenever Luna needs them. Never force an open count.

The current corpus has **69 documents**, including CommBank and competitors. `reference.json` preserves the captured pages. `experiment.json` supplies the six award-placement conditions. The target is the existing **Canstar 2024 Digital Banking Bank of the Year** footnote, a bank-level award. It is visible after scrolling; this is a text-retrieval experiment, not a visual-attention experiment.

The older **offline** 72-answer comparison found 6.47 versus 7.06 queries and 0.50 versus 0.33 opens per answer (custom versus hosted). Opening patterns and search batching still differ, and category results are less similar. Use the scoped claim in [VALIDATION.md](VALIDATION.md); formal equivalence remains inconclusive. Its numerical result does not validate the changed navigation. Interpret award effects within this exploratory harness.

## Get the inputs

Install and check the code:

```sh
python3 -m pip install -r requirements-validation.txt
python3 -m unittest discover -s tests -q
```

Download **commbank-handoff-navigation-v2.zip** from the [navigation-v2 release](https://github.com/heyinwong/harness-gpt-luna-web-serach/releases/tag/navigation-v2). Extract it and work inside `luna-harness/`; it includes current code, the exact corpus, raw evidence and navigation caches. GitHub's automatic “Source code” archives do not include these inputs. Avoid mixing this code with the older handover ZIP's code.

`BUNDLE_MANIFEST.json` lists every packaged file hash. The release includes a SHA-256 checksum file. No API key is included. Old runs retain their original code and manifests; do not resume them with the new implementation.

If the release download is unavailable, build a new corpus:

```sh
python3 commbank_setup.py --cache results/commbank-cache --out-dir results/commbank-new
```

Building needs Node/npm and Chrome for selected dynamic pages, but spends no model-API credit. A fresh capture is a new corpus: rerun the comparison below. Do not inherit the old similarity result when corpus, model, retrieval, instructions or question mix changes. For an exact offline rebuild from a transferred raw cache, add `--offline` and use the cache path in the bundle.

## Repeat the comparison when inputs change

The bundle includes the older comparison and a new navigation-focused diagnostic. A full repeat comparison is available below; it is not already completed for the changed navigation. The following assumes the frozen inputs are at `results/commbank_final`. Change that path if you made a fresh build. Keep the key in an ignored `.env`; never paste it into chat.

```sh
python3 benchmark.py freeze --profile corpora/commbank/navigation_validation.json --corpus results/commbank_final/reference.json --out-dir results/my-comparison
python3 benchmark.py run --run-dir results/my-comparison --budget-usd 4 --allow-paid
python3 benchmark.py report --run-dir results/my-comparison
```

This repeats 18 previously inspected questions, twice per mode: 72 answers. It is a descriptive regression check, not a fresh holdout. The profile explicitly enables live cached navigation. The dollar cap is a per-directory conservative request budget. Use only an owner-authorized budget. A failed or unfinished attempt stays in the evidence; do not delete or retry it silently. The report covers means, distributions, mentions, citations and reliability. The questions are a fixed convenience set, so population-wide claims remain limited.

## Run the award experiment

Use the same corpus version and retrieval configuration as the comparison:

```sh
python3 suite.py --corpus results/commbank_final/experiment.json --questions results/commbank_final/award_questions.json --arms baseline inline no_link link_vague link_descriptive current_footnote --repeats 2 --navigation live --retrieval context --snippet-chars 6000 --page-chars 32000 --top-k 5 --max-rounds 8 --out-dir results/my-awards
```

The six-condition operational smoke test and scoring check used the older offline runner. The new navigation has automated treatment-isolation checks across all six conditions; start with a small paid operational batch on your machine. The full award study has not been run. This is plan-only: 216 custom answers. Add `--allow-paid`, an authorized `--budget-usd`, `--stop-after-estimated-usd` and `--max-runs` to execute. All conditions share `results/my-awards/web-cache`; archive that directory with the results. Background fetches do not enter the search index. The same command resumes completed jobs; changing the configuration requires a new directory. Hosted web search cannot see the local treatments.

```sh
python3 award_report.py prepare --suite-dir results/my-awards --corpus results/commbank_final/experiment.json --out results/my-awards/scoring.json
```

Review each answer using the embedded rubric, fill the scores, then run:

```sh
python3 award_report.py analyze --suite-dir results/my-awards --scores results/my-awards/scoring.json --out results/my-awards/effects.json
```

A mention is not necessarily an endorsement or correct award use. Other awards remain in background pages. The separate award hub is an explicitly counterfactual local page. [COMMBANK_RUNBOOK.md](COMMBANK_RUNBOOK.md) documents the exact arms and contrasts if needed.

When scoring, check PDF-dependent claims against the cached original: one validation answer misread the GoalSaver withdrawal table. Do not treat hosted answers as factual ground truth either; source versions can disagree. Preserve these errors in the quality report.
