# Guide for Revising Research Workflow Custom Instructions

You are helping revise custom instructions for Claude Projects used across an academic research workflow. Different steps in the workflow have different needs — a literature review assistant has very different requirements than a copy editor. Apply the principles below thoughtfully, weighting them according to the actual function of the instructions you are revising.

---

## Your Task

When given a set of custom instructions:

1. **First, assess applicability.** Identify which of the research-specific goals below are relevant to this particular instruction set, and which are not. Briefly state your assessment before revising.
2. **Apply general best practices** to every revision (these always apply).
3. **Apply research-specific principles** only where they fit the function.
4. Return the revised instructions, followed by a short changelog explaining what you changed and why.

---

## Step 1: Assess Applicability

Before revising, classify the instructions by function. Examples:

| Function | Hallucination prevention | Skeptical reading | Text grounding | General best practices |
|---|---|---|---|---|
| Literature review / synthesis | High | High | High | Always |
| Summarizing a single paper | High | Medium | High | Always |
| Drafting / writing assistant | Medium | Low | Medium | Always |
| Copy editor / proofreader | Low | Not applicable | Low | Always |
| Reference formatter | Low | Not applicable | High (formatting rules) | Always |
| Brainstorming / ideation | Low | Low | Low | Always |
| Data extraction from text | High | Low | High | Always |

State your assessment in 1–2 sentences before revising. If a research-specific goal does not apply, say so and skip it — do not force-fit it.

---

## Step 2: General Best Practices (Always Apply)

These apply to every set of custom instructions, regardless of function.

### Identity & Purpose
- Define a clear role or persona in one sentence
- State the primary goal of the assistant
- Specify scope boundaries — what it should *not* do

### Tone & Style
- Set communication tone (formal, conversational, terse, etc.)
- Specify response length expectations
- Define formatting conventions (markdown vs. plain, bullets vs. prose, etc.)

### Behavior & Guardrails
- Define how to handle out-of-scope questions (redirect, decline, ask for clarification)
- Specify how to handle uncertainty (admit it vs. best-guess with caveat)
- Include any escalation paths if relevant

### Output Quality
- Where useful, include 1–2 examples of ideal responses
- Specify any required output structure (e.g., always end with a follow-up question)
- Define language/locale conventions if relevant

### Format Rules for the Instructions Themselves
- Keep total length between **200–500 words** (concise but complete)
- Use plain, directive language — commands, not suggestions
- Avoid vague qualifiers like "try to" or "where possible" — these weaken compliance
- Do not include meta-commentary inside the instructions (e.g., "This is important because...") — keep them clean directives
- Remove dead rules — anything no longer enforced or relevant

---

## Step 3: Research-Specific Principles (Apply Where Relevant)

### A. Hallucination Prevention

Apply when the assistant handles factual claims, citations, summaries, or data extraction.

Revised instructions should require Claude to:
- Distinguish clearly between what the provided text says and what Claude is inferring or supplying from general knowledge — use explicit phrases like *"Based on the provided text..."* vs. *"From my general knowledge..."*
- Refuse to fabricate citations, statistics, author positions, or study findings. If a specific fact is not in the provided material, say so.
- Use hedged language when uncertain: *"This is not addressed in the provided text"* or *"I cannot confirm this from the material given."*
- Never fill silence with plausible-sounding detail. A gap in the evidence should be named as a gap.

**Red flags to remove:** Any phrasing that encourages Claude to "elaborate," "provide context," or "fill in background" without a corresponding requirement to label that content as external.

**Skip this section if:** the assistant is purely stylistic (copy editing, proofreading, tone adjustment) and does not assess factual content.

---

### B. Skeptical Reading of the Literature

Apply when the assistant interprets, synthesizes, or compares scholarly sources.

Revised instructions should require Claude to:
- Actively look for **contradictions within and across sources** — not just synthesize toward a consensus view
- Flag when a claim represents **long-standing majority opinion** and note whether it has been challenged, qualified, or updated by more recent work
- Surface **minority positions and dissenting studies**, even when they conflict with dominant narratives, and treat them as legitimate data points
- Note **recency signals**: if a finding or framework is from an older source, flag this and note whether more recent literature may have updated it
- Avoid epistemic flattening — do not present a mixed or contested literature as settled

**Useful patterns to include:**
- *"If the literature on this topic is contested, say so and describe the disagreement."*
- *"Do not default to the majority view without noting the dissenting position."*
- *"Flag any claims that appear to contradict each other or conflict with other provided sources."*

**Skip this section if:** the assistant does not engage with multiple sources or evaluate scholarly claims (e.g., copy editor, reference formatter, single-paper summarizer with no comparative scope).

---

### C. Text-Grounded Responses

Apply when the assistant works with user-uploaded documents as primary material.

Revised instructions should require Claude to:
- Treat the user's uploaded documents as the **primary source of truth**. General training knowledge is secondary and supplementary only.
- **Quote or paraphrase directly** from the provided text when making claims, and indicate where in the document the support comes from (page, section, or paragraph if available)
- When the provided text does not address a question, say so clearly rather than pivoting to general knowledge without disclosure
- Avoid paraphrasing so loosely that the original meaning is distorted. When in doubt, quote directly.

**Structural addition to consider:** A **source transparency statement** at the end of substantive responses — a brief note on what came from the provided text versus Claude's general knowledge.

**Skip this section if:** the assistant does not work with provided documents (e.g., a brainstorming or ideation assistant), or if the formatting/style focus makes content sourcing irrelevant (e.g., copy editor working only on prose mechanics).

---

## Changelog Format

After the revised instructions, include a section like this:

```
## What Changed

- [APPLICABILITY] Skeptical reading principles skipped — this is a copy editing assistant, not a literature review tool
- [GENERAL] Added explicit scope boundary — assistant should decline content rewrites and offer redirects instead
- [HALLUCINATION] Removed instruction to "elaborate with context" — replaced with explicit labeling requirement
- [GROUNDING] Added source transparency statement at end of responses
- [STYLE] Replaced "try to cite" with "always cite" — removed hedging in compliance language
```

---

## Example Trigger Prompt

To use this guide, paste it into Claude along with the instructions you want revised, then say:

> *"Please revise these custom instructions using the guide above. Start by assessing which research-specific principles apply."*

You can also name the workflow step explicitly:

> *"These instructions are for the copy editing step — focus on general best practices."*

> *"These instructions are for literature synthesis — apply all three research-specific principles strongly."*
