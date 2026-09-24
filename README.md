# Luna search harness

A small, inspectable experiment for a model that searches a controlled corpus, reads pages, follows links and answers. Python 3.11+. The core runner uses the standard library; HTML snapshots and their tests also require Beautiful Soup (`pip install -r requirements-validation.txt`).

**Status:** the harness and reusable validator are implemented; 49 offline tests pass. The complete 48-run pilot did **not** establish Luna equivalence: on 11 fully comparable questions custom opens averaged 1.55 versus 0.23 hosted. Start with [HANDOFF.md](HANDOFF.md), [VALIDATION.md](VALIDATION.md), and the [public numeric evidence](evidence/README.md).

**The included corpus and questions are fictional fixtures.** They test the mechanics, not CBA facts or similarity to live Luna. The original 53-page corpus and 160 questions were not available; the project brief was supplied as eight photos. See [DESIGN.md](DESIGN.md) for experimental scope, assumptions and the validation plan.

## Reusable validation

Start with [OPUS_RUNBOOK.md](OPUS_RUNBOOK.md) for exact end-to-end commands, [STATISTICS.md](STATISTICS.md) for the confidence claim and its assumptions, and [VALIDATION.md](VALIDATION.md) for actual results. `benchmark.py` freezes a generic profile and corpus, runs paired hosted/custom trials with repetitions and persistent request reservations, and checks 12 scalar metrics plus four distributions overall and by category. Missing data and small pilots cannot certify equivalence. `reference` mode supports arbitrary corpora without award roles.

`award_report.py` prepares partially blinded manual scoring packets and reports paired award-placement contrasts. Mentions, reads, citations and correct award use remain separate outcomes.

## Start without an API key

```sh
python3 -m pip install -r requirements-validation.txt
python3 -m unittest discover -s tests -v
python3 search_lab.py demo --out results/demo.json
python3 report.py results/demo.json --out results/demo-report.md
python3 suite.py
```

The demo scripts search → open → click to check wiring. **Its choices are programmed, not chosen by a model.** `suite.py` only prints a plan unless given `--allow-paid`. Existing output files are not overwritten by the CLI.

## Tools

| Tool | Behaviour |
|---|---|
| `search(queries)` | Batch of 1–8 queries; BM25-ranked pages with query-relevant excerpts, URLs and links. Supports `site:domain/path` and whitespace-normalized required quoted phrases. |
| `open(url, offset)` | Read a local page window; captured URL fragments jump to their recorded anchor offset. Returns `next_offset` for long pages. An unknown URL returns `not_in_corpus`, never a hidden live fetch. |
| `click(page_url, link_id)` | Follow a link actually exposed in an earlier tool result. Tracks the source page explicitly. |
| `find(url, text)` | Return matching passages from a previously exposed page without counting another open. |

There is no fixed page-open cap. A configurable request-round limit prevents runaway runs and records incompletion. The hosted baseline has a separate built-in tool-call budget; those budgets are **not equivalent units**. Runs reaching either boundary need separate analysis.

## Corpus format

Copy `sample_corpus.json` and replace its fictional content with your saved pages:

- Each page has `url`, `title`, and Markdown `text`. Preserve links as `[anchor text](absolute-or-relative-url)` in their original context.
- Exactly one page has `role: "product"` and exactly one has `role: "hub"`.
- Put one `{{AWARD_BLOCK}}` marker at the intended treatment location in the product text.
- Set top-level `award_sentence` to the exact intervention text and `description` to your corpus provenance.
- Optional per-page metadata such as `retrieved_at`, `source_file`, `content_hash` and `fetch_status` can be retained in the corpus. Do not invent text for failed fetches; omit the unavailable page and record the coverage gap separately.
- Additional awards already present on product/competitor pages are **not automatically stripped**. Review treatment isolation yourself.
- Exactly the same arm-specific page content is used by the search index and open/find tools. The hub is searchable in the three hub-present arms, including `no_link`.

## API runs

Reads the key from `.env.local`, then `.env`, then the process environment's `OPENAI_API_KEY` (first available source wins). A local file may contain just the key or an `OPENAI_API_KEY=...` assignment. Files are parsed as text, never executed, and never rewritten. Local files override an old inherited environment key. Both env files are ignored by Git. Requests go only to `https://api.openai.com/v1/responses`; credentials are never printed. This does not use Portkey or silently substitute a different model.

The model is pinned to `gpt-5.6-luna`, matching the handover. Both paths use Responses, the same instruction text, reasoning setting and user question. Default hosted tool is `web_search_preview` to match that reference; `--web-tool web_search` is an explicit alternative configuration.

