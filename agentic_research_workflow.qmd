---
title: "Agentic workflow for auto-generated research reports"
subtitle: "From background literature and register data to a reproducible report"
format:
  html:
    embed-resources: true
    toc: true
    toc-depth: 2
---

## Overview

This workflow shows how **agents** and **humans** collaborate on a reproducible report from:

- **Background literature PDFs** — methods corpus under `pdfs/`, indexed in [`chatbots/sources.md`](chatbots/sources.md)
- **Chatbot instructions / skills** — personas in [`chatbots/`](chatbots/) (and optional Cursor `SKILL.md` wrappers)
- **Register data + metadata** — tabular data with a full dictionary (see also [`KI4Forsking.qmd`](KI4Forsking.qmd))

**Governance:** in every phase the **agent** produces a **plan**, the **human** **approves** or requests revision, and only then the **agent** **implements** synthesis, code, or narrative.

---

## Skill types

Three types of skills appear throughout:

| Symbol | Type | What it means |
|--------|------|---------------|
| `[C]` | **Custom chatbot** | An existing persona file in `chatbots/` |
| `[T]` | **Tool** | A platform capability (code execution, file access, web search, etc.) |
| `[!]` | **Missing** | Not yet in `chatbots/` — worth adding if needed |

---

## Chatbots vs agent skills

| Layer | What it is |
|-------|------------|
| **`chatbots/*.md`** | Canonical personas — methods general + epidemiology / econometrics / psychology, copy editors, grant reviewer. Use as Claude custom instructions, Cursor rules, or load as context. |
| **Cursor `.cursor/skills/.../SKILL.md`** | Procedures loaded by description. Point to or copy from a `chatbots/` file. |

**Persona files:** `methods_consultant.md`, `methods_consultant_epidemiology.md`, `methods_consultant_econometrics.md`, `methods_consultant_psychology.md`, `copy_editor_english.md`, `copy_editor_enkelt_sprak.md`, `grant_reviewer.md`, `literature_synthesizer.md`, `code_writer.md`, `sap_prereg_drafter.md`. **`sources.md`** lists PDFs; it is not a persona.

---

## Skills by phase

| Phase | Primary skills | Secondary / optional |
|-------|---------------|----------------------|
| ① Literature | `[T]` PDF Reader · Web Search · `[C]` [`literature_synthesizer.md`](chatbots/literature_synthesizer.md) | `[C]` Domain consultant to critique claims |
| ② Estimand | `[C]` Methods Consultant (domain) · `[T]` Metadata Explorer | `[C]` Grant Reviewer for significance framing |
| ③ Analysis plan | `[C]` Methods Consultant (domain) · `[T]` DAG Builder · Statistical Computing | `[C]` [`sap_prereg_drafter.md`](chatbots/sap_prereg_drafter.md) |
| ④ Implementation | `[T]` Code Interpreter (R/Python) · Data Query · `[C]` [`code_writer.md`](chatbots/code_writer.md) | `[C]` Domain consultant to verify model vs estimand |
| ⑤ Results | `[C]` Methods Consultant (domain) · `[T]` Statistical Output Parser | `[C]` Copy Editor EN |
| ⑥ Discussion | `[C]` Copy Editor EN · Grant Reviewer · `[T]` PDF Reader · Citation Formatter | `[C]` Copy Editor Enkelt Språk (lay summary) |

---

## Workflow diagram

Node labels include the key skills used. Colors: **blue** = input, **green** = agent, **yellow** = human gate.

