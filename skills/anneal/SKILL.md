---
name: anneal
description: Methodology coach pass. Walks scoped notes, flags drift, suggests fixes, applies on confirmation. Explicit only — never proactive.
version: "0.1"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Bash, mcp__qmd__query
argument-hint: "[--scope=note <path>|topic <topic-slug>|vault] [--commit] — scope of the pass. --commit makes a git commit at the end."
---

# /anneal

**Intent.** A patient pass that lowers the disorder of the graph without adding new content. Reviews recent work against the methodology core; flags drift; offers fixes; applies on user confirmation.

The metallurgical metaphor is the right one: you are not creating; you are bringing existing structure to a more ordered, lower-energy state. Slow heat, careful cooling. **Never proactive — only invoked.**

## Scopes

| Scope | What's in scope |
|---|---|
| `--scope=note <path>` | one note |
| `--scope=topic <topic-slug>` | one topic-MOC + every claim it owns |
| `--scope=vault` | the whole vault (sampling for very large vaults) |

If no `--scope`, default to "all notes modified in the last 7 days".

## Behaviour

### Phase 1 — gather

1. Resolve scope into a concrete list of note paths.
2. Read each note: title, frontmatter, body.

### Phase 2 — assess

For each note, check against the methodology core:

- **Title is a prose proposition.** Not a topic label. (`reference/empirical-grounding/title as claim enables traversal as reasoning.md`)
- **Description adds information.** Not a paraphrase of the title. Layers heuristic → mechanism → implication. (`reference/empirical-grounding/good descriptions layer heuristic then mechanism then implication.md`)
- **Frontmatter contract complete.** All required fields per type. Enums valid. Source link present for claims.
- **Body length 150–400 words** (claims/memories). Outside the band → flag for split or expand.
- **Inline wikilinks have surrounding prose.** Bare `[[a]] [[b]]` = drift.
- **MOC membership.** Every claim/memory should appear in at least one `_<topic>.md`. (`reference/empirical-grounding/MOCs are attention management devices not just organizational tools.md`)
- **No dangling links.** Every `[[wikilink]]` resolves to an existing file.

For `--scope=topic` add MOC-specific checks:
- The MOC's `## Core claims` lists ≥3 claims (else: too narrow, consider absorbing into parent).
- The MOC's `## Core claims` lists ≤30 claims (else: too broad, consider splitting).
- Bidirectionality: every claim in `## Core claims` lists this MOC in its `## Topics` footer, and vice versa.

For `--scope=vault` add structural checks (via `walk/tools/topology.py`):
- Orphan count + ratio
- MOC coverage gaps
- High-centrality claims that lack a description (those are read most; description quality matters most)

### Phase 3 — report

Print a structured report:

```
/anneal --scope=<scope>

Findings:
  drift: 7 notes
    notes/claims/X.md
      - description paraphrases title
      - body 612 words (split candidate)
    notes/claims/Y.md
      - 3 dangling links
    ...

  topology (vault scope only):
    orphans: 4
    moc-uncovered: 2
    high-centrality without strong description: 1

  fix priorities (top 5):
    1. rewrite description for [[X]] (high)
    2. resolve dangling [[gone-claim]] in [[Y]] (high)
    3. add [[Z]] to a topic MOC (medium)
    4. ...
```

### Phase 4 — fix (interactive)

For each finding, offer to apply a fix:

- "Rewrite description for [[X]]?" → if yes, propose new description, show before/after, apply on confirm.
- "Resolve dangling [[gone-claim]]?" → offer alternatives: remove the link, redirect to a similar existing slug, create a stub.
- "Add [[Z]] to a topic MOC?" → propose which MOC, apply on confirm.

User can `apply all`, `apply only high-priority`, or `skip`.

### Phase 5 — commit (optional)

If `--commit` was passed, make a git commit summarising the changes:

```bash
git add -A
git commit -m "anneal: <scope> — <N> fixes applied"
```

## When to spawn a subagent

- `--scope=vault`: spawn one subagent per topic-MOC for the assess phase. Lead aggregates the reports and does the interactive fix phase.
- Other scopes: inline.

## Failure modes to resist

- **Becoming proactive.** `/anneal` only runs when invoked. Do not nag the user during other skills' work; flag issues only inside their own report (`/audit` does that).
- **Auto-applying without confirmation.** Every fix gets the user's nod first.
- **Adding content.** Anneal lowers disorder. If a note is missing a section the user ought to write, flag it; don't fabricate the section.
- **Touching git without `--commit`.** No silent commits. The flag is the consent.

## Output

- A printed report
- File modifications applied with user confirmation
- Optional git commit

## Cross-references

- Composes: `audit` (quality checks), `walk` (topology for vault scope)
- Editorial: `reference/empirical-grounding/maintenance operations are more universal than creative pipelines because structural health is domain-invariant.md`, `maintenance-patterns.md`, `backward maintenance asks what would be different if written today.md`