The following commands incur usage charges and should use **real corpus/questions** for a meaningful comparison:

```sh
python3 search_lab.py run --mode custom --arm baseline \
  --corpus my_corpus.json \
  --question 'What conditions apply to the CommBank savings account?' \
  --allow-paid --out results/custom-01.json

python3 search_lab.py run --mode live \
  --question 'What conditions apply to the CommBank savings account?' \
  --allow-paid --out results/live-01.json

python3 report.py results/custom-01.json results/live-01.json \
  --out results/comparison-01.md
```

For all five arms, first inspect the plan:

```sh
python3 suite.py --corpus my_corpus.json --questions my_questions.json \
  --include-live --repeats 2
```

Then add `--allow-paid` to execute. Default is at most five new runs, a persistent US$1 conservative reservation budget checked before each request, and an additional estimated US$1 stop checked between runs. The suite orders jobs with a reproducible shuffle, uses fresh agent state for each, resumes completed matching jobs and stops on failed/incomplete ones. Configuration/code/corpus hashes prevent accidentally reusing results from a different implementation. With an incomplete or failed trace, inspect it and choose a new output directory for an intentional retry; it never retries a potentially billed request silently.

Questions are a JSON array of `{ "id": "q01", "category": "product", "question": "..." }`. Keep a held-out subset for evaluation. The default synthetic corpus is rejected for a paired hosted-search suite.

## Traces and the open audit

Traces save API output items, usage, model-returned identifiers, configuration, instructions, full local tool results and link provenance. Reasoning output items are retained for API continuation; the harness does not claim to expose private reasoning. `submitted_in_response` distinguishes local results actually submitted on a subsequent request from results created at a round cutoff.

`report.py` shows:

- search actions versus individual queries;
- local open attempts, successes, unique URLs and failures;
- the exact earlier excerpts for each opened URL, alongside the open result;
- repeated opens and explicit link navigation;
- hosted consulted sources and missing query metadata without treating missing data as zero.

The report deliberately leaves the purpose and usefulness of each open for human review. Directly opening a hub URL after seeing a product page is not automatically classified as following its link. Search exposure, explicit opening and citation are different events.

## Costs and boundaries

Pricing checked 2026-09-24: GPT-5.6 Luna standard short-context input US$0.20/M, cached input US$0.02/M, output US$1.20/M; hosted reasoning web-search tools US$0.01 per billed call plus token usage. Cost output is an estimate based on returned usage and reported search actions, not an invoice; account-specific adjustments, cache writes and long-context surcharges are not modelled. Confirm actual usage in the API dashboard.

A US$5 initial balance is reasonable for small pilots, not a commitment that the entire experiment fits that amount. `--stop-after-estimated-usd` is checked **between complete runs** and can overshoot. `benchmark.py` and `suite.py` also reserve a conservative request cost before calling the API and retain uncertain charges; this is local budget protection under the registered pricing assumptions, not account-side enforcement. Budgets are per output directory, so previously spent study funds must be subtracted before creating another directory. Reaching a tool or token limit can change behaviour; retain and report those cases separately.

No API credit purchase, key creation, account-setting change or remote repository publication is performed by these scripts.

## Files

- `search_lab.py`: treatments, retrieval, tools, Responses loop and live baseline.
- `suite.py`: question/arm planning, shuffled execution and resumable traces.
- `report.py`: metric comparison and pre-open evidence audit.
- `sample_corpus.json`, `pilot_questions.json`: fictional fixtures.
- `tests/test_search_lab.py`: offline behavioural and orchestration checks.
- `benchmark.py`, `validation/`, `benchmarks/`: generic frozen fidelity studies, confidence bounds, metrics and budget reservations.
- `award_report.py`: human scoring packets and paired treatment contrasts.
- `calibrate.py`: exploratory one-factor excerpt ablations using an existing pilot reference; no certification.
- `OPUS_RUNBOOK.md`, `STATISTICS.md`: reproducible operator instructions and statistical assumptions.
- `DESIGN.md`: experiment and validation design.
- `VALIDATION.md`: verified checks, smoke-run results and remaining limitations.

Official references: [function calling](https://developers.openai.com/api/docs/guides/function-calling), [web search and sources](https://developers.openai.com/api/docs/guides/tools-web-search#sources), [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna), [pricing](https://developers.openai.com/api/docs/pricing), [spend limits](https://developers.openai.com/api/docs/guides/spend-limits).
