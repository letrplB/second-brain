---
name: dream
description: Push synthesis back at the user. Daily mode pulls 3 connections + 1 pattern + 1 question from recent activity. Weekly mode surfaces emerging thesis, contradictions, gaps, and one action. The feedback loop that turns the vault from input-store into thinking-partner.
version: "0.1"
user-invocable: true
allowed-tools: Read, Write, Glob, Bash, mcp__qmd__query, mcp__qmd__multi_get
argument-hint: "[--daily | --weekly] [--scope=<window>] — daily is the default. --scope overrides the time window (e.g. --scope=14d for the last two weeks)."
---

# /dream

**Intent.** Make the vault talk back. Without this verb, a second-brain is "a very organised way to forget things." `/dream` is the feedback loop — synthesis pushed at the user without them having to ask.

The output is **a brief in `inbox/`**, not a graph node. Briefs are prompts to think, not auto-generated content. If a brief surfaces something load-bearing, the user (or `/extract` invoked on the brief) promotes it to a synthesis claim in `notes/synthesis/`.

This separation is deliberate: the model can identify candidate connections; only the user can decide which become atoms in the graph.

## Modes

### `--daily` (default)

A 3-second read before the user opens anything else. Three asks — surfaced from claim activity in the last 7 days (configurable via `--scope`):

1. **Connections (3)** — non-obvious links between recent captures and older notes the user probably forgot about. Each link is one sentence: "[[claim-A]] connects to [[older-claim-B]] because <one sentence>."
2. **Pattern (1)** — one pattern across the last week's reading. *What is your brain working on, even if you haven't said it explicitly?*
3. **Question (1)** — one question worth sitting with today. Not a task. A question.

Output: `inbox/dream-{YYYY-MM-DD}.md`.

### `--weekly`

Deeper, Monday-morning ritual. 15-minute read. Four asks — surfaced from the last 30 days (configurable):

1. **Emerging thesis** — what idea is the vault building toward without it having been stated explicitly? Look at the new claims, the new MOCs, the questions that recur.
2. **Contradictions** — what has been saved recently that contradicts something believed before? `confidence: contested` claims are the obvious place to look; also flag claims whose `contradicts:` arrays are non-empty.
3. **Knowledge gaps** — what is *clearly not* being read that should be? Look at the goals.md active threads vs. recent claim coverage. Where's the gap?
4. **One action** — the single highest-leverage thing to do or think about this week. Not a task list. One sentence.

Output: `inbox/dream-week-{YYYY-WXX}.md`.

## Behaviour

### Daily mode

1. **Determine window.** Default last 7 days. With `--scope=Nd`, last N days.
2. **Pull recent activity:**
   - New claim notes by mtime in window
   - Updated `goals.md` if changed in window
   - Recent inbox additions
3. **Read context for relevance:**
   - `goals.md` (active threads)
   - The 3-5 most recently-modified claims
4. **Find connections (3):**
   - For each recent claim, query `qmd` semantically against the older corpus (older than the window). Score by `qmd` rank + frontmatter overlap. Pick the strongest 3.
   - Each connection must be *non-obvious* — connections to siblings in the same `## Topics` MOC are too easy. Prefer cross-domain connections, surprising structural parallels, or claims that contradict prior beliefs.
5. **Identify pattern (1):**
   - Look for a theme that appears in ≥2 recent claims but is named differently each time, or a methodological move that recurs.
   - State it in one sentence with two example wikilinks.
6. **Frame question (1):**
   - The question should be answerable with a session of work but not currently answered. Look at the gap between what active threads ask for and what recent claims have shown.
7. **Write brief:**

```markdown
# Daily Brief — 2026-05-08

## Connections

1. [[recent-claim-1]] connects to [[older-claim-A]] because <one sentence>.
2. [[recent-claim-2]] connects to [[older-claim-B]] because <one sentence>.
3. [[recent-claim-3]] connects to [[older-claim-C]] because <one sentence>.

## Pattern

<one sentence on the recurring theme; cite [[wikilinks]] inline>

## Question

<one question, no task>

---
*From last 7 days of activity. Read once and act. If a connection or pattern warrants a synthesis claim, run `/extract <this-brief>` or write directly in `notes/synthesis/`.*
```

