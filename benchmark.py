#!/usr/bin/env python3
"""Snapshot, freeze, run, and analyze a reusable paired search benchmark."""
import argparse
import json
from pathlib import Path
import random
from types import SimpleNamespace

import search_lab as lab
from validation.budget import BudgetedTransport
from validation.protocol import analyze, fingerprint, markdown, validate_profile
from validation.planning import precision_plan


def code_hashes():
    paths = [lab.ROOT / name for name in ("search_lab.py", "benchmark.py")] + sorted((lab.ROOT / "validation").glob("*.py"))
    import hashlib
    return {str(p.relative_to(lab.ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    snap = sub.add_parser("snapshot")
    snap.add_argument("--profile", required=True)
    snap.add_argument("--out", required=True)
    freeze = sub.add_parser("freeze")
    freeze.add_argument("--profile", required=True)
    freeze.add_argument("--corpus", required=True)
    freeze.add_argument("--out-dir", required=True)
    run = sub.add_parser("run")
    run.add_argument("--run-dir", required=True)
    run.add_argument("--budget-usd", type=float, default=2)
    run.add_argument("--allow-paid", action="store_true")
    report = sub.add_parser("report")
    report.add_argument("--run-dir", required=True)
    args = parser.parse_args()
    if args.command == "snapshot":
        from validation.snapshot import snapshot
        if Path(args.out).exists():
            parser.error("Snapshot exists; choose a new path to preserve provenance")
        profile = json.loads(Path(args.profile).read_text())
        validate_profile(profile)
        corpus = snapshot(profile["snapshot_urls"])
        lab.save(args.out, corpus)
        print(json.dumps({"pages": len(corpus["pages"]), "failures": corpus["failures"], "output": args.out}))
        if corpus["failures"]:
            raise SystemExit(1)
    elif args.command == "freeze":
        directory = Path(args.out_dir)
        if directory.exists():
            parser.error("Run directory exists; freeze into a new directory")
        profile = json.loads(Path(args.profile).read_text())
        validate_profile(profile)
        corpus = json.loads(Path(args.corpus).read_text())
        if corpus.get("failures"):
            parser.error("Fix or explicitly redesign snapshot coverage before freezing; unresolved fetch failures")
        lab.Browser(corpus, "reference")
        corpus_text = Path(args.corpus).read_bytes()
        import hashlib
        manifest = {"profile": profile, "corpus_sha256": hashlib.sha256(corpus_text).hexdigest(), "code_hashes": code_hashes()}
        directory.mkdir(parents=True)
        (directory / "corpus.json").write_bytes(corpus_text)
        lab.save(directory / "manifest.json", manifest)
        print(json.dumps({"manifest_sha256": fingerprint(manifest), "planned_runs": len(profile["cases"]) * profile["repeats"] * 2, "directory": str(directory)}))
    else:
        directory = Path(args.run_dir)
        manifest = json.loads((directory / "manifest.json").read_text())
        profile = manifest["profile"]
        if args.command == "run":
            if code_hashes() != manifest["code_hashes"]:
                parser.error("Code changed after freeze; create a new frozen run directory")
            import hashlib
            if hashlib.sha256((directory / "corpus.json").read_bytes()).hexdigest() != manifest["corpus_sha256"]:
                parser.error("Frozen corpus changed")
            jobs = [{"case_id": c["id"], "repeat": r, "mode": mode}
                    for c in profile["cases"] for r in range(profile["repeats"]) for mode in ("custom", "live")]
            random.Random(profile["seed"]).shuffle(jobs)
            print(json.dumps({"planned_runs": len(jobs), "budget_usd": args.budget_usd, "paid_enabled": args.allow_paid}), flush=True)
            if not args.allow_paid:
                return
            if not 0 < args.budget_usd <= 100:
                parser.error("Use a positive explicit budget, at most US$100 per pilot directory")
            budget = BudgetedTransport(directory / "budget.json", args.budget_usd)
            cases = {c["id"]: c for c in profile["cases"]}
            for job in jobs:
                path = directory / "traces" / (fingerprint(job)[:20] + ".json")
                if path.exists():
                    if json.loads(path.read_text()).get("status") in ("failed", "running"):
                        print("Stopped: previous failed/pending request exists. Inspect before starting a new pilot.")
                        break
                    # A completed billed attempt with a model budget cutoff remains
                    # a censored observation; never retry or silently drop it.
                    continue
                case = cases[job["case_id"]]
                values = profile["runner"] | {"model": profile["model"], "instructions": profile["instructions"],
                         "allow_paid": True, "mode": job["mode"], "arm": "reference", "question": case["question"],
                         "corpus": str(directory / "corpus.json"), "out": str(path)}
                trace = lab.run(SimpleNamespace(**values), transport=budget)
                trace["benchmark_job"] = job
                trace["benchmark_manifest_sha256"] = fingerprint(manifest)
                lab.save(path, trace)
                print(json.dumps({"case": job["case_id"], "repeat": job["repeat"], "mode": job["mode"],
                                  "status": trace["status"], "conservative_spend_usd": round(budget.ledger["reserved_or_charged_usd"], 4)}), flush=True)
                if trace["status"] == "failed":
                    print("Stopped after request failure; no automatic retries.", flush=True)
                    break
        traces = [json.loads(p.read_text()) for p in sorted((directory / "traces").glob("*.json"))]
        result = analyze(manifest, traces)
        result["precision_plan"] = precision_plan(result)
        corpus = json.loads((directory / "corpus.json").read_text())
        from urllib.parse import urlsplit
        def page_key(url):
            parts = urlsplit(url)
            return (parts.hostname or "").removeprefix("www."), parts.path.rstrip("/")
        corpus_urls = {page_key(p["url"]) for p in corpus["pages"]}
        sources = {url for t in traces if t.get("mode") == "live"
                   for url in lab.hosted_metrics(t.get("responses", []))["consulted_sources"]}
        result["coverage"] = {"reported_hosted_source_urls": len(sources),
                              "source_urls_in_snapshot": sum(page_key(u) in corpus_urls for u in sources),
                              "outside_snapshot": sorted(u for u in sources if page_key(u) not in corpus_urls),
                              "notice": "URL overlap ignores query, scheme and fragment. It does not establish identical content, complete candidate coverage or actual reading."}
        lab.save(directory / "report.json", result)
        (directory / "report.md").write_text(markdown(result))
        print(json.dumps({"verdict": result["verdict"], "observed_runs": result["observed_runs"], "report": str(directory / "report.md")}), flush=True)


if __name__ == "__main__":
    main()
