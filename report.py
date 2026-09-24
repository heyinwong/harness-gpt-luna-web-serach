#!/usr/bin/env python3
"""Render trace metrics and exact pre-open evidence. No model, no paid requests."""
import argparse
import json
from pathlib import Path


def text_blocks(event):
    output = event["output"]
    if event["tool"] == "search":
        return [r for search in output.get("searches", []) for r in search["results"]]
    if event["tool"] == "find":
        return output.get("matches", [])
    return [output] if "text" in output else []


def render(traces):
    lines = ["# Search harness report", "", "Counts are descriptive. No automatic claim of equivalence to Luna is made.",
             "Scripted demos are not agent runs. Local and hosted tool representations differ.", "",
             "| Trace | Mode | Status | Search actions | Queries | Open attempts/actions | Successful/completed opens | Unique local open URLs |",
             "|---|---|---|---:|---:|---:|---:|---:|"]
    for path, trace in traces:
        metrics = trace["metrics"]
        queries = metrics.get("search_queries", metrics.get("search_queries_reported", "?"))
        if metrics.get("search_actions_missing_query_list", 0):
            queries = f">= {queries} (incomplete)"
        lines.append(f"| {Path(path).name} | {trace['mode']} | {trace.get('status', 'scripted')} | {metrics.get('search_actions', 0)} | {queries} | {metrics.get('open_attempts', metrics.get('open_actions_reported', 0))} | {metrics.get('successful_opens', metrics.get('completed_open_actions', 0))} | {metrics.get('unique_open_urls', 'not measured')} |")
    lines += ["", "## Comparability", "", "Only compare completed runs on identical questions, model, reasoning settings and instructions. Keep repetitions and configurations separate. Budget-limited runs need separate reporting."]
    for path, trace in traces:
        lines += ["", f"### {Path(path).name}", "", f"Question: {trace.get('question', 'scripted demonstration')}",
                  f"\nModel: {trace.get('model', 'none')}; arm: {trace.get('arm')}; potentially budget limited: {trace.get('possibly_budget_limited', False)}."]
        if "error" in trace:
            lines += ["", f"Run error: {trace['error']}"]
        if trace.get("answer"):
            lines += ["", "Answer:", "", trace["answer"]]
        if trace.get("mode") == "live":
            lines += ["", "Hosted-search excerpts are unavailable. Consulted source URLs are not the raw ranked result list."]
        seen_opens = set()
        events = trace.get("tool_events", [])
        for index, event in enumerate(events):
            if event["tool"] not in ("open", "click"):
                continue
            output = event["output"]
            url = output.get("url", (event["arguments"] or {}).get("url", "unresolved"))
            # Results of sibling calls in the same model response were not yet observed.
            previous = [(e["index"], b) for e in events[:index]
                        if "requested_in_response" not in event or e.get("submitted_in_response", float("inf")) <= event["requested_in_response"]
                        for b in text_blocks(e) if b.get("url") == url]
            lines += ["", f"#### Event {event['index']}: {event['tool']} → {url}", "",
                      f"Repeated successful open: {url in seen_opens}. Exact destination previously returned: {bool(previous)}.",
                      f"\nSubmitted to a subsequent model request: {'submitted_in_response' in event}.",
                      "\nEarlier excerpts from this exact destination:", ""]
            if not previous:
                lines.append("None. Check earlier source-page link context in the JSON trace.")
            for prior, block in previous:
                lines += [f"Event {prior}:", "", "````text", block["text"], "````", ""]
            lines += ["", "Open result:", "", "````json", json.dumps(output, ensure_ascii=False, indent=2), "````",
                      "", "Reviewer classification: information gap / verification / navigation / repeated read / failure / uncertain.",
                      "\nNew useful evidence: [review manually; do not infer motive from tool counts]."]
            if "error" not in output:
                seen_opens.add(url)
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", nargs="+")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    output = Path(args.out)
    if output.exists():
        parser.error("Output exists; choose a new path")
    traces = [(p, json.loads(Path(p).read_text())) for p in args.traces]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(traces))
    print(output.resolve())


if __name__ == "__main__":
    main()
