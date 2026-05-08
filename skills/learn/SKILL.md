---
name: learn
description: Full ingestion of a source. Composes /extract → /connect → /audit end-to-end. The verb you use when you want a source to land properly in the graph.
version: "0.1"
user-invocable: true
allowed-tools: Read, Write, Edit, Glob, Bash, Task, mcp__qmd__query, mcp__qmd__multi_get
argument-hint: "<source-path> [--deep] — source file. --deep parallelises per-claim with one subagent per claim."
---

# /learn

**Intent.** End-to-end ingestion. The user-facing composite for "learn this source properly."

## What it does (default mode)

Sequential, all inline:

1. **`/extract <source>`.** Atomic claim notes written to `notes/claims/`. Paper note created in `notes/papers/`.
2. **For each new claim, `/connect <claim>`.** Sequential pass. Forward + backward links + MOC membership.
3. **For each new claim, `/audit <claim>` (quick mode).** Schema + link check. Skip cold-read in this loop.
4. **Move source.** From `inbox/<source>` to `archive/<YYYY-MM-DD>-<source-slug>/<source>`. Untouched copy preserved.
5. **Print summary.** Claims created, links added, MOCs touched, audit issues, archive path.

If extraction returns 0 claims, stop after step 1 and report.

## Deep mode (`--deep`)

For papers and other dense sources where parallelism helps and the model genuinely needs full audit including cold-read.

1. **`/extract <source>`.** Same as above — inline; the lead does extraction.
2. **Spawn one subagent per new claim.** Each subagent does:
   - `/connect <its-claim>` (full forward + backward + MOC)
   - `/audit <its-claim> --mode=full` (schema + link + cold-read)
   Each subagent is fresh-context for its own claim. **One claim, one subagent, end-to-end** — *not* one subagent per phase.
3. **Lead waits for all subagents.** Collects their summaries.
4. **Cross-connect pass (lead, inline).** Walk the new claim set; for each claim, check whether it should link to *another new claim* whose note didn't exist when its sibling's connect ran. Add missed sibling links.
5. **Move source, print summary.**

Subagent count cap: **N (claims) × 1**. Hard cap of 16 concurrent (Task tool platform limit). If extraction returned >16 claims, queue: spawn first 16, wait for all, then spawn next batch.

## When to use which mode

| Source class | Mode |
|---|---|
| Tweet, single-paragraph note | default. Often 0–1 claim; sequential is fine. |
| Blog essay (≤2K words) | default. 3–8 claims; sequential takes < a minute. |
| Long essay / chapter (~3–8K words) | default unless user wants thorough audit. |
| Paper (peer-reviewed, dense) | `--deep` recommended. |
| Anything where the user said "thorough" or "deep" | `--deep`. |

The default is fast on purpose. Don't escalate without reason.

## Behaviour

```
input: <source-path>, [--deep]

read source
extract → claim_set, paper_note

if --deep:
  spawn worker per claim:
    in worker context: read shared graph state, connect + audit own claim, return summary
  wait
  cross-connect pass on claim_set (lead, inline)
else:
  for each claim in claim_set:
    connect (inline)
    audit --quick (inline)

move source to archive/<date>-<slug>/<source>
print summary
```

## Failure modes to resist

- **Defaulting to `--deep`.** Don't. The whole point of the redesign is that default is fast. Only escalate when source density warrants it.
- **Cross-connect omission in deep mode.** Step 4 is essential — without it, sibling claims linked to siblings that didn't yet exist when their connect ran will miss those links.
- **Failing partially and hiding it.** If any subagent fails, surface that to the user clearly. Don't move the source out of inbox if claims weren't all processed.

## Output

- Multiple new files (claims + paper note)
- Source moved to archive
- Summary printed:
  ```
  /learn <source>  [mode: default|deep]
    extracted: N claims, 1 paper note
    connected: X forward links, Y backward links, Z MOCs touched
    audited: A clean, B with issues
    archived: archive/<date>-<slug>/
  ```

## Cross-references

- Composes: `extract`, `connect`, `audit`
- Editorial: `reference/empirical-grounding/every knowledge domain shares a four-phase processing skeleton that diverges only in the process step.md`, `fresh context per task preserves quality better than chaining phases.md`, `continuous small-batch processing eliminates review dread.md`
