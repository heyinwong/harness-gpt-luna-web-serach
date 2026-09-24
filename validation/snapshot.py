"""Snapshot an operator-declared public-web corpus before model evaluation."""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import ipaddress
import re
import socket
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from bs4 import BeautifulSoup

from search_lab import canonical


def public_url(url):
    normalized = canonical(url)
    parsed = urlsplit(normalized)
    if parsed.port not in (None, 80, 443):
        raise ValueError("Only standard public HTTP(S) ports are allowed")
    addresses = socket.getaddrinfo(parsed.hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError("Snapshot URLs must resolve to public addresses")
    return normalized


class PublicRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def extract_html(content, url):
    soup = BeautifulSoup(content, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else url
    root = soup.find("main") or soup.find(attrs={"role": "main"}) or soup.find("article") or soup.body or soup
    # Aside elements can contain decisive footnotes, caveats or award evidence.
    # Only remove executable/interactive/navigation containers, not semantic asides.
    for node in root.select("script,style,nav,footer,header,form,noscript"):
        node.decompose()
    anchor_names = []
    for node in root.find_all(True):
        name = node.get("id") or (node.get("name") if node.name == "a" else None)
        if name:
            node.insert_before(f"\ue000{len(anchor_names)}\ue001")
            anchor_names.append(name)
    for a in root.find_all("a", href=True):
        label = a.get_text(" ", strip=True)
        target = urljoin(url, a["href"])
        if label and urlsplit(target).scheme in ("http", "https"):
            a.replace_with(f"[{label}]({target})")
    for node in root.find_all(["p", "div", "section", "li", "tr", "pre", "h1", "h2", "h3", "h4", "br"]):
        node.insert_before("\n")
        node.insert_after("\n")
    # Preserve adjacency of inline syntax: newline='' must not become newline\n=\n''.
    rendered = re.sub(r"[ \t\r\f\v]+", " ", root.get_text("", strip=False))
    rendered = re.sub(r"\n[ \t]*\n+", "\n\n", rendered).strip()
    anchors, chunks, cursor, length = {}, [], 0, 0
    for match in re.finditer("\ue000(\\d+)\ue001", rendered):
        chunk = rendered[cursor:match.start()]
        chunks.append(chunk)
        length += len(chunk)
        anchors.setdefault(anchor_names[int(match.group(1))], length)
        cursor = match.end()
    chunks.append(rendered[cursor:])
    return title, "".join(chunks), anchors


def fetch(url):
    try:
        public_url(url)
        request = Request(url, headers={"User-Agent": "LunaSearchValidation/1.0 (public documentation snapshot)"})
        with build_opener(PublicRedirect()).open(request, timeout=35) as response:
            final = public_url(response.url)
            raw = response.read(3000001)
            if len(raw) > 3000000:
                raise ValueError("Page exceeds the 3MB snapshot limit")
            content_type = response.headers.get_content_type()
            charset = response.headers.get_content_charset() or "utf-8"
        if content_type == "text/html":
            title, text, anchors = extract_html(raw.decode(charset, errors="replace"), final)
        elif content_type in ("text/plain", "text/markdown"):
            title, text = final, raw.decode(charset, errors="replace")
            anchors = {}
        else:
            raise ValueError("Unsupported snapshot content type")
        if len(text.strip()) < 150:
            raise ValueError("Extracted page is empty or too short")
        return {"url": canonical(url), "resolved_url": final, "title": title, "text": text, "anchors": anchors,
                "retrieved_at": datetime.now(timezone.utc).isoformat(), "content_sha256": hashlib.sha256(raw).hexdigest(),
                "fetch_status": "ok"}
    except Exception as exc:
        return {"url": url, "fetch_status": "failed", "error_type": type(exc).__name__}


def snapshot(urls):
    if len(set(urls)) != len(urls):
        raise ValueError("Duplicate snapshot URLs")
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        pages = list(pool.map(fetch, urls))
    failed = [p for p in pages if p["fetch_status"] != "ok"]
    return {"description": "Public documentation snapshots for a generic search-behaviour pilot; incomplete coverage of the live web.",
            "kind": "observed_reference", "pages": [p for p in pages if p["fetch_status"] == "ok"], "failures": failed}
