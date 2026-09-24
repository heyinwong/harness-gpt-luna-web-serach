# Public numeric evidence

The [2026-09-24](2026-09-24/) directory contains all five trial summaries, including unsuccessful attempts. Start with [the complete paired pilot](2026-09-24/public_web_pilot_v3.md) and [the excerpt-length diagnostic](2026-09-24/excerpt_calibration_v5.md).

JSON files contain registered metric rows, bounds, flags, numeric per-run observations where available, and conservative experiment costs. They intentionally omit raw API responses, response identifiers, encrypted reasoning, page contents, full source/query lists, credentials and local paths. Public question profiles are in `benchmarks/`.

These are exported measurements, not fabricated replacement traces. They permit arithmetic inspection but cannot independently prove that an API request occurred or reproduce page-exposure audits. Full snapshots/manifests/traces remain in the original machine's ignored `results/` directory. New runs require fresh snapshots and a separately authorized API budget. The reports cannot be passed to `benchmark.py run` as resumable run directories.

The main verdict is **inconclusive**, with a substantial observed opening gap. The excerpt trial is explicitly exploratory, reuses the recorded hosted baseline, and stopped at its request-reservation boundary. Do not pool the trials into one independent validation sample or relabel them as a holdout.
