#!/usr/bin/env python3
"""
Download PDFs for DOIs listed in chatbots/*.md into pdfs/<chatbot_folder>/.

Environment (optional):
  AI4RESEARCH_UNPAYWALL_EMAIL — override mailto used for Unpaywall API and OpenAlex User-Agent (default: in-script EMAIL).
  AI4RESEARCH_CORE_API_KEY — CORE API v3 bearer token when set (helps quota).
  AI4RESEARCH_COOKIE_FILE — Netscape/Mozilla cookies.txt for institutional PDF access.
  AI4RESEARCH_HTTP_COOKIE — raw Cookie header (alternative to file).
  AI4RESEARCH_USE_CURL_CFFI=1 — use curl-cffi TLS impersonation for PDF GET when urllib/curl.exe return HTML.
  AI4RESEARCH_PLAYWRIGHT=1 — last-resort PDF fetch via headless Chromium (requires: pip install playwright && playwright install).

Resolution order: Unpaywall -> Semantic Scholar -> OpenAlex -> Crossref ->
 Europe PMC (DOI) -> CORE -> PMC concrete PDFs (Europe PMC by PMCID) ->
 arXiv/PMC guesses -> landing HTML parsing -> optional curl_cffi -> optional Playwright.
Never commit real cookie files.

CLI: python download_chatbot_pdfs.py [--doi DOI] [--out PATH] [--dry-run]
      (no args: scan chatbots/*.md as before)
"""
from __future__ import annotations

import argparse
import html as html_module
import json
import os
import random
import re
import shutil
import subprocess
import tempfile
import time
import sys
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import MozillaCookieJar
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHATBOTS = ROOT / "chatbots"
PDFS = ROOT / "pdfs"
EMAIL = "guido.biele@fhi.no"


def _unpaywall_email() -> str:
    v = os.environ.get("AI4RESEARCH_UNPAYWALL_EMAIL", "").strip()
    return v if v else EMAIL


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

CTX = __import__("ssl").create_default_context()

# Max retries for transient HTTP errors (APIs + PDF hosts)
_MAX_RETRIES = 4
_RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _body_snippet(data: bytes, max_len: int = 220) -> str:
    return data[:max_len].decode("utf-8", errors="replace").replace("\n", " ")


def openalex_user_agent() -> str:
    """OpenAlex requests a mailto in the User-Agent string (polite pool)."""
    return f"{USER_AGENT} mailto:{_unpaywall_email()}"


# DOI path may contain parentheses, e.g. 10.1016/S1573-4412(07)06070-9
DOI_RE = re.compile(r"https?://doi\.org/(10\.\d{4,9}/[^\s\]]+)", re.I)

CURL = shutil.which("curl") or shutil.which("curl.exe")

_cookie_opener: urllib.request.OpenerDirector | None = None
_cookie_opener_source: str | None = None


def _cookie_file_path() -> str | None:
    raw = os.environ.get("AI4RESEARCH_COOKIE_FILE", "").strip()
    if not raw:
        return None
    path = Path(raw).expanduser()
    return str(path.resolve()) if path.is_file() else None


def _cookie_header_value() -> str | None:
    h = os.environ.get("AI4RESEARCH_HTTP_COOKIE", "").strip()
    return h or None


def _get_cookie_opener() -> urllib.request.OpenerDirector | None:
    global _cookie_opener, _cookie_opener_source
    fp = _cookie_file_path()
    if fp is None:
        return None
    if _cookie_opener is not None and _cookie_opener_source == fp:
        return _cookie_opener
    try:
        cj = MozillaCookieJar(fp)
        cj.load(ignore_discard=True, ignore_expires=True)
    except OSError as e:
        print(f"AI4RESEARCH_COOKIE_FILE: could not load {fp}: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"AI4RESEARCH_COOKIE_FILE: invalid or unsupported jar {fp}: {e}", file=sys.stderr)
        return None
    https_handler = urllib.request.HTTPSHandler(context=CTX)
    _cookie_opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cj),
        https_handler,
    )
    _cookie_opener_source = fp
    return _cookie_opener


def _apply_cookie_header(req: urllib.request.Request) -> None:
    hv = _cookie_header_value()
    if hv:
        req.add_header("Cookie", hv)


