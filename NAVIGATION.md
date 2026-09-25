# Public navigation for the award experiment

Use `--navigation live` in `suite.py` or `search_lab.py`. Benchmark profiles set `runner.navigation` to `live`. Historical defaults remain `offline` so old commands cannot silently change behavior; current commands are in [HANDOFF.md](HANDOFF.md).

1. Search uses the frozen seed corpus (currently 69 documents) and returns passages and links.
2. Opening a seed page returns its captured text. Opening another public URL fetches it on demand, follows redirects and stores the raw response plus extracted text.
3. Before every fetch or cached response is returned, the harness checks for a controlled experiment page. That condition's local version wins. A deliberately absent award hub remains absent, including through a redirect.
4. All conditions in a suite share one append-only `web-cache/`. It stores untreated responses, never condition-modified text. Fetched pages can be opened and searched with `find`; they do not enter the search index.

No enumeration of model-guessed URLs is needed. Direct opens are allowed and labelled as previously returned pages, exposed links or unexposed URLs. `click` still requires a link ID actually exposed to the model. Nothing forces a target open count.

Controlled page matching covers declared URLs/aliases and their scheme, www, trailing-slash and query variants. Redirect targets are checked before fetching their bodies. Ordinary background URLs retain their query parameters. Undeclared mirrors that serve equivalent content under unrelated URLs remain background evidence; this does not claim to identify every possible copy of a page. Other existing award mentions also remain available, as prespecified.

## Preserve and replay

Archive the entire suite directory, including its manifest, traces and `web-cache/`. Each response has capture time, status, raw-body hash, parser hash and record hash. Traces include the records read; tool outputs also include redirect-hop hashes. Do not edit cached entries. Use a new directory to refresh sources or change parsing code. Errors are cached too, so one condition cannot silently retry until a better response appears.

`--navigation replay --web-cache PATH` uses captured responses only. A new URL becomes `cache_miss`, not HTTP 404. Replaying the same recorded tool sequence reproduces captured page content; a new stochastic model run may request different URLs. Replay disables background network fetching, **not model API charges**. A run with a different navigation mode needs a new output directory.

For a fresh experiment, start with one empty shared cache and the suite's randomized job order. Existing seed pages retain their original capture dates; background pages are captured on first demand. This mixes capture times and is not a snapshot of the entire web at one instant. Keep timestamps and cache contents with the findings.

## Check the right outcomes

Reports separate open attempts, successful page reads, unexposed URL attempts and errors (`http_error` with status, `network_error`, `extraction_error`, `fetch_rejected`, `cache_miss`, or intentional `not_available_in_condition`). A real 404 remains a failed read. A successfully extracted page is not a factual-accuracy certificate. Hosted tool completion does not expose enough HTTP detail to assume equivalent successful reads.

The fetcher handles public HTTP(S) HTML, PDF and plain text using the corpus extraction policy. It does not log in, run JavaScript, bypass access restrictions or silently substitute another page for an error. Review graphical PDF tables against the originals.

The tests exercise redirect handling, all six treatment overrides, absent hubs, cache isolation, unchanged search results, failures, replay and trace persistence. The real regression opens the six URLs that failed in the old offline comparison and verifies cached replay. The separate navigation pilot compares model behavior; neither test proves general equivalence to ChatGPT.
