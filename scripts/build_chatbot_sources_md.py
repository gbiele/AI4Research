#!/usr/bin/env python3
"""Build chatbots/sources.md from DOI bullets in methods consultant chatbots."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHATBOTS = ROOT / "chatbots"
PDFS = ROOT / "pdfs"
OUT = CHATBOTS / "sources.md"

# Match download_chatbot_pdfs.py
DOI_RE = re.compile(r"https?://doi\.org/(10\.\d{4,9}/[^\s\]]+)", re.I)
MIN_PDF_BYTES = 1000

SOURCES: list[tuple[str, str, str | None]] = [
    ("methods_consultant_epidemiology.md", "Epidemiology", "methods_consultant_epidemiology"),
    ("methods_consultant_econometrics.md", "Econometrics", "methods_consultant_econometrics"),
    ("methods_consultant_psychology.md", "Psychology", "methods_consultant_psychology"),
    ("methods_consultant.md", "General", "methods_consultant"),
]


def slug_from_doi(doi: str) -> str:
    return doi.replace("/", "_").replace("(", "").replace(")", "")


def normalize_doi(raw: str) -> str:
    return raw.rstrip(").,;")


def escape_cell(s: str) -> str:
    return s.replace("|", "\\|").replace("\n", " ")


def rows_for_file(md_name: str, pdf_folder: str | None) -> list[tuple[str, str, bool, str]]:
    path = CHATBOTS / md_name
    text = path.read_text(encoding="utf-8")
    out: list[tuple[str, str, bool, str]] = []
    seen_set: set[str] = set()

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        if "doi.org" not in stripped.lower():
            continue
        m = DOI_RE.search(stripped)
        if not m:
            continue
        doi = normalize_doi(m.group(1))
        if doi in seen_set:
            continue
        seen_set.add(doi)

        prefix = stripped[: m.start()].strip()
        if prefix.startswith("- "):
            citation = prefix[2:].strip()
        else:
            citation = prefix

        if pdf_folder:
            pdf_path = PDFS / pdf_folder / f"{slug_from_doi(doi)}.pdf"
            ok = pdf_path.is_file() and pdf_path.stat().st_size > MIN_PDF_BYTES
            filepath = pdf_path.relative_to(ROOT).as_posix() if ok else ""
        else:
            ok = False
            filepath = ""

        out.append((citation, doi, ok, filepath))
    return out


def main() -> None:
    all_rows: list[tuple[str, str, str, bool, str]] = []
    for md_name, domain, folder in SOURCES:
        for citation, doi, ok, fp in rows_for_file(md_name, folder):
            all_rows.append((domain, citation, doi, ok, fp))

    lines = [
        "# Chatbot sources",
        "",
        "Journal references with DOIs from methods consultant chatbots. Regenerate with `python scripts/build_chatbot_sources_md.py`.",
        "",
        "| method domain | citation | doi | is downloaded | filepath |",
        "| --- | --- | --- | --- | --- |",
    ]
    for domain, citation, doi, ok, fp in all_rows:
        dl = "true" if ok else "false"
        fp_cell = fp if fp else "—"
        lines.append(
            f"| {escape_cell(domain)} | {escape_cell(citation)} | {escape_cell(doi)} | {dl} | {escape_cell(fp_cell)} |"
        )

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(all_rows)} rows)")


if __name__ == "__main__":
    main()
