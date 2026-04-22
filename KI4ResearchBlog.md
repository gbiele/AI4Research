# AI in Research: Moving Beyond the Default

*A practical guide to harnessing LLMs seriously — from custom instructions to agentic systems*

---

## The Future Is Already Here

Consider this prompt, given to an AI assistant with access to the web and code execution:

> - Download HBSC data and extract well-being, life satisfaction, and self-efficacy measures for 15-year-olds; compute a composite score per country.
> - Download the PISA 2022 student file from Zenodo; build a composite from reading, mathematics, and science; compute European country averages.
> - Plot a scatterplot of HBSC composite (x) vs. PISA composite (y); label all Nordic countries; highlight Norway.
> - Use R; save the script, figure, and all data to specified folders.[^1]

Here is the figure that came out:

![PISA 2022 vs. HBSC well-being composite by European country](figures/pisa_hbsc_composite_scatter.png)

Not bad for a single short prompt. The pipeline ran end to end — web scraping, data wrangling, composite scoring across two large international datasets, and a labelled scatterplot — with no manual coding. The AI searched the web, downloaded files, wrote and executed R code, read error messages, and corrected itself until the script ran cleanly.

That said, the result is not perfect.  In a more complete workflow, the prompt would include explicit instructions on how to construct composite scores (e.g., z-score each variable before averaging), what axis labels to use, and what the figure should communicate. The prompt would also specify what to do with missing data and how to handle countries that appear in one dataset but not the other.

This is the general pattern with agentic AI: the output scales with the quality of the instructions. A short prompt produces a plausible first draft. A well-specified prompt — written by someone who knows what a good analysis looks like — produces something close to a finished product.

This is not a demo. This is what current agentic AI systems can do. The question is no longer whether AI will change how we do research, but how to use it in ways that are actually reliable.

---

## Why LLMs Are Tricky for Researchers

Large language models (LLMs) are extraordinarily powerful — but their architecture creates two problems that matter especially in scientific contexts.

### Regression to the Mode

LLMs are trained to predict the next most-likely token (word fragment) given everything that came before. This makes them excellent at generating fluent, coherent text. But it also means they pull toward the *mode* of their training data. Ask an LLM to summarise evidence on a contested topic and it will often produce a smooth, confident synthesis that papers over genuine scientific disagreement. Ask it to generate a novel hypothesis and it will tend toward ideas that are already well-represented in the literature.

For researchers, regression to the mode is a subtle trap: the output *sounds* authoritative while being epistemically conservative. 

### Hallucination

Because LLMs are trained to produce plausible continuations rather than factually grounded ones, they sometimes generate content that is fluent but false. The canonical problem is fabricated citations — papers that do not exist, authors who did not write them, DOIs that resolve to unrelated content. But hallucination extends to statistics, dates, methodology descriptions, and any claim that requires retrieving a specific fact from memory rather than reasoning from the prompt.

For researchers, hallucination is not merely embarrassing — it is a validity threat. A results section drafted by an LLM that invents numbers, or a literature review that cites phantom papers, can compromise research integrity. This explains why many researchers are hesitant using LLMs. However, there are ways to make using LLMs safe and reduce risk for hallucinations.

---

## A Framework for Responsible Use

These two problems suggest a practical framework with four levers:

1. **Give the model specific, expert instructions** so it behaves like a domain specialist rather than a generalist assistant.
2. **Fill the context window with curated documents and domain knowledge** so the model reasons from evidence rather than from model-memory.
3. **Extend context retrieval dynamically** using semantic search over a larger document library (RAG).
4. **Automate or facilitate checking of outputs** so errors are caught before they propagate.

The rest of this post works through each lever in turn, from the simplest intervention (custom instructions) to the most powerful (agentic systems with programmatic verification).

---

## Data Privacy: What Not to Upload

Before working through the levers, one ground rule: be careful about what you paste or upload into an LLM.

**Raw research data should not be uploaded.** This applies to participant-level data, health records, administrative data, and any dataset with privacy implications — regardless of pseudonymisation. The clear exception is data you downloaded from a public source or would share openly anyway (the PISA and HBSC files in the example above fall into this category).

