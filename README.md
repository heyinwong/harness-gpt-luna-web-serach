# Luna search harness

A controlled search environment for **GPT-5.6 Luna**: search pages, read them, follow links and answer. Opus can operate the experiment; Luna remains the model making the search decisions.

The goal is to match observable behaviour—query counts, page opens, citations and mentions—on the same questions as hosted Luna web search. **The harness works, but the recorded tests have not established overall behavioural similarity. Page opening remains the main gap.** See [VALIDATION.md](VALIDATION.md) for results and the claim the evidence supports.

## Start here

1. Read [HANDOFF.md](HANDOFF.md) for the recommended setup and commands.
2. Use the frozen private corpus bundle, or build the supplied CommBank corpus recipe.
3. Run the comparison before interpreting the award experiment as evidence about hosted Luna.

The corpus recipe covers **69 documents** from CommBank, competing banks, Canstar, Finder and MoneySmart. It includes product pages, rates, conditions and PDFs. Real bank content and raw model traces stay in the private bundle; the public repository contains code, source manifests, question sets and numeric results. `sample_corpus.json` is only a fictional offline fixture.

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
