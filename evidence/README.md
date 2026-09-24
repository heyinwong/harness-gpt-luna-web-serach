# Public measurements

Start with [VALIDATION.md](../VALIDATION.md) for the current result and [HANDOFF.md](../HANDOFF.md) for the one recommended configuration.

The [2026-09-24](2026-09-24/) directory preserves numeric summaries of all trials, including unsuccessful and incomplete ones. `commbank_corpus_final.json` records the current 69-document source manifest and hashes; `commbank_validation_v3.json` records the final locked comparison; `commbank_operational_smoke.json` records the six-condition execution check. Earlier documentation pilots and retrieval variants are historical evidence, not alternative recommended setups.

Exports contain metric rows, bounds, provenance hashes, completion counts and costs. They omit credentials, raw page text, full API responses, response IDs, encrypted reasoning and private filesystem paths. Current bank-study snapshots, manifests and traces are in the owner's private bundle; earlier documentation-domain raw runs remain on the original machine. Public exports cannot be used as resumable raw runs or independently prove API execution.

Do not pool reused hosted responses across calibration trials as independent observations. A new corpus or model needs a new comparison; convenience samples do not establish population-wide equivalence.