Pre-publication results are a different matter. Sharing a table of means or a draft results section carries no privacy risk, and using an LLM to help draft or check such text is generally fine.

What does require care is training data. Standard consumer-facing LLM services may use your conversations to improve their models unless you opt out or use a version that excludes this. For tasks involving sensitive materials — confidential grant applications, internal project documents, unpublished methods — use a service that contractually excludes your prompts from training data. Enterprise versions of Microsoft Copilot (Microsoft 365) and the API-based tiers of Claude, ChatGPT, and Gemini typically provide this guarantee; verify the terms for the specific service before proceeding.

In all cases, follow FHI's guidelines on AI use. If you are uncertain whether a particular use is permitted, check with your data manager or privacy officer before proceeding.

---

## Lever 1: Custom Instructions

Every major LLM interface now allows you to set a persistent system prompt — instructions that apply to every conversation. This is the easiest and highest-leverage thing a researcher can do.

### What good custom instructions look like

Here is a set of custom instructions designed for researchers:

```
- Say "I don't know" rather than guessing; never fabricate citations or statistics
- Use web search and tools to verify facts before stating them
- Cite primary literature; prefer peer-reviewed sources over summaries
- Push back on flawed reasoning or unsupported claims
- Think step by step and check your reasoning before answering
- Read papers critically: flag when conclusions outrun the evidence, when study designs cannot support causal claims, or when limitations are understated
- Be concise; do not pad responses or ask unnecessary follow-up questions
- Do not suggest next steps or offer further help unless asked
```

These instructions address hallucination directly ("never fabricate citations"), push back against regression-to-the-mode style overconfidence ("push back on flawed reasoning"), and reduce noise ("do not pad responses"). A model following these instructions behaves quite differently from the default.

### Setting custom instructions in Microsoft Copilot

