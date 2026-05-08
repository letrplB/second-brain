---
name: connect
description: Wire a note into the graph. Add inline wikilinks both directions, update MOC membership. The primitive that turns isolated notes into a graph.
version: "0.1"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Bash, mcp__qmd__query, mcp__qmd__multi_get
argument-hint: "[note-path] [--bulk <glob>] — note to connect. --bulk operates on a glob (e.g., --bulk notes/claims/*.md)."
---

# /connect

**Intent.** Take a note that exists but is poorly connected, and integrate it into the graph. Add inline `[[wikilinks]]` in its body where genuine connections exist; add inverse links from connected notes back to it; update MOC membership both ways.

## When to invoke

- Just after `/extract` (composed by `/learn`)
- When you realise an old claim should link to newly-added work (use `--bulk` with a date-filtered glob)
- When `/audit` flags a note as orphaned

## Behaviour

### Forward pass — add links *from* this note to others

1. Read the target note: title, description, frontmatter, body.
2. **Discover candidates** via two channels in parallel:
   - **Semantic search:** `qmd query` with `intent` = the note's description, types `lex` and `vec`. Return top ~30 candidates.
   - **Frontmatter walk:** read the note's `tags`, `methods`, `topics`, `supports`, `contradicts` arrays. Walk those notes; collect their tags + neighbours (one hop).
3. **Filter candidates.** A connection is genuine when:
   - The target note's claim *requires*, *follows from*, *qualifies*, *contradicts*, or *exemplifies* the candidate
   - Or: the candidate is a method used in the target's evidence chain
   - Or: the candidate is a paper sourcing the target
   - **Not genuine:** "they share a topic", "they sound related", "they were co-extracted from the same source" (sibling-only)
4. **Add inline `[[wikilinks]]`** in the body where genuine connections fit, with surrounding prose explaining the relationship. Avoid bare-link lists — context phrases prefix every link.
5. **Update structured frontmatter** where the connection has a typed slot: `supports`, `contradicts`, `methods` arrays gain entries.

### Backward pass — add links *from* others to this note

6. For each connected note from step 4: read it. Decide whether the inverse link belongs in *its* body. If yes, add it (with surrounding prose).
7. Update structured frontmatter on the connected notes if applicable (e.g. paper notes get the new claim in their `claims:` list — though `/extract` may have done this already).

### MOC pass

8. Identify which `_<topic>.md` MOCs this note belongs to (by tags + semantic match against MOC descriptions).
9. For each: add the note to the MOC's `## Core claims` (or equivalent) section with a context phrase.
10. In the target note's footer, add or update `## Topics` listing the MOCs.

## When to spawn a subagent

- If step 2 returns >50 candidates after dedup, spawn a subagent to filter (it gets the descriptions + frontmatter for all candidates, returns only the ~10 genuine ones).
- If `--bulk` is invoked over >20 notes, spawn one subagent per ~10 notes, run in parallel, then a final lead-pass to deduplicate redundant link additions.
- Otherwise inline.

## Failure modes to resist

- **Forced engagement.** Adding links because "we should connect this somewhere". Empty `## Core claims` in a MOC is fine if the note doesn't fit. Do not force it.
- **Sibling clusters.** Notes co-extracted from the same source are *thematically related* but rarely *epistemically connected*. Don't link siblings unless one supports/contradicts/qualifies the other.
- **MOC sprawl.** If a note fits 5+ MOCs, you've miscategorised it or the MOCs are too fine-grained. Pick the 1–3 closest fits.
- **Stale links.** Before adding `[[wikilink]]`, check the file exists. Dangling links are a separate signal (handled by `/audit`).

## Output

- The target note's body has new inline `[[wikilinks]]` with surrounding prose
- The target note's frontmatter has updated `supports`/`contradicts`/`methods` arrays
- The target note has a `## Topics` footer
- Connected notes have inverse links where appropriate
- Relevant MOCs have the note listed in `## Core claims`
- Summary printed: "Connected N forward, M backward, K MOCs touched."

## Cross-references

- Editorial: `reference/empirical-grounding/inline links carry richer relationship data than metadata fields.md`, `propositional link semantics transform wiki links from associative to reasoned.md`, `forced engagement produces weak connections.md`
- Tools used: `qmd` MCP (`mcp__qmd__query`, `mcp__qmd__multi_get`)
