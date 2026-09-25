"""Observable metrics only. Citations are not reads; mentions are not endorsements."""
import re
from urllib.parse import urlsplit, urlunsplit

from search_lab import LINK, canonical, tokens


def citation_urls(trace):
    urls = {m.group(2) for m in LINK.finditer(trace.get("answer", ""))}
    for response in trace.get("responses", []):
        for item in response.get("output", []):
            for content in item.get("content", []):
                for annotation in content.get("annotations", []):
                    if annotation.get("type") == "url_citation" and annotation.get("url"):
                        urls.add(annotation["url"])
    result = set()
    for url in urls:
        try:
            result.add(canonical(url))
        except ValueError:
            continue
    return sorted(result)


def answer_prose(answer):
    text = LINK.sub(lambda m: m.group(1), answer)
    return re.sub(r"https?://\S+", "", text)


def contains_alias(text, aliases):
    return any(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", text, re.I) for alias in aliases)


def bin_vector(value, edges):
    # Edges are inclusive upper bounds; final bin is overflow.
    index = next((i for i, edge in enumerate(edges) if value <= edge), len(edges))
    return [float(i == index) for i in range(len(edges) + 1)]


def domain_group(host, domains):
    host = host.lower().removeprefix("www.")
    return next((d for d in domains if host == d or host.endswith("." + d)), "OTHER")


def extract(trace, case, profile):
    completed = trace.get("status") == "completed"
    limited = bool(trace.get("possibly_budget_limited"))
    base = {"completed": float(completed), "budget_limited": float(limited)}
    details = {"status": trace.get("status"), "citation_urls": citation_urls(trace), "missing": []}
    if not completed or limited:
        return {"scalar": base, "vectors": {}, "details": details}
    metrics = trace.get("metrics", {})
    queries = []
    actions = []
    open_count = 0
    known = True
    if trace["mode"] == "custom":
        for event in trace.get("tool_events", []):
            # A search/open request is counted even if the tool subsequently fails.
            name = event["tool"]
            if name == "search":
                arguments = event.get("arguments") or {}
                q = arguments.get("queries")
                if not isinstance(q, list) or any(not isinstance(x, str) for x in q):
                    known = False
                else:
                    queries.extend(q)
                actions.append("S")
            elif name in ("open", "click"):
                open_count += 1
                actions.append("O")
            elif name == "find":
                actions.append("F")
    else:
        for response in trace.get("responses", []):
            for item in response.get("output", []):
                if item.get("type") != "web_search_call":
                    continue
                action = item.get("action") or {}
                if action.get("type") == "search":
                    q = action.get("queries")
                    if not isinstance(q, list) or any(not isinstance(x, str) for x in q):
                        known = False
                    else:
                        queries.extend(q)
                    actions.append("S")
                elif action.get("type") == "open_page":
                    open_count += 1
                    actions.append("O")
                elif action.get("type") == "find_in_page":
                    actions.append("F")
    domains = sorted({urlsplit(url).hostname.lower().removeprefix("www.") for url in details["citation_urls"]})
    prose = answer_prose(trace.get("answer", ""))
    entities = {name: float(contains_alias(prose, aliases)) for name, aliases in profile["entities"].items()}
    base.update(open_actions=open_count, any_open=float(open_count > 0), search_actions=actions.count("S"),
                find_actions=actions.count("F"), citation_domains=len(domains), answer_words=len(tokens(prose)),
                entity_mentions=sum(entities.values()), target_mention=float(contains_alias(prose, case["target_aliases"])))
    if known:
        base.update(search_queries=len(queries), site_query_share=sum(bool(re.search(r"\bsite:", q)) for q in queries) / max(1, len(queries)))
    else:
        details["missing"].append("hosted_or_custom_query_list")
    vectors = {}
    for name, spec in profile["distributions"].items():
        if spec["kind"] == "count":
            value = base.get(spec["field"])
            if value is not None:
                vectors[name] = bin_vector(value, spec["edges"])
        elif spec["kind"] == "citation_domains":
            groups = spec["groups"] + ["OTHER", "NONE"]
            vector = [0.0] * len(groups)
            if not domains:
                vector[-1] = 1.0
            else:
                for domain in domains:
                    vector[groups.index(domain_group(domain, spec["groups"]))] += 1 / len(domains)
            vectors[name] = vector
        elif spec["kind"] == "entities":
            weights = list(entities.values())
            total = sum(weights)
            vectors[name] = [x / total for x in weights] + [0.0] if total else [0.0] * len(weights) + [1.0]
    details.update(queries=queries if known else None, action_sequence=actions, entity_presence=entities,
                   citation_domains=domains, local_failed_opens=metrics.get("failed_opens"),
                   successful_opens=metrics.get("successful_opens"), open_failure_types=metrics.get("open_failure_types"),
                   unexposed_url_attempts=metrics.get("unexposed_url_attempts"),
                   explicit_link_follow=metrics.get("explicit_product_to_hub_follow"),
                   elapsed_seconds=trace.get("elapsed_seconds"), estimated_usd=trace.get("usage", {}).get("estimated_usd"))
    details["clipped"] = {name: value for name, value in base.items()
                          if name in profile["metrics"] and value > profile["metrics"][name]["cap"]}
    return {"scalar": base, "vectors": vectors, "details": details}
