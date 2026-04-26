# AI4Research

> **Note:** All content in this repository — chatbot specifications and documentation — was created with AI assistance (primarily Claude and Cursor Composer), reviewed by the author, and adjusted where needed.

This repository collects materials for using AI tools responsibly and effectively in research. It includes two documents and ready-to-use chatbot specifications.

LLMs have two core failure modes that matter for researchers:

- **Regression to the mode** — models are trained to predict likely continuations, so they reproduce the dominant view in the literature, paper over genuine scientific disagreement, and generate output that sounds authoritative while being epistemically conservative.
- **Hallucination** — models sometimes generate fluent but false content: fabricated citations, invented statistics, misattributed findings. Because the output looks plausible, errors are easy to miss.

Both are addressable through three practical levers, in increasing order of effort:

1. **Custom instructions, extended reasoning, and careful prompts** — shapes how the model behaves in every conversation.
2. **Custom chatbots** — purpose-built specialists with domain expertise and methodological guardrails baked in.
3. **Grounding the model in your own documents** — retrieval-augmented systems (e.g. NotebookLM, Elicit) that answer from your papers rather than the model's training memory.

---

## Documents

| File | Description |
|---|---|
| [AI4Research_blog_en.qmd](AI4Research_blog_en.qmd) ([html](https://gbiele.github.io/AI4Research/AI4Research_blog_en.html)) / [AI4Research_blog_no.qmd](AI4Research_blog_no.qmd) ([html](https://gbiele.github.io/AI4Research/AI4Research_blog_no.html)) | Blog post (English / Norwegian): concrete instructions for using AI across the research workflow, covering key failure modes (hallucination, regression to the typical) and how to address them |
| [AI4Research_slides_en.qmd](AI4Research_slides_en.qmd) ([html](https://gbiele.github.io/AI4Research/AI4Research_slides_en.html)) / [AI4Research_slides_no.qmd](AI4Research_slides_no.qmd) ([html](https://gbiele.github.io/AI4Research/AI4Research_slides_no.html)) | Short presentation (English / Norwegian): brief overview of AI tools for researchers without detailed guidance |

Rendered HTML versions of each document are included alongside the source files.

---

## Chatbot specifications (`chatbots/`)

Ready-to-use chatbot specifications for Microsoft Copilot Studio, ChatGPT, Claude, or any platform that supports custom system instructions and uploaded knowledge bases. Each file is a Markdown document with instructions you can paste directly into a custom agent.

| File | Purpose |
|---|---|
| [grant_reviewer.md](chatbots/grant_reviewer.md) | Critical review of grant applications against funder criteria (NFR, ERC, NIH) |
| [literature_synthesizer.md](chatbots/literature_synthesizer.md) | Structured extraction and synthesis from uploaded PDFs with strict traceability |
| [narrative_review.md](chatbots/narrative_review.md) | Critical narrative literature reviews foregrounding contradictions and methodological quality |
| [methods_consultant.md](chatbots/methods_consultant.md) | General statistics and study design for social and health sciences |
| [methods_consultant_epidemiology.md](chatbots/methods_consultant_epidemiology.md) | Causal inference, DAGs, and epidemiological study designs |
| [methods_consultant_psychology.md](chatbots/methods_consultant_psychology.md) | Psychology-specific methods, open science, and the replication crisis |
| [methods_consultant_econometrics.md](chatbots/methods_consultant_econometrics.md) | Causal identification strategies: IV, DiD, RDD, program evaluation |
| [sap_prereg_drafter.md](chatbots/sap_prereg_drafter.md) | Formalises an analysis plan into a structured SAP or OSF pre-registration |
| [data_analyst_r.md](chatbots/data_analyst_r.md) | Interactive step-by-step R coding assistant (data.table, ggplot2, targets) |
| [results_writer.md](chatbots/results_writer.md) | Interactive assistant for drafting and reviewing results sections |
| [copy_editor_english.md](chatbots/copy_editor_english.md) | Academic copy editing for English manuscripts |
| [copy_editor_enkelt_sprak.md](chatbots/copy_editor_enkelt_sprak.md) | Plain-language rewriting in Norwegian (Enkelt Språk) |
| [code_writer.md](chatbots/code_writer.md) | General reproducible coding assistant for R or Python |
| [sources.md](chatbots/sources.md) | Overview of reference documents used across the knowledge bases |
| [NotebookLMCustomInstructions.txt](chatbots/NotebookLMCustomInstructions.txt) | Custom instructions for NotebookLM notebooks |

These specifications were generated with AI assistance and reviewed once. Treat them as starting points: read the instructions, test on a real task, and adjust where they fall short for your field.

---

## Related R packages

Two R packages are referenced throughout but live in separate repositories:

- [`pdfParser`](https://github.com/gbiele/pdfParser) — converts PDFs to semantic Markdown (using Docling + Google Gemini) for clean upload to chatbot knowledge bases
- [`tblscribe`](https://github.com/gbiele/tblscribe) — generates text from statistical tables and programmatically verifies that every number in the output matches the source data