def _urlopen_with_cookies(req: urllib.request.Request, timeout: int):
    opener = _get_cookie_opener()
    if opener is not None:
        return opener.open(req, timeout=timeout)
    _apply_cookie_header(req)
    return urllib.request.urlopen(req, timeout=timeout, context=CTX)


def _curl_cookie_args() -> list[str]:
    fp = _cookie_file_path()
    if fp:
        return ["-b", fp]
    hv = _cookie_header_value()
    if hv:
        return ["-b", hv]
    return []


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


def _http_get_urllib_once(
    url: str,
    *,
    user_agent: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> tuple[bytes, str]:
    h = {
        "User-Agent": user_agent or USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/pdf;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    if extra_headers:
        h.update(extra_headers)
    req = urllib.request.Request(url, headers=h, method="GET")
    with _urlopen_with_cookies(req, 90) as resp:
        return resp.read(), resp.geturl()


def http_get_urllib(
    url: str,
    *,
    openalex_mailto: bool = False,
    extra_headers: dict[str, str] | None = None,
) -> tuple[bytes, str]:
    ua = openalex_user_agent() if openalex_mailto or "api.openalex.org" in url else USER_AGENT
    last_err: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        try:
            return _http_get_urllib_once(
                url,
                user_agent=ua,
                extra_headers=extra_headers,
            )
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in _RETRYABLE_STATUS and attempt < _MAX_RETRIES - 1:
                time.sleep((2**attempt) * 0.4 + random.random() * 0.3)
                continue
            raise
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last_err = e
            if attempt < _MAX_RETRIES - 1:
                time.sleep((2**attempt) * 0.3 + random.random() * 0.2)
                continue
            raise
    assert last_err is not None
    raise last_err


def curl_fetch(url: str, referer: str | None = None) -> bytes | None:
    if not CURL:
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".bin")
    tmp.close()
    path = Path(tmp.name)
    ref = referer or referer_for_url(url)
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
                ref,
                *_curl_cookie_args(),
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
    url = f"https://api.unpaywall.org/v2/{q}?email={urllib.parse.quote(_unpaywall_email())}"
    try:
        data, _ = http_get_urllib(url)
        return json.loads(data.decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read() or b""
        except Exception:
            pass
        print(
            f"Unpaywall HTTP {e.code} for DOI {doi!r}: {_body_snippet(body)}",
            file=sys.stderr,
        )
        return None
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError) as e:
        print(f"Unpaywall request failed for DOI {doi!r}: {e}", file=sys.stderr)
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


def unpaywall_landing_follow_urls(uw: dict, direct: list[str]) -> list[str]:
    """URLs that may redirect to PDF (same OA entry `url` when not heuristic-matched)."""
    out: list[str] = []
    seen = set(direct)
    for loc in [uw.get("best_oa_location"), *list(uw.get("oa_locations") or [])]:
        if not loc:
            continue
        u = loc.get("url")
        if not u or u in seen:
            continue
        ul = u.lower()
        if ul.endswith(".pdf") or "/pdf" in ul or "pdf?" in ul:
            continue
        seen.add(u)
        out.append(u)
    return out


def semantic_scholar_lookup(doi: str) -> dict | None:
    q = urllib.parse.quote(doi, safe="")
    url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{q}?fields=openAccessPdf,externalIds"
    try:
        data, _ = http_get_urllib(url)
        return json.loads(data.decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read() or b""
        except Exception:
            pass
        print(
            f"Semantic Scholar HTTP {e.code} for DOI {doi!r}: {_body_snippet(body)}",
            file=sys.stderr,
        )
        return None
    except (urllib.error.URLError, json.JSONDecodeError, TimeoutError, OSError) as e:
        print(f"Semantic Scholar request failed for DOI {doi!r}: {e}", file=sys.stderr)
        return None


def iter_semantic_scholar_pdf_urls(ss: dict) -> list[str]:
    out: list[str] = []
    oa = ss.get("openAccessPdf")
    if oa and oa.get("url"):
        out.append(oa["url"])
    return out


def preprint_pdf_urls(ss: dict) -> list[str]:
    """Construct PDF URLs from arXiv and PubMed Central IDs found in Semantic Scholar metadata."""
    ids = ss.get("externalIds") or {}
    out: list[str] = []
    arxiv_id = ids.get("ArXiv")
    if arxiv_id:
        out.append(f"https://arxiv.org/pdf/{arxiv_id}.pdf")
    pmc_id = ids.get("PubMedCentral")
    if pmc_id:
        pid = str(pmc_id).strip().replace("PMC", "")
        ep = europepmc_pdf_urls_for_pmc_id(pid)
        out.extend(ep)
        if not ep:
            out.append(f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pid}/pdf/")
    return out


def openalex_pdf_urls(doi: str) -> list[str]:
    q = urllib.parse.quote(doi, safe="")
    url = f"https://api.openalex.org/works/https://doi.org/{q}"
    try:
        data, _ = http_get_urllib(url)
        msg = json.loads(data.decode("utf-8", errors="replace"))
    except Exception:
        return []
    out: list[str] = []
    for src in [
        msg.get("best_oa_location") or {},
        msg.get("primary_location") or {},
    ]:
        u = src.get("pdf_url")
        if u and u not in out:
            out.append(u)
    u = (msg.get("open_access") or {}).get("oa_url")
    if u and u not in out:
        out.append(u)
    for loc in msg.get("locations") or []:
        u = loc.get("pdf_url")
        if u and u not in out:
            out.append(u)
    return out


def core_pdf_urls(doi: str) -> list[str]:
    q = urllib.parse.quote(f'doi:"{doi}"', safe="")
    url = f"https://api.core.ac.uk/v3/search/works?q={q}&limit=1"
    xh: dict[str, str] = {}
    ck = os.environ.get("AI4RESEARCH_CORE_API_KEY", "").strip()
    if ck:
        xh["Authorization"] = f"Bearer {ck}"
    try:
        data, _ = http_get_urllib(url, extra_headers=xh or None)
        msg = json.loads(data.decode("utf-8", errors="replace"))
    except Exception:
        return []
    out: list[str] = []
    for result in (msg.get("results") or [])[:1]:
        u = result.get("downloadUrl")
        if u and u not in out:
            out.append(u)
    return out


def _europepmc_parse_fulltext_pdfs(r0: dict) -> list[str]:
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


def europepmc_pdf_urls(doi: str) -> list[str]:
    q = urllib.parse.quote(doi, safe="")
    url = f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:{q}&resultType=core&format=json"
    try:
        data, _ = http_get_urllib(url)
        results = json.loads(data.decode("utf-8", errors="replace"))["resultList"].get(
            "result"
        ) or []
        if not results:
            return []
        return _europepmc_parse_fulltext_pdfs(results[0])
    except Exception:
        return []


def europepmc_pdf_urls_for_pmc_id(pmc_numeric: str) -> list[str]:
    """Concrete PDF URLs via Europe PMC metadata (NIHMS-named paths), not directory stubs."""
    pid = pmc_numeric.strip().replace("PMC", "")
    if not pid.isdigit():
        return []
    q = urllib.parse.quote(f"EXT_ID:PMC{pid}", safe="")
    url = (
        "https://www.ebi.ac.uk/europepmc/webservices/rest/search?"
        f"query={q}&resultType=core&format=json"
    )
    try:
        data, _ = http_get_urllib(url)
        results = json.loads(data.decode("utf-8", errors="replace"))["resultList"].get(
            "result"
        ) or []
        if not results:
            return []
        return _europepmc_parse_fulltext_pdfs(results[0])
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
    """Prefer citation_pdf_url meta and <link type=application/pdf>; also catches
    /doi/pdf/ publisher links; only accepts same-registrable-domain hrefs for generic .pdf links."""
    text = body.decode("utf-8", errors="replace")
    meta_urls: list[str] = []
    for pat in (
        r'citation_pdf_url"\s+content="([^"]+)"',
        r"citation_pdf_url'\s+content='([^']+)'",
        r'<meta\s+name="citation_pdf_url"\s+content="([^"]+)"',
        # <link rel="alternate" type="application/pdf" href="...">
        r'<link[^>]+type=["\']application/pdf["\'][^>]+href=["\']([^"\']+)["\']',
        r'<link[^>]+href=["\']([^"\']+)["\'][^>]+type=["\']application/pdf["\']',
    ):
        for m in re.finditer(pat, text, re.I):
            meta_urls.append(m.group(1))

    base_dom = _reg_domain(urllib.parse.urlparse(base_url).netloc)
    href_urls: list[str] = []

    # Same-domain .pdf hrefs
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

    # Publisher /doi/pdf/, /doi/epdf/, /doi/pdfplus/ patterns (Taylor & Francis, Oxford, Wiley, etc.)
    for m in re.finditer(r'href="([^"]*?/doi/(?:pdf|epdf|pdfplus)/[^"]*)"', text, re.I):
        u = m.group(1)
        if "javascript" in u.lower():
            continue
        abs_u = _resolve_url(u, base_url)
        if not abs_u.startswith("http"):
            continue
        if abs_u not in href_urls:
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


def _curl_cffi_fetch_pdf(url: str, referer: str) -> bytes | None:
    if os.environ.get("AI4RESEARCH_USE_CURL_CFFI", "").strip().lower() not in (
        "1",
        "true",
        "yes",
    ):
        return None
    try:
        from curl_cffi import requests as creq
    except ImportError:
        return None
    try:
        r = creq.get(
            url,
            impersonate="chrome",
            headers={
                "User-Agent": USER_AGENT,
                "Referer": referer,
                "Accept": "application/pdf,*/*",
            },
            timeout=120,
        )
        body = getattr(r, "content", None) or b""
        if r.status_code == 200 and len(body) > 400 and body[:4] == b"%PDF":
            return body
    except Exception:
        pass
    return None


def _playwright_request_pdf(url: str, referer: str) -> bytes | None:
    if os.environ.get("AI4RESEARCH_PLAYWRIGHT", "").strip().lower() not in (
        "1",
        "true",
        "yes",
    ):
        return None
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]
    except ImportError:
        print(
            "AI4RESEARCH_PLAYWRIGHT=1 requires: pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        return None
    hdr = {
        "User-Agent": USER_AGENT,
        "Referer": referer,
        "Accept": "application/pdf,*/*",
    }
    try:
        with sync_playwright() as p:
            ctx = p.request.new_context(extra_http_headers=hdr)
            resp = ctx.get(url, timeout=120_000)
            if getattr(resp, "ok", resp.status == 200):
                body = resp.body()
                if len(body) > 400 and body[:4] == b"%PDF":
                    return body
    except Exception:
        pass
    return None


def fetch_pdf_bytes(
    url: str,
    referer: str | None = None,
    doi_landing: str | None = None,
) -> bytes | None:
    """GET URL with redirects; succeed when body begins with %PDF."""
    ref = doi_landing or referer or referer_for_url(url)
    backoff = _RETRYABLE_STATUS | {403}

    for attempt in range(_MAX_RETRIES):
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/pdf,*/*",
                "Referer": ref,
            },
            method="GET",
        )
        try:
            with _urlopen_with_cookies(req, 120) as resp:
                data = resp.read()
            if len(data) > 400 and data[:4] == b"%PDF":
                return data
        except urllib.error.HTTPError as e:
            try:
                e.read()
            except Exception:
                pass
            if (
                getattr(e, "code", None) in backoff
                and attempt < _MAX_RETRIES - 1
            ):
                time.sleep((2**attempt) * 0.35 + random.random() * 0.22)
                continue
            break
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt < _MAX_RETRIES - 1:
                time.sleep((2**attempt) * 0.25 + random.random() * 0.15)
                continue
            break

    c = curl_fetch(url, referer=ref)
    if c and len(c) > 400 and c[:4] == b"%PDF":
        return c
    cf = _curl_cffi_fetch_pdf(url, ref)
    if cf:
        return cf
    return _playwright_request_pdf(url, ref)


def try_urls(
    urls: list[str],
    *,
    doi_landing: str | None = None,
) -> tuple[bytes | None, str | None]:
    for u in urls:
        data = fetch_pdf_bytes(u, doi_landing=doi_landing)
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
        c = curl_fetch(landing, referer="https://doi.org/")
        if c:
            return c, landing
        return None, f"failed: {landing}"


def download_for_doi(doi: str) -> tuple[bool, bytes, str]:
    landing = f"https://doi.org/{urllib.parse.quote(doi, safe='')}"
    uw = unpaywall_lookup(doi)
    if uw:
        ulist = iter_unpaywall_pdf_urls(uw)
        data, src = try_urls(ulist, doi_landing=landing)
        if data:
            return True, data, f"unpaywall: {src}"
        for u in unpaywall_landing_follow_urls(uw, ulist):
            got = fetch_pdf_bytes(u, doi_landing=landing)
            if got:
                return True, got, f"unpaywall-follow: {u}"

    ss = semantic_scholar_lookup(doi)
    if ss:
        sslist = iter_semantic_scholar_pdf_urls(ss)
        data, src = try_urls(sslist, doi_landing=landing)
        if data:
            return True, data, f"semanticscholar: {src}"

    oalist = openalex_pdf_urls(doi)
    data, src = try_urls(oalist, doi_landing=landing)
    if data:
        return True, data, f"openalex: {src}"

    xlist = crossref_pdf_urls(doi)
    data, src = try_urls(xlist, doi_landing=landing)
    if data:
        return True, data, f"crossref: {src}"

    emlist = europepmc_pdf_urls(doi)
    data, src = try_urls(emlist, doi_landing=landing)
    if data:
        return True, data, f"europepmc: {src}"

    clist = core_pdf_urls(doi)
    data, src = try_urls(clist, doi_landing=landing)
    if data:
        return True, data, f"core: {src}"

    if ss:
        plist = preprint_pdf_urls(ss)
        data, src = try_urls(plist, doi_landing=landing)
        if data:
            return True, data, f"preprint: {src}"

    result = fetch_landing_html(doi)
    if result[0] is None:
        return False, b"", str(result[1])
    html_bytes, final = result

    if html_bytes[:4] == b"%PDF":
        return True, html_bytes, f"doi redirect PDF: {final}"

    for candidate in extract_pdf_urls_from_html(html_bytes, final):
        data = fetch_pdf_bytes(candidate, doi_landing=landing)
        if data:
            return True, data, f"html: {candidate}"
        time.sleep(0.2)

    extra = ""
    if uw:
        extra = f" is_oa={uw.get('is_oa')} title={uw.get('title', '')[:60]!r}"
    return False, b"", f"no PDF found{extra}"


def _parse_cli(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download PDFs cited in chatbots/*.md, or fetch one DOI.",
    )
    p.add_argument(
        "--doi",
        metavar="DOI",
        help="Resolve and download one DOI to --out (default: pdfs/single/<slug>.pdf)",
    )
    p.add_argument(
        "--out",
        type=Path,
        help="Output path when using --doi (default pdfs/single/<slug>.pdf)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="With --doi: resolve only; print result, do not write",
    )
    return p.parse_args(argv if argv is not None else sys.argv[1:])


def main(argv: list[str] | None = None) -> None:
    args = _parse_cli(argv)

    if args.doi:
        doi = args.doi.strip()
        PDFS.mkdir(parents=True, exist_ok=True)
        ok, data, msg = download_for_doi(doi)
        if args.dry_run:
            print(
                f"dry-run {doi!r}: ok={ok} bytes={len(data) if ok else 0} detail={msg}"
            )
            return
        dest = (
            Path(args.out)
            if args.out
            else (PDFS / "single" / (slug_from_doi(doi) + ".pdf"))
        )
        dest.parent.mkdir(parents=True, exist_ok=True)
        if ok and data:
            dest.write_bytes(data)
            print(f"OK {doi} -> {dest} ({msg})")
            return
        print(f"FAIL {doi}: {msg}", file=sys.stderr)
        raise SystemExit(1)

    mapping = [
        ("methods_consultant_psychology.md", "methods_consultant_psychology"),
        ("methods_consultant_econometrics.md", "methods_consultant_econometrics"),
        ("methods_consultant_epidemiology.md", "methods_consultant_epidemiology"),
        ("methods_consultant.md", "methods_consultant"),
    ]

    PDFS.mkdir(parents=True, exist_ok=True)
    summary: list[tuple[str, str, str, str]] = []

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
                summary.append((folder, doi, "cached", "-"))
                continue

            ok, data, msg = download_for_doi(doi)

            if ok and data:
                dest.write_bytes(data)
                print(f"  OK: {doi} -> {fn} ({msg})")
                summary.append((folder, doi, "ok", msg))
            else:
                print(f"  FAIL: {doi} ({msg})")
                summary.append((folder, doi, "fail", msg))

            time.sleep(0.4)

    fail_log = PDFS / "_download_summary.tsv"
    hdr = "folder\tdoi\tstatus\tdetail"
    body_lines = ["\t".join(x) for x in summary]
    fail_log.write_text(hdr + "\n" + "\n".join(body_lines) + ("\n" if body_lines else ""), encoding="utf-8")
    print(f"\nWrote {fail_log}")


if __name__ == "__main__":
    main()
