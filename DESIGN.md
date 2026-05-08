# Design

> *A graph of atomic structured claims, walkable by AI (LLMs) natively as semantic engines.*

This document is the design overview. Read it once to understand what `second-brain` is and why it's shaped the way it is. Every decision elsewhere in the plugin clears the principles below or gets cut.

## The frame

The graph is data. The LLM is the runtime.

A claim note is a structured atom: a sentence-as-title, a body, frontmatter that names what kind of claim it is and what it touches, and inline wikilinks marking semantic connections. That is the entire substrate. No queues, no phases, no ticking state.

Walking the graph is what an LLM does *natively*: read a node, follow a link, read another, decide where to go next, hold the partial answer in working context, return it. This is what semantic engines are for.

The plugin's job is therefore not to script the walk. Its job is to:

- Make claims easy to write well (templates, validators on demand, clear conventions).
- Make the graph easy to walk (consistent frontmatter, consistent linking style, a search index).
- Make synthesis easy to do (a small set of orthogonal verbs the model can compose).
- Otherwise stay out of the way.

## Eight design principles

### P1. Trust the model as runtime
No mandatory subagent rules. No phase machines. If a task is small, the model handles it inline. If it's large, the model decides to delegate. Delegation is a tool, not a law.

### P2. The graph is the only source of truth
The notes folder *is* the database. No queue file, no completed-task list, no parallel state machinery that has to stay in sync with what's on disk. Anything derivable from the notes is derived on demand.

### P3. Adapt to source density, not to source class
A tweet should produce 1–3 claims. A paper should produce 10–30. The plugin lets the model see the source and decide. No "tweet vs paper" config dial.

### P4. Make the rare path visible, not the common path mandatory
Heavy passes (whole-vault audit, deep ingestion, methodology coach) are opt-in tools the model reaches for when it has a reason — not phases that fire every time. Default to fast; escalate when the work merits it.

### P5. Composition over choreography
A small set of orthogonal primitives the model can compose freely beats a large set of named workflows that pre-decide the composition. The skills are verbs, not recipes.

### P6. Inline-first, subagent-when-justified
Subagents are valuable for: parallel independent work, protecting context window from large tool outputs, fresh-context for adversarial review. They are *not* valuable for every step of a sequential pipeline. Default to inline; spawn a subagent only when there's a real reason.

### P7. Visible state, no ceremony
When the model does work, the user sees what's happening. Progress reporting is an interface concern, not an architectural one. **No invisible hooks.** Orientation happens in the visible turn, performed by the model on session start.

### P8. Domain-aware without domain-prescriptive
The vocabulary file lets the same skills produce domain-native output (claim/topic-map for research, memory/life-area-map for personal, etc.). The plugin doesn't enforce domain-specific note schemas — let the user shape the graph by writing notes the way their field actually thinks.

## What "good" looks like

A user processing a source feels:
- *Fast.* Tweet → claims in seconds. Paper → claims in minutes.
- *Honest.* The model says what it's about to do, does it, and shows what changed.
- *Light.* The graph state lives in the notes. Nothing else has to be reconciled.
- *Composable.* Simple verbs combine for new things without writing new skills.
- *Walkable.* Reading any claim and following its links is the canonical way to use the graph.

A user inspecting the plugin sees:
- A handful of skills (verbs), each doing one thing well.
- A clear note schema with a small frontmatter contract.
- A vocabulary file that maps universal terms to their domain.
- No queues, no orchestration layers, no phase machines.

## Verbs

Seven active, one reserved for the future:

| Verb | Type | What it does |
|---|---|---|
| `/extract` | primitive | source → atomic claim notes (mechanical, inline) |
| `/connect` | primitive | wire a note into the graph (forward + backward links) |
| `/walk` | primitive | semantic + topology query over the graph |
| `/audit` | primitive | schema + link + cold-read quality report |
| `/learn` | composite | full ingestion: extract → connect → audit. `--deep` parallelises per-claim |
| `/init` | composite | scaffold a vault from a preset (guided or quick) |
| `/anneal` | composite | methodology-coach pass on recent work; explicit, never proactive |
| `/dream` | reserved | LLM-driven consolidation of high-level understanding (future) |

Detailed specs in each `skills/<verb>/SKILL.md`.

## Data model

Four persistent stores — and the *only* four:

| Store | What |
|---|---|
| `notes/**.md` | the graph itself: atomic claims, papers, methods, MOCs |
| `goals.md` | session intentions (small YAML head + free-form body) |
| `sessions/` | append-only session transcripts (audit log) |
| `vault.yaml` | runtime config: vocabulary, qmd flag, preset, domain |

That's it. No queue, no tasks file, no observation/tension folders, no methodology directory of accumulated rules. State that wants to live somewhere lives in note frontmatter.

## Frontmatter contract

The frontmatter is the contract. Every note has at minimum:

```yaml
---
description: "≤240 char one-liner that adds info beyond the title"
type: claim | paper | method | topic-map | domain-map | memory | life-area-map | index
confidence: <enum specific to type>
created: YYYY-MM-DD
---
```

Type-specific extensions (e.g. `source`, `evidence_type`, `supports`, `contradicts`, `methods`, `tags` for claims) live in the templates at `reference/templates/`.

Three rules that don't bend:
- **Title is a prose proposition.** `cognitive-surrender-is-path-dependent.md`, not `surrender.md`.
- **Description ≠ summary.** Layer heuristic → mechanism → implication. Paraphrasing the title is wrong.
- **Inline wikilinks have surrounding prose.** Never bare `[[a]] [[b]]` in claim bodies.

## Walking conventions

- Three-tier MOC topology: `index.md` → `_<domain>.md` → `_<topic>.md` → leaf claim. Bidirectional links — every claim ends with a `## Topics` footer; every MOC has a `## Core claims` section.
- Atom titles compose into wikilinks that read as sentences (`title as claim enables traversal as reasoning`).
- Confidence is honest: `established` is rare and earned; `probable` is the typical case; `speculative` is fine *and must be marked*; `contested` is for active counter-evidence.

## Subagent policy

Default: inline. Spawn a subagent only when:
- `/learn --deep` (one subagent per claim, end-to-end — extract+connect+audit per claim, isolated context)
- `/walk` would return 50+ candidates (spawn a filterer)
- `/audit --vault` (spawn a fresh-context inspector)

**The unit of context isolation is the claim, not the phase.** Never spawn a subagent for a single phase of a single claim — that's the failure mode the inline-first stance exists to avoid.

## What this is not

- A queue.
- A pipeline.
- A state machine.
- A finite set of phases.
- A tool that runs against you.

It is a graph and seven verbs that let the model edit it without ceremony.

## Non-goals

- **Hard determinism.** The plugin is cooperative with an LLM, not a deterministic compiler. Same input may produce slightly different graphs across runs; that's acceptable.
- **Multi-user collaboration semantics.** Single-user, single-vault. If multi-user is needed later, it's a different plugin.
- **Generic-purpose markdown editing.** The plugin assumes the conventions above; if you want freeform notes, use a different tool.

## Where to look next

- `README.md` — short intro for newcomers
- `skills/<verb>/SKILL.md` — what each verb does
- `reference/methodology.md` — editorial conventions
- `reference/empirical-grounding/` — ~60 PKM/cognition notes consulted on demand
- `reference/templates/` — frontmatter contracts per note type
- `presets/<preset>/CLAUDE.md.template` — what a vault's CLAUDE.md looks like