Microsoft Copilot (available at [copilot.microsoft.com](https://copilot.microsoft.com) and integrated into Microsoft 365) supports custom instructions through its settings.

**Step-by-step:**

1. Open Microsoft Copilot.
2. Click the **profile icon** in the top-right corner and select **Settings** (or the gear icon).
3. Look for **Personalization** or **Custom instructions** in the sidebar.
4. In the text field, paste your custom instructions. You can include multiple bullet points; the model will apply them persistently.
5. Save your settings. From this point on, every new Copilot conversation will start with these instructions already in effect.

> **Tip:** Custom instructions in Copilot apply across sessions but not across all Microsoft 365 entry points (e.g., Copilot in Word may not inherit browser-based instructions). Check the specific integration you are using.

---

## Lever 2: Custom Chatbots and Agents

Custom instructions give you a better-behaved generalist assistant. Custom chatbots go further: they embed domain expertise, methodological guardrails, and a curated knowledge base into a reusable agent you can share with colleagues or return to across projects.

### What a custom chatbot specification looks like

A chatbot specification has four parts:

- **Name and description:** a short, specific label that makes the chatbot's purpose immediately clear — both for your own reference and for colleagues you share it with (e.g., "Methods Consultant — Epidemiology" / "Causal inference and study design advisor for population health research")
- **Instructions:** what the chatbot should and should not do, how it should reason, what it should ask before answering
- **Knowledge:** files you upload to the chatbot — PDFs of methods papers, textbooks, reporting checklists, your institution's guidelines — that are stored with the agent and drawn on when generating responses. When you ask a question, the chatbot searches this uploaded material and uses the relevant passages to inform its answer, rather than relying solely on what the underlying model learned during training.
- **Tools:** web search, code execution, file access (depending on platform)

Here is the specification for the *Methods Consultant — Epidemiology* chatbot as a concrete example:

**Instructions (excerpt):**
```
- You are an expert in epidemiological methods and causal inference for population health research.
- Ask clarifying questions about the research question, target population, exposure, outcome,
  time horizon, and available data before recommending methods.
- Causal inference is central: always ask whether the goal is descriptive, predictive, or causal,
  and adjust recommendations accordingly.
- For causal questions, require the researcher to draw or describe a DAG before recommending
  adjustment sets; explain the difference between confounders, mediators, and colliders.
- Apply the counterfactual framework (potential outcomes) and discuss identifiability assumptions
  explicitly: exchangeability, positivity, consistency, no interference.
- Push back on adjustment strategies that open backdoor paths or condition on colliders.
- Never fabricate citations; cite real epidemiology methods papers or textbooks when relevant.
```

**Knowledge base (excerpt):**

These are the actual documents (PDFs or better markdown files, see below) uploaded to the chatbot. When you ask a question, the agent uses the relevant passages in its response — so it can cite and reason from the specific content of these papers rather than from the model's general training:

- Hernán & Robins (2006). Estimating causal effects from epidemiological data.
- Greenland, Pearl & Robins (1999). Causal diagrams for epidemiologic research.
- Hernán & Robins (2016). Using big data to emulate a target trial.
- STROBE and RECORD reporting checklists

The effect of these instructions is substantial. Instead of offering a generic answer to "should I adjust for X in my regression?", this chatbot will ask about your DAG, identify whether X is a confounder, mediator, or collider, and explain the consequences of conditioning on each — just as a good methodologist would.

The same principle applies to the other chatbots in this collection:

| Chatbot | Purpose |
|---|---|
| Methods Consultant | General statistics and study design for social/health sciences |
| Methods Consultant — Psychology | Psychology-specific, with replication crisis and open science norms |
| Methods Consultant — Epidemiology | Causal inference, DAGs, epidemiological study designs |
| Methods Consultant — Econometrics | IV, DiD, RDD, program evaluation designs |
| Grant Reviewer | Critical review against funder criteria (RCN, ERC, NIH) |
| Copy Editor — English | Academic editing, APA style, tracked changes |
| Copy Editor — Enkelt Språk | Plain-language rewriting in Norwegian |

### Setting up custom chatbots and agents in Microsoft Copilot

Microsoft Copilot supports custom configurations (called **Copilot Agents** in Copilot Studio) that embed persistent instructions, knowledge, and tools. In practice, most research use cases call for a **custom chatbot**: a named assistant with fixed instructions and an uploaded knowledge base that you interact with conversationally. This becomes a true **agent** when you additionally grant it the ability to take actions — for example, generating and editing Word or PowerPoint files, sending emails, or querying SharePoint. For a methods consultant or copy editor, the chatbot form is usually sufficient. The agent form becomes useful when you want the AI to produce a draft document directly, not just advise on its content.

**Step-by-step (Copilot Studio / Microsoft 365 Copilot):**

1. Go to [copilotstudio.microsoft.com](https://copilotstudio.microsoft.com) and sign in.
2. Click **Create** → **New agent**.
3. Give the agent a **name** and a short **description** (e.g., "Methods Consultant — Epidemiology").
4. In the **Instructions** field, paste the instructions from the chatbot specification. Be specific: the more precise the instructions, the more reliably the agent will behave.
5. Under **Knowledge**, click **Add knowledge** and upload relevant documents — PDFs of methods papers, reporting checklists, your project's analysis plan.
6. Configure **Actions** (tools) as needed: web search, file access, or code interpreter if available in your tenant.
7. Click **Publish** to make the agent available in Teams, Copilot, or via a shared link.

> **Tip:** Copilot agents can be scoped to your organisation, shared with a team, or kept private. For a methods consultant that references your institution's statistical guidelines, keeping it within your organisation makes sense.

---

## Improving Output Quality with High-Quality Documents

The instructions above reference a knowledge base of methods papers, textbooks, and reporting checklists. The quality of these documents matters, because LLMs reason from what is in the context window — and that means the quality of the *text the platform extracts from your uploads* determines how well the chatbot can reason from them.

When you upload a PDF to Copilot Studio, NotebookLM, or a similar platform, the platform automatically extracts the text behind the scenes before indexing it. This extraction is often poor: equations become garbled, tables lose their structure, and multi-column layouts produce jumbled, out-of-order text. The chatbot then reasons from this degraded version — not from the original paper as you read it. This is the "garbage in, garbage out" problem for document-grounded chatbots.

A better approach is to upload a clean **Markdown** version of the document instead of the raw PDF. Markdown is plain text with simple formatting that platforms can index accurately, without any lossy extraction step. If you upload a well-structured Markdown file, the chatbot reads essentially the same content you do.

[`pdfParser`](https://github.com/gbiele/pdfParser) is an R package that converts PDFs to semantic Markdown using [Docling](https://github.com/DS4SD/docling) for layout analysis and body text, and Google Gemini for table and figure extraction. The result preserves the semantic content of a paper — tables with correct cell alignment, figure captions, and section hierarchy — in a format that chatbot platforms can index cleanly. Conveniently, `pdfParser` includes a `pdf_dir_to_markdown_docling()` function that processes all PDFs in a folder and writes the resulting Markdown files to disk in one step, making it straightforward to prepare an entire knowledge base at once.

For knowledge-base documents you return to repeatedly — core methods papers, reporting checklists, textbooks — converting them once with `pdfParser` and uploading the Markdown versions is worth the extra step.

---

## Lever 3: Retrieval Augmented Generation (RAG)

Custom chatbots with a fixed knowledge base are powerful, but they require you to anticipate which documents you need. Retrieval Augmented Generation (RAG) systems go further: they maintain a searchable knowledge base and retrieve relevant passages *at query time* using semantic search.

In a RAG system, your question is converted to a vector embedding and matched against embeddings of document chunks. The most relevant passages are pulled into the context window before the model generates its answer. The model is effectively asked: "Given these specific passages, answer this question." This constrains the model to reason from the provided text rather than from its training data — directly addressing the hallucination problem for literature-based questions.

### Practical RAG tools for researchers

**[NotebookLM](https://notebooklm.google.com/)** (Google) is the most accessible RAG tool for researchers — and it is free. You upload your sources — PDFs, Markdown, Google Docs, web pages — and NotebookLM creates a searchable notebook grounded in those sources. Answers include citations to the specific passage used, so you can verify them directly. It is a general-purpose tool, however, and lacks the research-specific features that make systematic literature work faster.

Use it for:
- Literature synthesis from a curated set of papers
- Drafting introductions or discussion sections grounded in your reference list
- Answering specific questions about uploaded papers

**[Elicit](https://elicit.com/)** is purpose-built for research. It searches a large academic database and extracts structured information (outcomes, population, methods, effect sizes) from papers (though often only abstracts are used) in a way that is directly useful for systematic reviews and evidence synthesis — capabilities NotebookLM does not offer. The trade-off is cost and setup effort: to use Elicit effectively, you need one of the better paid plans (around 4,500 NOK/year), and the three or cheaper Paid accounts analyse only a small number of full texts per month. Even with a more expensive paid plan, to get full-text reasoning, you likely will need to upload the many PDFs yourself. That extra step is worth it for systematic review work, but it does mean Elicit rewards deliberate setup rather than casual use.

**In both cases:** the quality of your uploaded documents matters. PDFs converted with `pdfParser` before upload will give the RAG system more accurate, structured text to index.

---

## Lever 4: AI-Assisted Text Generation with Programmatic Verification

One of the most practically valuable uses of LLMs in research is generating text from statistical results — drafting results sections, municipality-specific reports, or subgroup summaries from tabular output. The challenge is hallucination of numbers: an LLM given a results table may misread a value, transpose digits, or confabulate a statistic.

At the Norwegian Institute of Public Health (FHI), this problem is concrete: FHI produces reports for hundreds of municipalities, schools, and population subgroups. Writing subgroup-specific text by hand does not scale; LLM-generated text is fast but can introduce numerical errors.

[`tblscribe`](https://github.com/gbiele/tblscribe) is an R package that addresses this directly. It:

1. Formats a data frame or statistical table into a prompt-safe representation
2. Sends it to an LLM (OpenAI, Anthropic, or Google) with a prompt template
3. **Verifies the generated text** by checking that every numeric token in the prose matches the source table within specified tolerances — deterministically, without re-querying the model

```r
library(tblscribe)

df <- data.frame(
  group = c("Boys", "Girls"),
  prevalence = c(0.31, 0.44),
  ci_lower = c(0.27, 0.39),
  ci_upper = c(0.35, 0.49)
)

result <- llm_describe(
  "Describe the prevalence of the outcome by sex, including confidence intervals.",
  data = df,
  decimals = 2,
  verify = "numbers"   # check all numbers in the prose against the table
)
```

If the model writes "boys showed a prevalence of 0.32" when the table says 0.31, `tblscribe` flags the mismatch. With `verify_max_attempts > 0`, it will automatically retry with corrective feedback. With `on_fail = "prepend"`, it prefixes a warning banner to the returned text so downstream users know the verification failed.

This is the pattern that makes AI-assisted text generation safe at scale: the LLM generates the prose, deterministic code verifies the numbers, and humans review flagged outputs. Neither step alone is sufficient; together they are.

---

## Agentic Systems: The Full Picture

Agentic systems bring everything together. They combine:

- **Tool use:** web search, code execution, file reading and writing, API calls
- **Iterative self-correction:** run code, read the error, rewrite the code, run again
- **Long-horizon planning:** decompose a complex task into steps, execute them in sequence

The PISA/HBSC example at the top of this post is a real agentic workflow. The prompt provided the download URLs directly; the agent then:

1. Downloaded the HBSC data and metadata files from the provided URLs
2. Downloaded the PISA 2022 student file from Zenodo
3. Wrote R code to extract the relevant variables for 15-year-olds (WHO-5 well-being index, life satisfaction, two self-efficacy measures) and compute a composite score per country
4. Ran the code, read the error messages, and fixed the code
5. Built a composite score from PISA reading, mathematics, and science, and computed country averages for Europe
6. Wrote and executed the plotting code — a labelled scatterplot with Nordic countries highlighted and Norway specifically called out
7. Saved the figure, the script, and all data to the specified locations

Current tools that support this kind of workflow include:

- **Claude Code / Claude Workspace** (Anthropic) — strong code generation and execution, excellent for R and Python data pipelines
- **Cursor** (cursor.com) — code editor with an AI agent that writes, runs, and debugs code
- **GitHub Copilot Workspace** — similar within GitHub's ecosystem
- **Microsoft Copilot + Code Interpreter** — available in some Microsoft 365 configurations

### What agentic systems are best at

- Automating repetitive data pipelines (download → clean → analyse → plot)
- Writing boilerplate code for standard analyses
- Translating a verbal description of an analysis into executable code
- Iterating on code until it runs correctly

### What they can do with the right context

With good instructions and relevant background documents in the context window, the picture is more nuanced than "the agent writes code and you check it." If you describe the analysis goal and upload the relevant methods literature, an agentic system can:

- Review model specifications and flag potential mismatches with the stated research question
- Propose alternative or better-suited analytical approaches, drawing on uploaded methods papers
- Catch common errors — wrong reference category, model estimated on the wrong subset, outcome coded in the wrong direction — when the analysis plan is explicit enough to check against

The key is that the agent reasons from what is in the context. Provide the analysis plan, the relevant methods references, and a description of the data structure, and the agent has enough to act as a critical reviewer of its own output.

### What they are still not good at

Even with rich context, agentic systems fall short in several ways that matter for research:

- **Generating novel scientific ideas** — regression to the mode means output tends toward what is already common in the literature
- **Quick sanity checks from background knowledge** — an experienced researcher notices immediately when a result is implausible given domain knowledge; an agent without that knowledge loaded into the context cannot
- **Deriving statistical hypotheses from research hypotheses** — translating a theoretical prediction into a precise, testable statistical claim requires the kind of conceptual reasoning that LLMs handle poorly without very explicit scaffolding
- **Judging ecological validity** — whether a measure actually captures the construct of interest, or whether a study sample is representative of the target population, requires substantive expertise the agent does not have unless it is explicitly provided
- **Noticing what is missing** — agents work with what is in front of them; they are poor at flagging that a critical confound was not measured, that a sensitivity analysis is absent, or that the discussion ignores a rival explanation

This last point deserves emphasis. LLMs multiply the competences you already have — they do not give you entirely new ones. An agentic system that produces a structural equation model will produce correct-looking code, but only a researcher who understands SEM can judge whether the model is appropriate for the data and question. The value of agentic systems scales with your ability to evaluate their output.

---

## Putting It Together: A Practical Workflow

| Task | Tool | Verification | Watch out for |
|---|---|---|---|
| Statistical consultation | Methods Consultant chatbot (with custom instructions + knowledge base) | Your domain expertise | May miss field-specific norms not covered in the knowledge base |
| Literature synthesis | NotebookLM or Elicit | Citation checking against sources | Retrieval is imperfect; not all relevant passages will surface |
| PDF ingestion for knowledge bases | `pdfParser` (R) | Compare Markdown output against original | Tables and figures still need manual checking after conversion |
| Generating results text | `tblscribe` (R) | Programmatic number verification | Numbers are verified; framing and interpretation still need expert review |
| Data pipelines and analysis code | Claude Code / Cursor | Run the code; inspect outputs | Code may run correctly but implement the wrong analysis |
| Grant application review | Grant Reviewer chatbot | Your knowledge of funder criteria | Feedback reflects the knowledge base; keep it current with funder priorities |
| Manuscript editing | Copy Editor chatbot | Read the diff carefully | Style changes can inadvertently alter meaning |

The common thread: instructions shape model behaviour, context windows filled with reliable information ground model reasoning, and verification — whether programmatic or expert — catches what slips through.

---

## Getting Started

Everything in this post — writing precise custom instructions, specifying a chatbot, drafting a detailed analysis prompt — takes real effort to build. But here is the shortcut: use LLMs to help build all of it. Ask a model to draft custom instructions for your field, then iterate. Describe the kind of expert you want a chatbot to behave like and ask the model to write the instruction set. Paste a rough analysis prompt and ask the model to identify what is underspecified. The first version does not need to be perfect — it needs to be good enough to start, and you refine it as you learn where the model fails.

One practical note on tool selection: model capabilities change quickly. When choosing between services, ask a model with web search to look up recent benchmarks rather than relying on what it knows from training — the landscape moves faster than any training dataset.

---

## Conclusion

The PISA/HBSC analysis at the top of this post came from a single short prompt. A more complete version — one that specifies how to construct composite scores, how to handle missing data, what axis labels to use — would take ten minutes to write and produce something close to a finished product. That is not a demo condition; it is the current state.

The framework in this post is not about being cautious with AI. It is about being smart with it: specific instructions, curated knowledge, and systematic verification are what separate a research tool from a plausible-sounding liability. LLMs multiply the competences you already have — the output scales with the quality of what you bring to the prompt.

---

*The chatbot specifications referenced in this post are available in the `chatbots/` directory. The `pdfParser` and `tblscribe` R packages are available on GitHub.*

---

[^1]: Full prompt: "Download hsbc data here: https://data-browser.hbsc.org/wp-content/uploads/csvs/data.csv and meta data here https://data-browser.hbsc.org/wp-content/uploads/csvs/metadata.csv. Then extract data for 15 year olds — who-5-well-being-index, life satisfaction, self efficacy (2 measures) — from the data and calculate a composite score for each country. Next go to https://zenodo.org/records/13382904 and download the PISA 2022 student file. Build a composite score from reading, mathematics and science, and compute the average for each European country. Finally, plot a scatterplot with the composite HBSC score on the x-axis and the composite PISA score on the y-axis. Label all the Nordic countries and highlight Norway and save the figure as figures/scatter_pisa_hsbc.png. Use R to do this. Document all steps in a script, which you save as scripts/pisa_hbsc_scatter. Save all data in the data folder."