### Weekly mode

Same structure, longer window, deeper asks:

1. **Determine window.** Default last 30 days.
2. **Pull all claim activity** in window. Read `goals.md`, recent MOC changes, recent contested claims.
3. **For "emerging thesis":**
   - Look at MOCs that grew most in the window. The thesis is often the H2 section that's been quietly accumulating claims around an unstated organising idea.
   - State the thesis in one sentence. Cite the strongest 3-5 claims supporting it.
4. **For "contradictions":**
   - Surface every `confidence: contested` claim. Surface every claim whose `contradicts:` array contains a wikilink to a recently-modified claim. Surface places where two recent claims disagree implicitly.
   - List the top 3.
5. **For "knowledge gaps":**
   - Compare goals.md active threads to recent claim coverage. Threads with no claim activity in the last 14 days are gaps.
   - Walk topic MOCs in the user's domain — which topics are stubs (≤3 claims) but referenced by many threads?
6. **For "one action":**
   - The highest-leverage move, given the thesis + the gaps. One sentence.
7. **Write brief:**

```markdown
# Weekly Synthesis — 2026-W19

## Emerging thesis

<one sentence>

Supported by:
- [[claim-1]]
- [[claim-2]]
- [[claim-3]]

## Contradictions

1. [[claim-A]] contradicts [[claim-B]]: <one sentence>
2. ...

## Knowledge gaps

- <thread X> in goals.md has no claim activity in 14d
- <topic Y> MOC is a stub (3 claims) but referenced by 5 active claims
- ...

## One action

<one sentence; not a task list>

---
*From last 30 days. Be direct. Challenge me. Do not summarise what I already know.*
```

## When to spawn a subagent

- `--weekly` over a vault with >100 claim modifications in window: spawn one subagent to read recent claims and one for older corpus, then aggregate. Otherwise inline.
- `--daily` over a small recent set: inline.

## What `/dream` does NOT do

- **Does not auto-write synthesis claims.** The brief surfaces candidates; the user decides which become atoms.
- **Does not modify the graph.** No edits to claims, no MOC updates. Pure read + write to inbox.
- **Does not summarise.** Summarising what the user already saved is the failure mode. Be direct, surface what's *between* the captures, ask what they haven't.
- **Does not file follow-ups.** No "tasks for tomorrow." One question, one action — that's the discipline.

## Failure modes to resist

- **Sycophancy.** Don't praise the vault. State observations, including disconfirming ones.
- **Overgeneralisation.** Patterns must cite ≥2 specific wikilinks. "I notice you're thinking about X" without claims to back it is not a pattern; it's flattery.
- **Task list creep.** The output is a brief, not a TODO. One question per daily, one action per weekly. Anything more dilutes both.
- **Stale-brief mode.** If `--scope` window has fewer than 3 new claims, say "the vault has been quiet — nothing to brief on" rather than padding. Honest no-output beats fluff.

## Output

- A markdown brief in `inbox/dream-{date}.md` (daily) or `inbox/dream-week-{week}.md` (weekly)
- Print summary to user: brief location, count of connections found, link to read it

## Integration with `/extract`

If a daily or weekly brief surfaces a connection or thesis the user wants to anchor, they run `/extract <path-to-brief>`. The extract step writes a **synthesis note** (`notes/synthesis/<slug>.md`, `type: synthesis`, `composed_from:` filled with the wikilinks the brief cited) instead of a regular claim note. This is the path from "model surfaced it" to "user owns it as a graph node."

`/extract` detects synthesis-from-brief by reading the source's frontmatter or filename pattern (`dream-*.md`).

## Cross-references

- The feedback-loop framing: per the Vault-That-Adds-To-You essay (the diagnosis these modes implement)
- The eval target: `/dream`'s output is what the claim-fact-gradient essay calls the "per-session signal" — coherence, connectivity, boundary-precision moves surfaced before they become drift.
- Composes with: `/extract` (promote brief content), `/walk` (model uses it internally to find connections), `/audit` (the brief itself can be audited if it becomes a synthesis note)
