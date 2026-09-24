# CommBank corpus and award experiment

For the short, current workflow, use [HANDOFF.md](HANDOFF.md). This document records corpus and treatment details.

## What this package establishes

The corpus is built and the experiment is executable. **This is not yet a validated replica of hosted Luna or the ChatGPT product.** Read the current bank calibration evidence before interpreting treatment effects outside this harness. Opus is the operator; `gpt-5.6-luna` is the decision model.

Eight hosted Luna discovery questions informed source selection. Those questions are for discovery only, not a confirmatory holdout. The current capture contains **69 documents**, including **9 PDFs comprising 392 PDF pages**, across CommBank, ANZ, NAB, Westpac, ING, ubank, Macquarie, AMP, P&N Bank, Canstar, Finder and ASIC MoneySmart. The seven core banks each have product and conditions/rate information; coverage is deliberately unequal where the target and observed questions need more detail. This is neither a complete market census nor the full web.

The discovery audit matches **30/37 answer-cited URLs** and **6/7 explicitly opened URLs** by hostname/path. It matches 70/324 reported source URLs by that looser rule; exact/declared-alias matches are lower. These denominators are separate. Search source metadata does not reveal every candidate or prove every page was read. Two Rabobank pages returned HTTP 403 through both ordinary HTTP and browser access; those exclusions are recorded. Never call corpus size or discovery overlap a fidelity pass.

## Build without API charges

