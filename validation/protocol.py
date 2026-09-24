"""Immutable benchmark manifests and a conservative, simultaneous equivalence report."""
import hashlib
import json

from .metrics import extract
from .statistics import bounded_interval, distribution_verdict, equivalence, mean, total_variation_interval


def fingerprint(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_profile(profile):
    if not 0 < profile["confidence"] < 1 or profile["repeats"] < 2:
        raise ValueError("Use a confidence in (0,1) and at least two repetitions")
    if profile["split"] not in ("pilot", "calibration", "validation"):
        raise ValueError("Unknown benchmark split")
    cases = profile["cases"]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Case IDs must be unique and nonempty")
    categories = set(profile["categories"])
    if not categories or len(categories) != len(profile["categories"]) or "overall" in categories:
        raise ValueError("Categories must be unique, nonempty and exclude the reserved overall scope")
    if not profile["metrics"] or not profile["distributions"]:
        raise ValueError("Register both scalar and distribution checks")
    if not {"completed", "budget_limited"} <= profile["metrics"].keys():
        raise ValueError("Register completion and budget-limited metrics")
    for case in cases:
        if case["category"] not in categories or not case["question"].strip() or not case["target_aliases"]:
            raise ValueError("Every case needs a registered category, question and target aliases")
    for spec in profile["metrics"].values():
        if spec["cap"] <= 0 or not 0 < spec["margin"] <= spec["cap"]:
            raise ValueError("Invalid scalar cap or equivalence margin")
    for spec in profile["distributions"].values():
        if not 0 < spec["margin"] < 1:
            raise ValueError("Distribution margin must be in (0,1)")
        if spec["kind"] == "count" and spec["edges"] != sorted(set(spec["edges"])):
            raise ValueError("Count distribution edges must be strictly increasing")


def dimensions(spec, profile):
    if spec["kind"] == "count":
        return len(spec["edges"]) + 1
    if spec["kind"] == "citation_domains":
        return len(spec["groups"]) + 2
    if spec["kind"] == "entities":
        return len(profile["entities"]) + 1
    raise ValueError("Unknown distribution kind")


def observations(manifest, traces):
    profile = manifest["profile"]
    result, errors = {}, []
    cases = {c["id"]: c for c in profile["cases"]}
    digest = fingerprint(manifest)
    for trace in traces:
        job = trace.get("benchmark_job", {})
        key = (job.get("case_id"), job.get("repeat"), trace.get("mode"))
        if trace.get("benchmark_manifest_sha256") != digest:
            errors.append("manifest_mismatch")
            continue
        if key[0] not in cases or key[1] not in range(profile["repeats"]) or key[2] not in ("custom", "live") or job.get("mode") != key[2]:
            errors.append("invalid_job_identity")
            continue
        if key in result:
            raise ValueError("Duplicate case/repetition/mode trace")
        if trace.get("question") != cases[key[0]]["question"] or trace.get("model") != profile["model"]:
            errors.append("question_or_model_mismatch")
            continue
        if trace.get("reasoning") != profile["runner"]["reasoning"] or trace.get("instructions") != profile["instructions"]:
            errors.append("reasoning_or_instructions_mismatch")
            continue
        if trace["mode"] == "custom" and (trace.get("arm") != "reference" or trace.get("corpus_sha256") != manifest["corpus_sha256"]):
            errors.append("custom_corpus_or_treatment_mismatch")
            continue
        expected = profile["runner"]
        if any((trace.get("allowed_domains") if k == "allowed_domains" else trace.get("config", {}).get(k)) != v for k, v in expected.items() if k != "reasoning"):
            errors.append("runner_config_mismatch")
            continue
        returned = {r.get("model") for r in trace.get("responses", []) if r.get("model")}
        if returned and returned != {profile["model"]}:
            errors.append("returned_model_mismatch")
            continue
        result[key] = extract(trace, cases[key[0]], profile)
    return result, sorted(set(errors))


def analyze(manifest, traces):
    profile = manifest["profile"]
    validate_profile(profile)
    observed, flags = observations(manifest, traces)
    repeats = profile["repeats"]
    cases = profile["cases"]
    expected_runs = len(cases) * repeats * 2
    if len(observed) != expected_runs:
        flags.append("planned_runs_missing")
    if profile["split"] != "validation":
        flags.append("exploratory_split_not_confirmatory")
    if profile.get("sampling") != "independent_representative_holdout":
        flags.append("representative_independent_sampling_not_declared")
    if len(cases) < profile["minimum_questions"]:
        flags.append("too_few_independent_questions")
    if any(obs["details"]["clipped"] for obs in observed.values() if "clipped" in obs["details"]):
        flags.append("values_exceed_registered_caps")
    scopes = ["overall"] + profile["categories"]
    # Include every coordinate, even missing ones, so missingness cannot reduce correction.
    scalar_count = len(profile["metrics"])
    vector_count = sum(dimensions(s, profile) for s in profile["distributions"].values())
    # Absolute quality gates: both modes' completion and budget-limited probabilities.
    family_size = len(scopes) * (scalar_count + vector_count + 4)
    alpha = (1 - profile["confidence"]) / family_size
    rows = []
    for scope in scopes:
        subset = [c for c in cases if scope == "overall" or c["category"] == scope]
        if not subset:
            flags.append("empty_registered_category:" + scope)
        if scope != "overall" and len(subset) < profile["minimum_questions_per_category"]:
            flags.append("too_few_questions_in_category:" + scope)
        def clusters(kind, name, dim=None):
            xs, ys, included = [], [], []
            for case in subset:
                per_mode = {}
                for mode in ("custom", "live"):
                    values = []
                    for repeat in range(repeats):
                        obs = observed.get((case["id"], repeat, mode))
                        if obs is None or name not in obs[kind]:
                            break
                        value = obs[kind][name]
                        values.append(value[dim] if dim is not None else value)
                    if len(values) == repeats:
                        per_mode[mode] = values
                if len(per_mode) == 2:
                    if kind == "scalar":
                        cap = profile["metrics"][name]["cap"]
                        xs.append(mean([min(cap, v) for v in per_mode["custom"]]))
                        ys.append(mean([min(cap, v) for v in per_mode["live"]]))
                    else:
                        xs.append(mean(per_mode["custom"]))
                        ys.append(mean(per_mode["live"]))
                    included.append(case["id"])
            return xs, ys, included
        for name, spec in profile["metrics"].items():
            xs, ys, ids = clusters("scalar", name)
            interval = bounded_interval([x-y for x,y in zip(xs,ys)], -spec["cap"], spec["cap"], alpha)
            status = equivalence(interval, spec["margin"])
            if len(ids) != len(subset):
                flags.append("missing_metric_data:" + scope + ":" + name)
                if status == "equivalent":
                    status = "inconclusive"
            rows.append({"scope": scope, "name": name, "kind": "mean_difference", "custom": mean(xs) if xs else None,
                         "live": mean(ys) if ys else None, "interval": interval, "margin": spec["margin"],
                         "status": status, "n_questions": len(ids), "description": spec["description"], "cap": spec["cap"]})
        for name, spec in profile["distributions"].items():
            bins, pc, pl, ids = [], [], [], []
            for dim in range(dimensions(spec, profile)):
                xs, ys, ids = clusters("vectors", name, dim)
                bins.append(bounded_interval([x-y for x,y in zip(xs,ys)], -1, 1, alpha))
                pc.append(mean(xs) if xs else 0)
                pl.append(mean(ys) if ys else 0)
            interval = total_variation_interval(bins) if ids else {"estimate": None, "low": 0, "high": 1}
            status = distribution_verdict(interval, spec["margin"]) if ids else "inconclusive"
            if len(ids) != len(subset):
                flags.append("missing_metric_data:" + scope + ":" + name)
                if status == "equivalent":
                    status = "inconclusive"
            rows.append({"scope": scope, "name": name, "kind": "total_variation", "custom": pc, "live": pl,
                         "interval": interval, "margin": spec["margin"], "status": status, "n_questions": len(ids),
                         "coordinate_intervals": bins, "description": spec["description"]})
        for mode in ("custom", "live"):
            for name, limit, direction in [("completed", profile["quality"]["minimum_completion"], "minimum"),
                                           ("budget_limited", profile["quality"]["maximum_budget_limited"], "maximum")]:
                vals = []
                for case in subset:
                    group = [observed.get((case["id"], r, mode)) for r in range(repeats)]
                    if all(g is not None for g in group):
                        vals.append(mean([g["scalar"][name] for g in group]))
                interval = bounded_interval(vals, 0, 1, alpha)
                status = "inconclusive"
                if vals:
                    if direction == "minimum":
                        status = "equivalent" if interval["low"] >= limit else "different" if interval["high"] < limit else "inconclusive"
                    else:
                        status = "equivalent" if interval["high"] <= limit else "different" if interval["low"] > limit else "inconclusive"
                rows.append({"scope": scope, "name": mode + "_" + name + "_quality", "kind": "absolute_quality",
                             "interval": interval, "margin": limit, "direction": direction, "status": status, "n_questions": len(vals),
                             "description": "Absolute reliability requirement, not merely similarity between two failing systems."})
    statuses = [r["status"] for r in rows]
    verdict = "different" if "different" in statuses else "equivalent" if not flags and all(s == "equivalent" for s in statuses) else "inconclusive"
    point_failures = [r["name"] for r in rows if r["scope"] == "overall" and r["interval"]["estimate"] is not None
                      and r["kind"] != "absolute_quality" and abs(r["interval"]["estimate"]) > r["margin"]]
    # Live/live variability is descriptive, using the first two independent repetitions.
    repeatability = {}
    for name in profile["metrics"]:
        diffs = []
        for case in cases:
            a, b = observed.get((case["id"], 0, "live")), observed.get((case["id"], 1, "live"))
            if a and b and name in a["scalar"] and name in b["scalar"]:
                diffs.append(abs(a["scalar"][name] - b["scalar"][name]))
        if diffs:
            repeatability[name] = {"mean_absolute_repeat_difference": mean(diffs), "n_questions": len(diffs)}
    return {"verdict": verdict, "confidence_level": profile["confidence"], "simultaneous_coordinates": family_size,
            "interval_method": "Two-sided empirical Bernstein bounds with Bonferroni correction; paired question clusters.",
            "scope": profile["scope"], "manifest_sha256": fingerprint(manifest), "planned_runs": expected_runs,
            "observed_runs": len(observed), "n_independent_questions": len(cases), "flags": sorted(set(flags)),
            "point_estimates_outside_tolerance": point_failures, "rows": rows, "live_repeatability": repeatability,
            "run_metrics": [{"case_id": k[0], "repeat": k[1], "mode": k[2], **v} for k,v in observed.items()],
            "interpretation": "Confidence is coverage of registered metric bounds under the sampling assumptions; it is not a probability that two agents are identical or that results transfer to all future designs."}


def markdown(result):
    def fmt(x):
        return "—" if x is None else f"{x:.3f}"
    lines = ["# Behavioural validation", "", f"**Verdict: {result['verdict'].upper()}**", "",
             f"Registered simultaneous confidence level: {result['confidence_level']:.0%}. {result['observed_runs']}/{result['planned_runs']} runs recorded across {result['n_independent_questions']} questions.",
             "", result["interpretation"], "", "Scope: " + result["scope"], "", "## Overall metrics", "",
             "Differences are custom minus live. TV is total variation distance (0 identical, 1 disjoint). Count means are capped as registered; raw values remain in the JSON.", "",
             "| Metric | Custom | Live | Difference / TV | Simultaneous interval | Tolerance | Verdict |",
             "|---|---:|---:|---:|---|---|---|"]
    for row in result["rows"]:
        if row["scope"] != "overall":
            continue
        interval = row["interval"]
        custom = fmt(row.get("custom")) if not isinstance(row.get("custom"), list) else "distribution"
        live = fmt(row.get("live")) if not isinstance(row.get("live"), list) else "distribution"
        lines.append(f"| {row['name']} | {custom} | {live} | {fmt(interval['estimate'])} | [{fmt(interval['low'])}, {fmt(interval['high'])}] | {row.get('direction', '±' if row['kind']=='mean_difference' else '≤')} {row['margin']} | {row['status']} |")
    lines += ["", "## Validity gates", ""] + (["- " + f for f in result["flags"]] or ["No validity gates blocked."])
    lines += ["", "## Point estimates needing attention", ""] + (["- " + f for f in result["point_estimates_outside_tolerance"]] or ["None; this alone is not evidence of equivalence."])
    lines += ["", "## Category checks", "", "| Category | Equivalent | Different | Inconclusive |", "|---|---:|---:|---:|"]
    for scope in sorted({r["scope"] for r in result["rows"]} - {"overall"}):
        rows = [r for r in result["rows"] if r["scope"] == scope]
        lines.append(f"| {scope} | {sum(r['status']=='equivalent' for r in rows)} | {sum(r['status']=='different' for r in rows)} | {sum(r['status']=='inconclusive' for r in rows)} |")
    lines += ["", "## Live baseline repeatability", "", "Repeated runs of hosted Luna are compared with each other; no assumption of deterministic answers is made.", "", "| Metric | Mean absolute live/live repeat difference | Questions |", "|---|---:|---:|"]
    for name, value in result["live_repeatability"].items():
        lines.append(f"| {name} | {value['mean_absolute_repeat_difference']:.3f} | {value['n_questions']} |")
    if "coverage" in result:
        c = result["coverage"]
        lines += ["", "## Corpus coverage diagnostic", "", f"{c['source_urls_in_snapshot']}/{c['reported_hosted_source_urls']} reported hosted source URLs match a snapshot page.", "", c["notice"]]
    if "precision_plan" in result:
        p = result["precision_plan"]
        lines += ["", "## Sample-size planning", "", p["notice"], "",
                  f"The strictest registered check requires at least {p['largest_per_scope_floor']} questions per evaluated scope even in this optimistic scenario. The configured minimum question count is only an eligibility floor."]
    lines += ["", "## Next decision", "", "Do not tune against held-out results or widen tolerances after seeing them. Use a calibration set to diagnose differences, then freeze a new implementation and test new held-out questions. A small or unfinished pilot cannot produce a confirmatory pass."]
    return "\n".join(lines) + "\n"
