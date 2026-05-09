---
name: audit
description: Quality gate. Schema + link + cold-read on a note (or --vault). Returns a report with ranked issues and suggested fixes.
version: "0.1"
user-invocable: true
allowed-tools: Read, Glob, Bash, mcp__qmd__query
argument-hint: "[note-path] [--vault] [--mode=quick|full] — note to audit. --vault sweeps everything. --mode quick skips cold-read."
---

# /audit

**Intent.** Check a note's quality against the contract. Three orthogonal checks: schema (frontmatter), links (no danglers), cold-read (can the model predict the body from title+description+frontmatter alone?).

## Modes

| Mode | Schema | Links | Cold-read | Topology |
|---|---|---|---|---|
| `--mode=quick` | yes | yes | no | no |
| `--mode=full` (default for single note) | yes | yes | yes | no |
| `--vault` | yes | yes | sample | yes |

## Behaviour

### Single-note audit (default)

1. **Schema check.** Run `tools/schema-check.py <note>`. Validates frontmatter against the active preset's contract. Reports missing required fields, invalid enum values, descriptions that are too short / too long / merely paraphrase the title.
2. **Link check.** Run `tools/link-check.sh <note>`. Reports `[[wikilinks]]` whose target file doesn't exist (danglers) plus a list of context-prose-less inline links (bare `[[a]]. [[b]].` with no surrounding sentence).
3. **Cold-read.** Read only the title + frontmatter + description. *Predict* what the body should say (3 bullets). Then read the body. Compare. Report:
   - **Strong:** body matches prediction in spirit
   - **Weak:** body adds material the description didn't trail-blaze (description should layer heuristic → mechanism → implication; if the body has a key idea the description omits, the description is too short)
   - **Wrong:** body contradicts the description
4. **Synthesis.** Print a short report:
   ```
   /audit notes/claims/X.md
     schema: 2 issues
       - description is paraphrase of title (not adding info)
       - confidence missing
     links: 1 dangler
       - [[some-claim-that-doesnt-exist]]
     cold-read: weak
       - body introduces "scaling regime" not flagged in description
     fix priority:
       1. rewrite description to trail mechanism (high)
       2. set confidence (medium)
       3. resolve or remove [[some-claim-that-doesnt-exist]] (medium)
   ```

### Vault audit (`--vault`)

1. Same schema + link checks across every `notes/**.md`.
2. Run `../walk/tools/topology.py orphans` and `topology.py moc-coverage` for structural health.
3. Sample cold-read on ~10 claims (random + recent) — full cold-read on every note is too expensive.
4. **Run `tools/health-metrics.py`** to print the four-family health dashboard (coherence, connectivity, boundary precision, confidence distribution). This is the per-session eval signal from the claim-fact-gradient framing — print it as the `## Health Metrics` section of the report.
5. Synthesise: total counts, top-N worst-offenders, suggested order of fix.

## When to spawn a subagent

- `--vault` always. Fresh-context inspector reads the entire vault and produces the report. Lead does not need that in context.
- Single-note: never. Inline.

## Tools

- `tools/schema-check.py` — frontmatter validator (against `vault.yaml` + preset contract)
- `tools/link-check.sh` — dangling-link finder (bash + grep + find)
- `tools/topology.py` (from `/walk` skill) — invoke for `--vault` mode's structural checks

## Failure modes to resist

- **Auto-fix without asking.** `/audit` *reports*; it does not modify files. Use `/anneal` for fix application.
- **Excessive nitpicking.** A note with 3 minor issues and a clear claim is fine. Don't drown signal in style notes.
- **Cold-read against a stale description.** If the description has been edited since the body was written, the cold-read result is misleading. The fix is "update description to match body" not "rewrite body to match description".

## Output

- A printed report (single-note: ~10 lines; --vault: longer with sectioned rollup)
- Exit code: 0 if clean, 1 if any issue found (so the verb composes with shell scripting)
- No file modifications

## Cross-references

- Tools: `tools/schema-check.py`, `tools/link-check.sh`, `tools/health-metrics.py`, `../walk/tools/topology.py`
- Editorial: `reference/empirical-grounding/distinctiveness scoring treats description quality as measurable.md`, `descriptions are retrieval filters not summaries.md`