Requires Python 3.11+, Node/npm and Chrome for the small subset of pages needing browser rendering. Install the Python dependencies, then run from the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-validation.txt
python -m unittest discover -s tests -v
python commbank_setup.py --cache results/commbank-cache --out-dir results/commbank-v1
```

This command uses ordinary public-web requests and Playwright CLI; it does **not** load a key or call a model. It produces `reference.json`, `experiment.json`, `audit.json`, `calibration.json`, `validation.json` and the question files. Output directories are immutable. Browser captures and original HTTP responses remain in the private cache. Rerunning against an existing cache reuses it; choose a new cache directory to refresh sources.

For the original machine, the existing cache is `results/commbank_build/cache`, the current reviewed corpus is `results/commbank_final` (identical reference/experiment content to `results/commbank_corpus_v6`), discovery is `results/commbank_discovery_v1`, and the first bank calibration is `results/commbank_calibration_v1`. These paths are **not in a public clone**. The private `commbank-handoff.zip` preserves them, along with current validation and operational evidence, without publishing bank-page copies or model traces.

To rebuild entirely from a transferred cache:

```sh
python commbank_setup.py --offline --cache results/commbank_build/cache --out-dir results/commbank-rebuilt
```

Capture time, response URL and content hashes are retained. HTML extraction preserves headings, table rows, links, fragments and legal footnotes. Browser rendering is explicitly declared per source. PDF spreads are split only for reviewed layouts; extracted tables label uncertain blank/graphical cells. PDF text remains an approximation: consult the original PDF when scoring an answer that depends on a table. A successful extraction gate is not a complete semantic audit. Sparse cover/divider-page reviews are tied to exact content hashes, so a changed PDF requires review again.

## The award and six conditions

The target is the existing phrase **“Canstar 2024 Digital Banking Bank of the Year.”** on [CommBank's savings landing page](https://www.commbank.com.au/savings-accounts.html). It appears in “Things you should know,” near the bottom, approximately 86% through the captured text. A browser check at 1280×720 confirmed it is visible after scrolling, initially about 5,485 pixels below the viewport top; it is not hidden behind a required click. It is a bank-level digital-banking award, not proof of a superior savings rate or a savings-product award. Do not silently replace 2024 with another year.

The reference corpus preserves the page unchanged. The experimental derivative removes only its isolated award footnote and inserts a controlled location immediately after the source H1. The original text and anchors are stored for restoration. The conditions are:

| Arm | Target landing-page claim | Separate local award hub |
|---|---|---|
| `current_footnote` | Original source text and bottom footnote, exactly restored | Absent |
| `baseline` | Removed from the manipulated location | Absent |
| `inline` | Award sentence immediately after H1 | Absent |
| `no_link` | No claim or link in the manipulated location | Searchable |
| `link_vague` | “See our awards” link after H1 | Searchable |
| `link_descriptive` | Same award sentence plus “Award details” link after H1 | Searchable |

The hub URL is a **counterfactual local document** under the CommBank domain, not a claim that such a public page exists. The URL, hub wording and text position are frozen in the corpus. The descriptive arm includes the claim inline, so it tests claim-plus-link, not anchor wording alone. Baseline/inline versus hub arms also change page availability. For a pure link-label study, create a new prespecified design holding claim, hub availability and search index constant; do not reinterpret these contrasts afterward.

Other CommBank and competitor award evidence remains unchanged in the background. Therefore `baseline` means no award at the manipulated locations, **not** no award anywhere and not no model prior knowledge. This estimates the incremental effect of those placements in a richer environment. A globally award-scrubbed study would be a different experiment and less naturalistic.

This is a **text retrieval experiment**, not a visual-attention study. Collapsed/low-page content may still be accessible to search. BM25 can surface a footnote directly; being low on a human viewport does not imply the model missed it. Measure observed exposure, navigation and answer use separately.

## Historical calibration

The first bank calibration used the **initial 67-document corpus**, before the ANZ dynamic-rate repair. Of 48 planned runs, hosted completed 24/24 and custom 23/24; one ANZ case exhausted its eight rounds. On 11 fully comparable questions, query counts averaged 3.00 custom versus 2.73 hosted, while opens averaged 2.77 versus 0.41. The verdict is **inconclusive**, with a substantial observed opening gap. See `evidence/2026-09-24/commbank_calibration_v1.json`.

The missing ANZ rate figures and a missing Macquarie eligibility link led to the current 69-document version. `sources_v1.json` and `calibration_v1.json` preserve the original manifests. The repaired corpus gets a targeted diagnostic, not an inherited fidelity pass. The separate 6,000-character excerpt trial retains the original corpus to isolate excerpt length. Neither experiment is a confirmatory holdout.

## Calibrate the unchanged reference first

The 12 authored calibration cases cover lookup, conditions and comparisons, with two repetitions. They are convenience cases, not representative independent holdout observations. `target_mention` consistently refers to CommBank, even in competitor-only questions. Entity and citation distributions use the registered provider groups; OTHER/NONE remain explicit. All existing completion, budget, scalar and distribution gates remain in force.

```sh
python benchmark.py freeze --profile results/commbank-v1/calibration.json --corpus results/commbank-v1/reference.json --out-dir results/commbank-check-v1
python benchmark.py run --run-dir results/commbank-check-v1 --budget-usd 3
```

The last command is plan-only. After the owner authorizes that run's budget, add `--allow-paid`. Preserve all failures and cutoffs. Generate the report without further API charges:

```sh
python benchmark.py report --run-dir results/commbank-check-v1
```

The current configuration uses context-preserving source passages, 6,000-character search excerpts and 32,000-character open windows; it does not impose an open quota. The initial bank pilot used 1,200-character windows. Historical retrieval trials are retained in evidence, but the operator should use the single configuration in HANDOFF.md. Freeze a new directory whenever code or corpus changes.

Before generalizing to actual ChatGPT, obtain fresh representative questions from the intended use distribution, separate them by intent from discovery/tuning examples, preregister margins and sampling, then freeze a genuine holdout. Do not change `sampling` to claim representativeness for these authored examples. There is no defensible single “XX% similar” score here: report simultaneous confidence intervals against practical equivalence margins, missingness, quality and the scope actually tested. Hosted API search is itself a proxy for the ChatGPT product's hidden orchestration.

## Plan and run the controlled award study

Eighteen authored prompts cover unbranded discovery, branded consideration and provider comparisons, six each. They do not explicitly ask for awards. They are a reproducible exploratory question set; they are not the owner's original 160 questions and not a population sample. In the unbranded cases, missing market options are a known limitation. Prespecify the primary mix and distinguish award mention from endorsement, accurate relevance and unsupported product claims.

```sh
python suite.py --corpus results/commbank-v1/experiment.json --questions results/commbank-v1/award_questions.json --arms baseline inline no_link link_vague link_descriptive current_footnote --repeats 2 --retrieval context --snippet-chars 6000 --page-chars 32000 --top-k 5 --max-rounds 8 --out-dir results/commbank-awards-v1
```

This plans **216 custom runs** and spends nothing. Keep this exact configuration for execution; add an explicitly authorized `--budget-usd`, `--stop-after-estimated-usd`, `--max-runs` and `--allow-paid`. Run a small operational pilot first. Never use hosted search to test the local treatments: it cannot see the altered pages. The suite default remains the original five arms, so explicitly pass all six as shown.

```sh
python award_report.py prepare --suite-dir results/commbank-awards-v1 --corpus results/commbank-v1/experiment.json --out results/commbank-awards-v1/scoring.json
```

Complete the blinded scores using the rubric, the actual answer and its supporting sources, then:

```sh
python award_report.py analyze --suite-dir results/commbank-awards-v1 --scores results/commbank-awards-v1/scoring.json --out results/commbank-awards-v1/effects.json
```

The six-arm report adds current-footnote versus baseline and inline versus current-footnote contrasts. Question repetitions remain clustered. Do not treat 216 runs as 216 independent questions. Until the applicable fidelity study passes, all effects are **effects within this harness**.

## When Opus changes the corpus

Freeze a new corpus, profile and run directory if any page, rate, extraction rule, source selection, URL alias, treatment, model or tool setting changes. Preserve the previous version. Recheck source coverage, provider balance, missing links, award evidence elsewhere and known-answer passages; rerun matched calibration and any affected validation. Never carry a fidelity verdict or confidence interval across corpus versions. For pure transfer testing, retain the original question distribution and margins; report new-domain results separately.

Keep `.env`, page captures, full model responses, screenshots and private archives out of Git. Publish the recipe, source manifest, code and numeric audit results. Future recrawls will not reproduce the exact 2026-09-24 bank content; use the private frozen bundle for that purpose.
