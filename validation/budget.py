"""Serial request reservations against a user-authorized pilot budget."""
import json
from pathlib import Path

import search_lab as lab


class BudgetedTransport:
    def __init__(self, path, maximum_usd, transport=lab.request_response):
        self.path = Path(path)
        self.maximum = maximum_usd
        self.transport = transport
        self.ledger = json.loads(self.path.read_text()) if self.path.exists() else {"maximum_usd": maximum_usd, "reserved_or_charged_usd": 0, "requests": []}
        if self.ledger["maximum_usd"] != maximum_usd:
            raise ValueError("Existing budget cannot be silently changed")
        if any(r["status"] in ("pending", "unknown") for r in self.ledger["requests"]):
            raise ValueError("Previous request has unknown billing outcome; inspect before resuming")

    def __call__(self, payload):
        if payload["model"] != "gpt-5.6-luna":
            raise RuntimeError("Budget pricing is only configured for gpt-5.6-luna")
        hosted = any(t["type"] in ("web_search", "web_search_preview") for t in payload["tools"])
        if hosted and payload.get("reasoning", {}).get("effort") == "none":
            raise RuntimeError("Budgeted hosted pilot requires a reasoning effort other than none")
        encoded_bytes = len(json.dumps(payload, ensure_ascii=False).encode())
        # Rich multi-query search results can exceed 200k bytes. Keep a byte-based
        # upper bound below the model's context capacity; reserve every byte as a
        # token before the request rather than truncating evidence to save budget.
        if encoded_bytes > 750000:
            raise RuntimeError("Pilot request exceeds the declared 750k-byte client-input ceiling")
        # Bytes conservatively bound ordinary BPE text tokens. Hosted retrieval is hidden,
        # so reserve the entire documented 1.05M model window for hosted input instead.
        input_reserve = 1050000 if hosted else encoded_bytes + 4096
        tools_reserve = payload.get("max_tool_calls", 0) * .01 if hosted else 0
        reserve = input_reserve * .50 / 1e6 + payload["max_output_tokens"] * 1.80 / 1e6 + tools_reserve
        if self.ledger["reserved_or_charged_usd"] + reserve > self.maximum:
            raise RuntimeError("pilot_budget_reservation_blocked: not enough unreserved pilot budget for the next request")
        entry = {"status": "pending", "reserved_usd": reserve, "hosted": hosted}
        self.ledger["requests"].append(entry)
        self.ledger["reserved_or_charged_usd"] += reserve
        lab.save(self.path, self.ledger)
        try:
            response = self.transport(payload)
        except Exception:
            entry["status"] = "unknown"
            lab.save(self.path, self.ledger)
            raise
        usage = response.get("usage")
        if not usage:
            entry["status"] = "unknown"
            lab.save(self.path, self.ledger)
            raise RuntimeError("Missing usage after API response; reservation retained and pilot stopped")
        billed_searches = lab.hosted_metrics([response])["search_actions"] if hosted else 0
        conservative = usage["input_tokens"] * .50 / 1e6 + usage["output_tokens"] * 1.80 / 1e6 + billed_searches * .01
        entry.update(status="settled", conservative_usd=conservative, response_id=response.get("id"))
        self.ledger["reserved_or_charged_usd"] += conservative - reserve
        lab.save(self.path, self.ledger)
        if conservative > reserve:
            raise RuntimeError("Observed usage exceeded the pricing reservation; stop and inspect billing before continuing")
        return response
