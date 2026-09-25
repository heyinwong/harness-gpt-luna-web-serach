#!/usr/bin/env python3
"""Plan or run a reproducible set of questions/arms. Planning is the default."""
import argparse
import hashlib
import json
from pathlib import Path
import random
from types import SimpleNamespace

import search_lab as lab
from validation.budget import BudgetedTransport


def plan(questions, arms, repeats, live, seed):
    ids = [q["id"] for q in questions]
    if len(set(ids)) != len(ids) or not questions:
        raise ValueError("Question IDs must be unique and the question set nonempty")
    jobs = []
    for question in questions:
        if not isinstance(question["question"], str) or not question["question"].strip():
            raise ValueError("Each question must contain nonempty text")
        for repeat in range(repeats):
            for arm in arms:
                jobs.append({"id": question["id"], "category": question.get("category", "unspecified"),
                             "question": question["question"], "repeat": repeat, "mode": "custom", "arm": arm})
            if live:
                jobs.append({"id": question["id"], "category": question.get("category", "unspecified"),
                             "question": question["question"], "repeat": repeat, "mode": "live", "arm": "baseline"})
    random.Random(seed).shuffle(jobs)
    return jobs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", default=str(lab.ROOT / "pilot_questions.json"))
    parser.add_argument("--corpus", default=str(lab.ROOT / "sample_corpus.json"))
    parser.add_argument("--arms", nargs="+", choices=lab.EXPERIMENT_ARMS, default=list(lab.ARMS))
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--include-live", action="store_true")
    parser.add_argument("--seed", type=int, default=20260924)
    parser.add_argument("--reasoning", choices=("none", "low", "medium", "high", "xhigh", "max"), default="medium")
    parser.add_argument("--web-tool", choices=("web_search", "web_search_preview"), default="web_search_preview")
    parser.add_argument("--retrieval", choices=("context", "window"), default="context")
    parser.add_argument("--navigation", choices=("offline", "live", "replay"), default="offline")
    parser.add_argument("--web-cache", help="Shared cache for all conditions; defaults to out-dir/web-cache")
    parser.add_argument("--snippet-chars", type=int, default=6000)
    parser.add_argument("--page-chars", type=int, default=32000)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--max-rounds", type=int, default=8)
    parser.add_argument("--max-output-tokens", type=int, default=4096)
    parser.add_argument("--max-runs", type=int, default=5)
    parser.add_argument("--stop-after-estimated-usd", type=float, default=1.0)
    parser.add_argument("--budget-usd", type=float, default=1.0,
                        help="Persistent conservative request-reservation budget for this directory")
    parser.add_argument("--allow-paid", action="store_true")
    parser.add_argument("--out-dir", default=str(lab.ROOT / "results" / "suite"))
    args = parser.parse_args()
    if not (1 <= args.repeats <= 20 and 1 <= args.max_runs <= 1000 and args.stop_after_estimated_usd > 0 and 0 < args.budget_usd <= 100):
        parser.error("Use 1–20 repetitions, 1–1000 max runs and a positive estimated-spend stop")
    if not 1 <= args.max_rounds <= 30 or not 256 <= args.max_output_tokens <= 16000:
        parser.error("Use 1–30 rounds and 256–16000 output tokens")
    corpus = json.loads(Path(args.corpus).read_text())
    # Validate before any paid request, including when the first job happens to be live.
    lab.browser_class(args.retrieval)(corpus, args.arms[0], args.snippet_chars, args.top_k, args.page_chars)
    if args.include_live and "SYNTHETIC" in corpus.get("description", "").upper():
        parser.error("Use a real corpus/question set for a paired live suite; the default fixture is synthetic")
    jobs = plan(json.loads(Path(args.questions).read_text()), list(dict.fromkeys(args.arms)), args.repeats, args.include_live, args.seed)
    config = {k: getattr(args, k) for k in ("navigation", "retrieval", "reasoning", "web_tool", "snippet_chars", "page_chars", "top_k", "max_rounds", "max_output_tokens")}
    config.update(model="gpt-5.6-luna", corpus_sha256=hashlib.sha256(Path(args.corpus).read_bytes()).hexdigest(),
                  instructions=lab.INSTRUCTIONS, runner_sha256=hashlib.sha256(Path(lab.__file__).read_bytes()).hexdigest(),
                  suite_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    if args.web_cache:
        config["web_cache"] = str(Path(args.web_cache).resolve())
    config['retrieval_code_hashes'] = {name: hashlib.sha256((lab.ROOT/name).read_bytes()).hexdigest()
                                       for name in ('context_passages.py', 'passage_retrieval.py', 'navigation.py', 'corpus_builder.py', 'validation/snapshot.py')}
    print(json.dumps({"paid_enabled": args.allow_paid, "planned_runs": len(jobs), "maximum_new_runs_this_invocation": args.max_runs,
                      "estimated_spend_stop_usd": args.stop_after_estimated_usd,
                      "reservation_budget_usd": args.budget_usd,
                      "notice": "Persistent conservative reservations precede each request; estimated-spend stop is additionally checked between runs. Neither is a provider invoice.",
                      "config": config, "jobs": jobs}, indent=2))
    if not args.allow_paid:
        return
    output = Path(args.out_dir)
    budget = BudgetedTransport(output / "budget.json", args.budget_usd)
    manifest = {"jobs": jobs, "config": config}
    manifest_path = output / "manifest.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest:
        parser.error("Suite configuration changed; use a new directory")
    lab.save(manifest_path, manifest)
    spent = 0.0
    new_runs = 0
    for job in jobs:
        digest = hashlib.sha256(json.dumps({"job": job, "config": config}, sort_keys=True).encode()).hexdigest()[:20]
        path = output / f"{digest}.json"
        if path.exists():
            previous = json.loads(path.read_text())
            spent += previous.get("usage", {}).get("estimated_usd", 0)
            if previous.get("status") != "completed":
                print(f"Stopped at existing incomplete/failed trace {path}; inspect before retrying.")
                return
            continue
        if new_runs >= args.max_runs or spent >= args.stop_after_estimated_usd:
            print("Stopped before the next run at the configured run-count or estimated-spend boundary.")
            return
        values = config | {"allow_paid": True, "mode": job["mode"], "arm": job["arm"],
                           "question": job["question"], "corpus": args.corpus, "out": str(path),
                           "web_cache": args.web_cache or str(output / "web-cache")}
        trace = lab.run(SimpleNamespace(**values), transport=budget)
        trace["suite_job"] = job
        trace["suite_config"] = config
        lab.save(path, trace)
        spent += trace["usage"]["estimated_usd"]
        new_runs += 1
        print(json.dumps({"trace": str(path), "status": trace["status"], "estimated_spend_usd": spent}))
        if trace["status"] != "completed":
            print("Stopped after a failed or incomplete run; no automatic retries.")
            return


if __name__ == "__main__":
    main()