```{mermaid}
%%| fig-width: 10
%%| fig-height: 18
flowchart TB
  subgraph inputs [Inputs]
    PDFs[PDFs — background literature]
    Skills[Skills and chatbot instructions]
    Reg[Register data and complete metadata]
  end

  subgraph phase1 ["① Literature Review"]
    A1P["AGENT — plan\nDefine retrieval strategy and synthesis outline\n· · · · · · · · · · · · · · · · · · · · · · · ·\nT: PDF Reader · Web Search  C: Literature Synthesizer"]:::agent
    H1A["HUMAN — approve or request revision"]:::human
    A1I["AGENT — implement\nStructured synthesis with traceable citations\n· · · · · · · · · · · · · · · · · · · · · · · ·\nT: PDF Reader  C: Literature Synthesizer"]:::agent
    A1P --> H1A --> A1I
    H1A -.->|revise| A1P
  end

  subgraph phase2 ["② Research Goal & Estimand"]
    A2P["AGENT — plan\nPropose estimand · population · exposure\noutcome · time horizon · assumptions\n· · · · · · · · · · · · · · · · · · · · · · · ·\nC: Methods Consultant (domain)  T: Metadata Explorer"]:::agent
    H2A["HUMAN — approve or request revision"]:::human
    A2I["AGENT — implement\nEstimand text for methods section\n· · · · · · · · · · · · · · · · · · · · · · · ·\nC: Methods Consultant (domain) · Grant Reviewer"]:::agent
    A2P --> H2A --> A2I
    H2A -.->|revise| A2P
  end

  subgraph phase3 ["③ Analysis Plan"]
    A3P["AGENT — plan\nStudy design · DAG · adjustment set\nSE strategy · multiplicity · power analysis\n· · · · · · · · · · · · · · · · · · · · · · · ·\nC: Methods Consultant (domain)  T: DAG Builder · Stat Computing"]:::agent
    H3A["HUMAN — approve or request revision"]:::human
    A3I["AGENT — implement\nLocked analysis specification / pre-registration draft\n· · · · · · · · · · · · · · · · · · · · · · · ·\nC: Methods Consultant (domain) · SAP / Prereg drafter"]:::agent
    A3P --> H3A --> A3I
    H3A -.->|revise| A3P
  end

  subgraph phase4 ["④ Analysis Implementation"]
    A4P["AGENT — plan\nRepo layout · reproducibility checks · pipeline steps\n· · · · · · · · · · · · · · · · · · · · · · · ·\nT: Code Interpreter (R/Python) · Data Query  C: Code Writer"]:::agent
    H4A["HUMAN — approve or request revision"]:::human
    A4I["AGENT — implement\nFully scripted pipeline: raw data → tables & figures\n· · · · · · · · · · · · · · · · · · · · · · · ·\nT: Code Interpreter (R/Python) · Data Query  C: Code Writer"]:::agent
    A4P --> H4A --> A4I
    H4A -.->|revise| A4P
  end

  subgraph phase5 ["⑤ Results Description"]
    A5P["AGENT — plan\nTables and figures tied to estimands\nEffect sizes · CIs · exploratory vs confirmatory\n· · · · · · · · · · · · · · · · · · · · · · · ·\nC: Methods Consultant (domain)  T: Stat Output Parser"]:::agent
    H5A["HUMAN — approve or request revision"]:::human
    A5I["AGENT — implement\nNeutral results narrative with CIs and effect sizes\n· · · · · · · · · · · · · · · · · · · · · · · ·\nC: Methods Consultant (domain) · Copy Editor EN"]:::agent
    A5P --> H5A --> A5I
    H5A -.->|revise| A5P
  end

  subgraph phase6 ["⑥ Discussion"]
    A6P["AGENT — plan\nLimitations · links to prior literature\nRobustness checks · future directions\n· · · · · · · · · · · · · · · · · · · · · · · ·\nC: Grant Reviewer  T: PDF Reader"]:::agent
    H6A["HUMAN — approve or request revision"]:::human
    A6I["AGENT — implement\nDiscussion draft + optional lay summary\n· · · · · · · · · · · · · · · · · · · · · · · ·\nC: Copy Editor EN · Copy Editor Enkelt Språk · Grant Reviewer\nT: Citation Formatter"]:::agent
    A6P --> H6A --> A6I
    H6A -.->|revise| A6P
  end

  HFinal["HUMAN — final sign-off\nEthics · data access · submission-ready text"]:::human

  PDFs --> A1P
  Skills --> A1P
  Reg --> A1P

  Skills -.->|inform| A2P
  Skills -.->|inform| A3P
  Skills -.->|inform| A4P
  Reg -.->|inform| A2P
  Reg -.->|inform| A3P
  Reg -.->|inform| A4P
  PDFs -.->|inform| A6P

  A1I --> A2P
  A2I --> A3P
  A3I --> A4P
  A4I --> A5P
  A5I --> A6P
  A6I --> HFinal

  classDef agent fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d
  classDef human fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#713f12
```

