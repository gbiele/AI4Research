#!/usr/bin/env python3
"""
Download PDFs for DOIs listed in chatbots/*.md into pdfs/<chatbot_folder>/.

Resolution order: Unpaywall (all OA locations) -> Crossref pdf links ->
 landing page (urllib, then curl) -> extract PDF URLs from HTML.
Uses curl.exe as fallback when urllib is blocked (common for publisher sites).
"""
from __future__ import annotations

import html as html_module
import json
import re
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHATBOTS = ROOT / "chatbots"
PDFS = ROOT / "pdfs"
EMAIL = "ai4research-local@local"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

CTX = __import__("ssl").create_default_context()

# DOI path may contain parentheses, e.g. 10.1016/S1573-4412(07)06070-9
DOI_RE = re.compile(r"https?://doi\.org/(10\.\d{4,9}/[^\s\]]+)", re.I)

CURL = shutil.which("curl") or shutil.which("curl.exe")


def find_dois_in_md(text: str) -> list[str]:
    out: list[str] = []
    for m in DOI_RE.finditer(text):
        d = m.group(1).rstrip(").,;")
        if d not in out:
            out.append(d)
    return out


def slug_from_doi(doi: str) -> str:
    return doi.replace("/", "_").replace("(", "").replace(")", "")


def referer_for_url(url: str) -> str:
    p = urllib.parse.urlparse(url)
    if p.scheme and p.netloc:
        return f"{p.scheme}://{p.netloc}/"
    return "https://www.google.com/"


def http_get_urllib(url: str) -> tuple[bytes, str]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=90, context=CTX) as resp:
        return resp.read(), resp.geturl()


def curl_fetch(url: str) -> bytes | None:
    if not CURL:
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
    tmp.close()
    path = Path(tmp.name)
    try:
        subprocess.run(
            [
                CURL,
                "-L",
                "-s",
                "--max-time",
                "120",
                "-A",
                USER_AGENT,
                "-e",
                referer_for_url(url),
                "-o",
                str(path),
                url,
            ],
            check=True,
            timeout=130,
        )
        data = path.read_bytes()
        return data if data else None
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None
    finally:
        path.unlink(missing_ok=True)


def http_get(url: str) -> tuple[bytes, str]:
    try:
        return http_get_urllib(url)
    except Exception:
        c = curl_fetch(url)
        if c is None:
            raise
        return c, url


def unpaywall_lookup(doi: str) -> dict | None:
    q = urllib.parse.quote(doi, safe="")
    url = f"https://api.unpaywall.org/v2/{q}?email={urllib.parse.quote(EMAIL)}"
    try:
        data, _ = http_get_urllib(url)
        return json.loads(data.decode("utf-8", errors="replace"))
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError):
        return None


def iter_unpaywall_pdf_urls(uw: dict) -> list[str]:
    seen: list[str] = []
    for loc in [uw.get("best_oa_location"), *list(uw.get("oa_locations") or [])]:
        if not loc:
            continue
        for key in ("url_for_pdf", "url"):
            u = loc.get(key)
            if not u:
                continue
            ul = u.lower()
            if ul.endswith(".pdf") or "/pdf" in ul or "pdf?" in ul:
                if u not in seen:
                    seen.append(u)
            elif key == "url_for_pdf":
                if u not in seen:
                    seen.append(u)
    return seen


def europepmc_pdf_urls(doi: str) -> list[str]:
    q = urllib.parse.quote(doi, safe="")
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{q}&resultType=core&format=json"
    try:
        data, _ = http_get_urllib(url)
        results = json.loads(data.decode("utf-8", errors="replace"))["resultList"].get("result") or []
        if not results:
            return []
        r0 = results[0]
        ftl = r0.get("fullTextUrlList")
        if not ftl:
            return []
        items = ftl.get("fullTextUrl")
        if isinstance(items, dict):
            items = [items]
        elif not items:
            return []
        out: list[str] = []
        for item in items:
            if item.get("documentStyle") != "pdf":
                continue
            if item.get("availabilityCode") != "F":
                continue
            u = item.get("url")
            if u and "pdf" in u.lower():
                out.append(u)
        return out
    except Exception:
        return []


def crossref_pdf_urls(doi: str) -> list[str]:
    q = urllib.parse.quote(doi, safe="")
    url = f"https://api.crossref.org/works/{q}"
    try:
        data, _ = http_get_urllib(url)
        msg = json.loads(data.decode("utf-8", errors="replace"))["message"]
    except Exception:
        return []
    out: list[str] = []
    for link in msg.get("link") or []:
        u = link.get("URL") or ""
        ct = (link.get("content-type") or "").lower()
        if not u:
            continue
        if ct == "application/pdf" or "/pdf" in u.lower() or u.lower().endswith(".pdf"):
            if u not in out:
                out.append(u)
    return out


def _reg_domain(netloc: str) -> str:
    host = (netloc or "").split(":")[0].lower()
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host


def _resolve_url(u: str, base_url: str) -> str:
    u = html_module.unescape(u.strip())
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        p = urllib.parse.urlparse(base_url)
        return f"{p.scheme}://{p.netloc}{u}"
    return u


