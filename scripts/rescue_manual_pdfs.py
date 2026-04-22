#!/usr/bin/env python3
"""
Fetch PDFs from known open URLs when Unpaywall / publishers block scripted downloads.

Also copies an existing PDF into every chatbot subfolder that lists the same DOI
(so Epidemiology / Econometrics / Psychology rows in sources.md stay consistent).

Run after editing chatbot DOIs, then optionally re-run download_chatbot_pdfs.py for stragglers:

  python scripts/rescue_manual_pdfs.py
  python scripts/download_chatbot_pdfs.py
  python scripts/build_chatbot_sources_md.py
"""
from __future__ import annotations

import argparse
import shutil
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import download_chatbot_pdfs as dl  # noqa: E402

MIN_BYTES = 1000

# DOI -> one or more direct PDF URLs (tried in order).
MANUAL_PDF_URLS: dict[str, list[str]] = {
    "10.1177/2515245917745629": [
        "https://www2.psych.ubc.ca/~schaller/528Readings/Rohrer2018.pdf",
    ],
    "10.1093/esr/jcp006": [
        "https://ora.ox.ac.uk/objects/uuid:77a4f8f2-6b50-4a24-a05f-8d350dca8fff/files/mfba752c9ac58b1681b19382a578fb588",
    ],
    "10.1080/00031305.2016.1154108": [
        "https://www.burtthompson.net/uploads/9/6/8/4/9684389/wasserstein-2016__asa_p-value_statement.pdf",
    ],
    "10.1080/00031305.2019.1583913": [
        "https://sites.pitt.edu/~bertsch/Moving%20to%20a%20World%20Beyond%20p%200%2005.pdf",
    ],
    "10.1093/ije/dyw341": [
        "https://eprints.whiterose.ac.uk/id/eprint/109517/7/ije-sap-final.pdf",
    ],
    "10.1097/00001648-199901000-00008": [
        "https://cpb-us-w2.wpmucdn.com/u.osu.edu/dist/7/36891/files/2020/01/Greenland-Pearl-and-Robins-1999.pdf",
    ],
    "10.1093/aje/kwi188": [
        "https://files-profile.medicine.yale.edu/documents/5c89b92a-4fae-4a34-aa5c-c23b2aaded4e",
    ],
    "10.2307/2951620": [
        "https://business.baylor.edu/scott_cunningham/teaching/imbens--angrist---late-1994.pdf",
    ],
}

CHATBOT_PDF_MAP: list[tuple[str, str]] = [
    ("methods_consultant_epidemiology.md", "methods_consultant_epidemiology"),
    ("methods_consultant_econometrics.md", "methods_consultant_econometrics"),
    ("methods_consultant_psychology.md", "methods_consultant_psychology"),
    ("methods_consultant.md", "methods_consultant"),
]


def doi_to_folders() -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for md_name, folder in CHATBOT_PDF_MAP:
        text = (dl.CHATBOTS / md_name).read_text(encoding="utf-8")
        for doi in dl.find_dois_in_md(text):
            if folder not in out[doi]:
                out[doi].append(folder)
    return dict(out)


def is_valid_pdf(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > MIN_BYTES and path.read_bytes()[:4] == b"%PDF"


def fetch_first_pdf(urls: list[str]) -> bytes | None:
    for url in urls:
        data, src = dl.try_urls([url])
        if data and data[:4] == b"%PDF" and len(data) > MIN_BYTES:
            return data
    return None


def write_to_folders(doi: str, folders: list[str], data: bytes) -> None:
    slug = dl.slug_from_doi(doi) + ".pdf"
    for folder in folders:
        dest = dl.PDFS / folder / slug
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        print(f"  wrote {dest.relative_to(dl.ROOT)} ({len(data)} bytes)")


def rescue_manual() -> None:
    mapping = doi_to_folders()
    for doi, urls in MANUAL_PDF_URLS.items():
        folders = mapping.get(doi)
        if not folders:
            print(f"skip {doi} (not listed in any chatbot md)")
            continue
        slug = dl.slug_from_doi(doi) + ".pdf"
        if all(is_valid_pdf(dl.PDFS / f / slug) for f in folders):
            print(f"skip {doi} (already in all folders)")
            continue
        print(f"fetch {doi} …")
        data = fetch_first_pdf(urls)
        if not data:
            print(f"  FAIL: could not download PDF from mirrors")
            continue
        write_to_folders(doi, folders, data)


def sync_shared_dois() -> None:
    """Copy PDF from any folder that has it to other folders listing the same DOI."""
    mapping = doi_to_folders()
    for doi, folders in mapping.items():
        slug = dl.slug_from_doi(doi) + ".pdf"
        paths = [dl.PDFS / f / slug for f in folders]
        source = next((p for p in paths if is_valid_pdf(p)), None)
        if not source:
            continue
        for p in paths:
            if not is_valid_pdf(p):
                p.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, p)
                print(f"  sync {source.relative_to(dl.ROOT)} -> {p.relative_to(dl.ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manual PDF mirrors + cross-folder sync for chatbot DOIs.")
    parser.add_argument(
        "--sync-only",
        action="store_true",
        help="Only copy PDFs across folders; do not hit mirror URLs.",
    )
    args = parser.parse_args()

    dl.PDFS.mkdir(parents=True, exist_ok=True)
    if not args.sync_only:
        rescue_manual()
    print("\n=== sync shared DOIs across folders ===")
    sync_shared_dois()


if __name__ == "__main__":
    main()