---

## Skills inventory

### Existing custom chatbots `[C]`

| Chatbot | File | Phases |
|---------|------|--------|
| Methods Consultant — General | `chatbots/methods_consultant.md` | ②③⑤ |
| Methods Consultant — Epidemiology | `chatbots/methods_consultant_epidemiology.md` | ②③⑤ |
| Methods Consultant — Econometrics | `chatbots/methods_consultant_econometrics.md` | ②③⑤ |
| Methods Consultant — Psychology | `chatbots/methods_consultant_psychology.md` | ②③⑤ |
| Copy Editor — English | `chatbots/copy_editor_english.md` | ⑤⑥ |
| Copy Editor — Enkelt Språk | `chatbots/copy_editor_enkelt_sprak.md` | ⑥ (lay summary) |
| Grant Reviewer | `chatbots/grant_reviewer.md` | ②⑥ |
| Literature Synthesizer | `chatbots/literature_synthesizer.md` | ① |
| Code Writer | `chatbots/code_writer.md` | ④ |
| SAP / Prereg Drafter | `chatbots/sap_prereg_drafter.md` | ③ |

### Required platform tools `[T]`

| Tool | Role | Phases |
|------|------|--------|
| PDF Reader | Extract text from academic PDFs | ①⑥ |
| Web Search | Verify DOIs, find supplementary references | ① |
| Metadata Explorer | Parse register data dictionaries and codebooks | ② |
| DAG Builder | Construct and validate DAGs (e.g. dagitty API or R `dagitty`) | ③ |
| Statistical Computing | Run power simulations and prototype models (R/Python) | ③ |
| Code Interpreter (R/Python) | Write and execute the full reproducible pipeline | ④ |
| Data Query | Read and subset register data (CSV / parquet / SQL) | ④ |
| Statistical Output Parser | Extract estimates, SEs, CIs, p-values from model output | ⑤ |
| Citation Formatter | Format references to target journal style | ⑥ |

### Optional additions `[!]`

Further personas (e.g. register QA-only, ethics checklist) are not required for the core workflow above; add new files under `chatbots/` if a project needs them.

---

## Stage notes

### ① Literature review

Use **`literature_synthesizer.md`** together with grounded retrieval from `pdfs/` (see `chatbots/sources.md`). The **PDF Reader** tool is essential; **Web Search** helps verify DOIs. Human review remains important; the synthesizer enforces traceable, per-paper extraction with source pointers.

### ② Estimand

Load the **domain Methods Consultant** (`_epidemiology`, `_econometrics`, or `_psychology`). The **Metadata Explorer** tool must parse the register data dictionary before the estimand is locked — the agent needs to confirm that exposure, outcome, and covariates exist with acceptable missingness and correct units. **Grant Reviewer** can optionally sharpen the significance framing.

### ③ Analysis plan

The **domain Methods Consultant** drives study design, adjustment set, SE estimator, and multiplicity strategy. The **DAG Builder** tool renders and validates the causal diagram (d-separation checks via dagitty). **Statistical Computing** supports a-priori power simulations with the smallest effect of interest specified. **`sap_prereg_drafter.md`** turns the approved plan into registration-ready SAP or OSF-style text.

### ④ Implementation

The **Code Interpreter** runs a fully reproducible pipeline from raw register data to tables and figures without manual steps. The **Data Query** tool provides access to data files. **`code_writer.md`** encodes project conventions—folder layout, naming, checkpoints, session logging—so implementation stays auditable and consistent with the approved plan.

### ⑤ Results description

The **Statistical Output Parser** extracts estimates and intervals from model output. The **domain Methods Consultant** ensures correct reporting: effect sizes alongside p-values, no causal language where it is not warranted, explicit labelling of exploratory vs. confirmatory findings. **Copy Editor EN** polishes language without altering scientific content.

### ⑥ Discussion

The agent re-reads background PDFs (**PDF Reader**) to contextualise findings. **Copy Editor EN** handles academic language; **Copy Editor Enkelt Språk** can produce a Norwegian lay summary. **Grant Reviewer** frames impact and generalisability for a funder or broad audience. **Citation Formatter** matches the target journal style. The **human** owns ethics, data access, and final sign-off.