def extract_pdf_urls_from_html(body: bytes, base_url: str) -> list[str]:
    """Prefer citation_pdf_url meta; only accept same-registrable-domain hrefs (avoids bogus CMS PDFs)."""
    text = body.decode("utf-8", errors="replace")
    meta_urls: list[str] = []
    for pat in (
        r'citation_pdf_url"\s+content="([^"]+)"',
        r"citation_pdf_url'\s+content='([^']+)'",
        r'<meta\s+name="citation_pdf_url"\s+content="([^"]+)"',
    ):
        for m in re.finditer(pat, text, re.I):
            meta_urls.append(m.group(1))

    base_dom = _reg_domain(urllib.parse.urlparse(base_url).netloc)
    href_urls: list[str] = []
    for m in re.finditer(r'href="([^"]+\.pdf[^"]*)"', text, re.I):
        u = m.group(1)
        if "javascript" in u.lower():
            continue
        abs_u = _resolve_url(u, base_url)
        if not abs_u.startswith("http"):
            continue
        if _reg_domain(urllib.parse.urlparse(abs_u).netloc) != base_dom:
            continue
        href_urls.append(abs_u)

    ordered = meta_urls + href_urls
    abs_urls: list[str] = []
    for u in ordered:
        u = _resolve_url(u, base_url)
        if not u.startswith("http"):
            continue
        if u not in abs_urls:
            abs_urls.append(u)
    return abs_urls


def fetch_pdf_bytes(url: str) -> bytes | None:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/pdf,*/*"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=120, context=CTX) as resp:
            ct = (resp.headers.get("Content-Type") or "").lower()
            data = resp.read()
        if data[:4] == b"%PDF" or "pdf" in ct:
            return data if data[:4] == b"%PDF" else None
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError):
        pass
    c = curl_fetch(url)
    if c and c[:4] == b"%PDF":
        return c
    return None


def try_urls(urls: list[str]) -> tuple[bytes | None, str | None]:
    for u in urls:
        data = fetch_pdf_bytes(u)
        if data:
            return data, u
        time.sleep(0.2)
    return None, None


def fetch_landing_html(doi: str) -> tuple[bytes, str] | tuple[None, str]:
    landing = f"https://doi.org/{urllib.parse.quote(doi, safe='')}"
    try:
        body, final = http_get_urllib(landing)
        return body, final
    except Exception:
        c = curl_fetch(landing)
        if c:
            return c, landing
        return None, f"failed: {landing}"


def download_for_doi(doi: str) -> tuple[bool, bytes, str]:
    uw = unpaywall_lookup(doi)

    if uw:
        ulist = iter_unpaywall_pdf_urls(uw)
        data, src = try_urls(ulist)
        if data:
            return True, data, f"unpaywall: {src}"

    xlist = crossref_pdf_urls(doi)
    data, src = try_urls(xlist)
    if data:
        return True, data, f"crossref: {src}"

    emlist = europepmc_pdf_urls(doi)
    data, src = try_urls(emlist)
    if data:
        return True, data, f"europepmc: {src}"

    result = fetch_landing_html(doi)
    if result[0] is None:
        return False, b"", str(result[1])
    html_bytes, final = result

    if html_bytes[:4] == b"%PDF":
        return True, html_bytes, f"doi redirect PDF: {final}"

    for candidate in extract_pdf_urls_from_html(html_bytes, final):
        data = fetch_pdf_bytes(candidate)
        if data:
            return True, data, f"html: {candidate}"
        time.sleep(0.2)

    extra = ""
    if uw:
        extra = f" is_oa={uw.get('is_oa')} title={uw.get('title', '')[:60]!r}"
    return False, b"", f"no PDF found{extra}"


def main() -> None:
    mapping = [
        ("methods_consultant_psychology.md", "methods_consultant_psychology"),
        ("methods_consultant_econometrics.md", "methods_consultant_econometrics"),
        ("methods_consultant_epidemiology.md", "methods_consultant_epidemiology"),
    ]

    PDFS.mkdir(parents=True, exist_ok=True)
    summary: list[tuple[str, str, str]] = []

    for md_name, folder in mapping:
        md_path = CHATBOTS / md_name
        if not md_path.exists():
            print(f"Skip missing {md_path}")
            continue
        text = md_path.read_text(encoding="utf-8")
        dois = find_dois_in_md(text)
        out_dir = PDFS / folder
        out_dir.mkdir(parents=True, exist_ok=True)
        print(f"\n=== {folder} ({len(dois)} DOIs) ===")

        for doi in dois:
            fn = slug_from_doi(doi) + ".pdf"
            dest = out_dir / fn
            if dest.exists() and dest.stat().st_size > 1000:
                print(f"  OK (cached): {doi}")
                summary.append((folder, doi, "cached"))
                continue

            ok, data, msg = download_for_doi(doi)

            if ok and data:
                dest.write_bytes(data)
                print(f"  OK: {doi} -> {fn} ({msg})")
                summary.append((folder, doi, msg))
            else:
                print(f"  FAIL: {doi} ({msg})")
                summary.append((folder, doi, f"FAIL: {msg}"))

            time.sleep(0.4)

    fail_log = PDFS / "_download_summary.txt"
    lines = [f"{a}\t{b}\t{c}" for a, b, c in summary]
    fail_log.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nWrote {fail_log}")


if __name__ == "__main__":
    main()
