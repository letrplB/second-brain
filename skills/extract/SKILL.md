---
name: extract
description: Mechanical extraction of atomic claims from a source file. Inline, fast, no choreography. The primitive that /learn composes with /connect and /audit.
version: "0.1"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Bash
argument-hint: "[source-path] — file to extract from. Defaults to most recent in inbox/ if omitted."
---

# /extract

**Intent.** Mechanical claim extraction. Read a source, write atomic claim notes. Nothing else.

## What this verb does NOT do

- Does not connect (no inline `[[wikilinks]]` to other notes added in this step — that's `/connect`)
- Does not audit (no quality check — that's `/audit`)
- Does not update MOCs (that's `/connect`)
- Does not move the source out of `inbox/` (that's `/learn` if invoked, else manual)

It writes claim notes. That is all.

## Behaviour

1. **Resolve source.** If an argument is given, treat it as the source path. If no argument, list `inbox/` files by mtime and process the most recent (or ask).
2. **Read the source.** Whole file, in one read, inline.
3. **Identify atomic claims.** A claim is:
   - A proposition that is true or false (not a description, not a list of topics)
   - Specific enough that it could in principle be wrong
   - Sourced to *this* text (don't extract claims the text merely cites)
   - Narrow enough to fit one note (not a multi-claim summary)
4. **Calibrate count to source density.** **Hard floor: zero.** **Soft ceiling: model judgement.** Reference numbers:
   - Tweet / single short post: 0–3
   - Blog essay (≤2K words): 3–8
   - Long essay / chapter: 8–15
   - Paper: 10–25 (rare to exceed; over-extraction is the known failure mode)
   - When in doubt, *fewer* is better — duplicates and restatements should collapse to one claim.
5. **Write paper note.** If no `notes/papers/<source-slug>.md` exists, create one. Frontmatter per `reference/templates/paper.md`. Body: ≤200 words on what the source argues + why you're processing it.
6. **Write claim notes.** For each identified claim:
   - Filename: `notes/claims/<kebab-case-prose-proposition>.md`. Title = filename. Prose proposition, not topic label.
   - Frontmatter per `reference/templates/claim.md`. **Mandatory:** `description`, `type: claim`, `confidence`, `source: "[[<paper-slug>]]"`, `evidence_type`, `created: <today>`, `tags`.
   - Body: 150–400 words. Show *why* the claim holds in this source (mechanism, evidence, scope conditions). Do NOT add `[[wikilinks]]` to other claims yet — that's connect's job.
7. **Update paper's `claims:` list.** Append the new claim filenames to the paper note's `claims:` frontmatter array.
8. **Print summary.** "Extracted N claims into notes/claims/. Paper note: <slug>. Source untouched in <source-path>."

## When to spawn a subagent

Almost never. `/extract` is mechanical and bounded by source length. Inline.

The one case: if the source is genuinely paper-class (long, dense, multi-section) AND the user expects ≥10 claims, optionally spawn one subagent per major section to extract that section's claims in parallel. This is rare. Default is single-pass inline.

## Failure modes to resist

- **Over-extraction.** If you find yourself writing claim N while the marginal claim is *clearly* a paraphrase of claim 3, stop. Reduce the list.
- **Topic-label titles.** "cognitive surrender" is not a claim. "cognitive surrender is path-dependent" is a claim. Always check that the filename reads as a complete prose proposition.
- **Borrowed claims.** If the source cites someone else's work, that claim belongs to the cited paper, not this source. Note it as a reference, not as an extracted claim.
- **Assumed connections.** Don't link to other claims yet. The graph state may be stale; `/connect` reads it fresh.

## Output

- N new files in `notes/claims/`
- 1 new file in `notes/papers/` (if not already present)
- Paper note's `claims:` updated
- Summary printed

## Cross-references in this plugin

- Frontmatter: `reference/templates/{claim,paper}.md`
- Editorial: `reference/methodology.md` (atom contract section)
- On atom design: `reference/empirical-grounding/claims must be specific enough to be wrong.md`, `title as claim enables traversal as reasoning.md`, `elaborative encoding is the quality gate for new notes.md`
