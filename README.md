# Luna search harness

A controlled search environment for **GPT-5.6 Luna**: search pages, read them, follow links and answer. Opus can operate the experiment; Luna remains the model making the search decisions.

The goal is to match observable behaviour—query counts, page opens, citations and mentions—on the same questions as hosted Luna web search. **Ready for a controlled, exploratory award experiment. A 72-answer comparison found close average query/open counts, citations and mentions; opening patterns and search batching still differ. Overall equivalence remains inconclusive.** See [VALIDATION.md](VALIDATION.md) for results and the claim the evidence supports.

## Start here

1. Read [HANDOFF.md](HANDOFF.md) for the recommended setup and commands.
2. Download **commbank-handoff.zip** from the [handover release](https://github.com/heyinwong/harness-gpt-luna-web-serach/releases/tag/handover) and extract it. Work inside `luna-harness/`; this ZIP contains both code and frozen inputs. GitHub’s automatic “Source code” ZIP does not contain the corpus.
3. Use the recorded comparison’s scoped claim; rerun the comparison when inputs change.

The corpus recipe covers **69 documents** from CommBank, competing banks, Canstar, Finder and MoneySmart. It includes product pages, rates, conditions and PDFs. The owner-authorized release ZIP includes captured bank content and raw model traces. Git history contains code, source manifests, question sets and numeric results; credentials are excluded from both. `sample_corpus.json` is only a fictional offline fixture.

## Check the installation without API charges

```sh
python3 -m pip install -r requirements-validation.txt
python3 -m unittest discover -s tests -q
python3 search_lab.py demo --out results/demo.json
```

The demo checks tool wiring with scripted choices. It is not a model validation run.

## What is measured

- Individual search queries and search actions, counted separately.
- Opens per answer, the fraction of answers that open a page, and the open-count distribution.
- Citations, provider mentions, answer length, completion and failures.
- Search exposure, link following and award use as separate experiment outcomes.

Search returns source excerpts and links. `open`, `click` and `find` read the same frozen corpus. Opens are never forced or capped to imitate the reference. The hosted comparison uses the Responses API with web search; it cannot reveal every internal search result or establish identical ChatGPT orchestration.

The validator uses paired questions and repetitions, fixed tolerances and confidence intervals. It reports inconclusive results when evidence is insufficient; it does not invent an “XX% similar” score.

## Credentials and costs

Keep the API key in an ignored `.env` file, either as a raw key or `OPENAI_API_KEY=...`. Never put it in a prompt or commit it. Paid runs require `--allow-paid` and a dollar budget; planning and offline tests do not call the model API. Spending is recorded conservatively per run directory, not enforced on the account itself.

For the award placements and corpus details, see [COMMBANK_RUNBOOK.md](COMMBANK_RUNBOOK.md). [OPUS_RUNBOOK.md](OPUS_RUNBOOK.md) and [STATISTICS.md](STATISTICS.md) are optional technical references. Historical retrieval trials remain in [evidence/](evidence/README.md); they are not a menu of recommended configurations.
