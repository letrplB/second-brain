# second-brain

A Claude Code plugin for personal knowledge graphs that **LLMs walk natively as semantic engines**.

> **Status: evolving — always work in progress.** Verbs, conventions, and presets change as the design is sharpened by use. Pull regularly (`/plugin marketplace update second-brain` or `git pull` if you cloned locally) and skim recent commits for breaking changes before relying on a workflow. Pin a commit if you need stability.

## What

A small set of orthogonal verbs operating on a directory of atomic markdown notes:

| Verb | What |
|---|---|
| `/extract` | source → atomic claim notes (mechanical, inline) |
| `/connect` | wire a note into the graph (forward + backward links) |
| `/walk` | semantic + topology query over the graph |
| `/audit` | schema + link + cold-read quality check |
| `/learn` | full ingestion: extract → connect → audit. `--deep` parallelises per-claim |
| `/init` | scaffold a vault from a preset (guided or quick) |
| `/anneal` | methodology-coach pass on recent work (explicit, never proactive) |
| `/dream` | model surfaces 3 connections + 1 pattern + 1 question from recent activity to inbox |

Surrender system (opt-in via `surrender.enabled` in `vault.yaml`, default off):

| Verb | What |
|---|---|
| `/no-surrender` | probe user grip on a claim across mechanism / implications / falsifiability / bounds; updates engagement vector with FSRS-inspired decay |
| `/teach` | Socratic teaching on identified gaps (3–5 prompts per session, 30% revelation cap). Does NOT write engagement — no-write contract enforced at the tool-allowlist level. |

## What it is not

- Not a queue. Not a pipeline. Not a state machine.
- No phase tracking, no mandatory subagents, no orchestration of orchestration.
- No invisible hooks that fire when you can't see them.

## The frame

The graph is data. The LLM is the runtime. A claim note is a structured atom; a wikilink is an edge; the model walks both. The plugin gives the substrate to walk and the editorial conventions to keep the graph walkable. It does not script the walk.

Detailed principles, verb specs, and conventions: see [`DESIGN.md`](./DESIGN.md).

## Layout

```
second-brain/
├── .claude-plugin/{plugin.json, marketplace.json}
├── DESIGN.md                     # design overview + 8 principles
├── README.md                     # you are here
├── ATTRIBUTION.md                # acknowledgements for inherited research material
├── presets/
│   ├── research/                 # for research vaults (note=claim, MOC=topic-map)
│   └── personal/                 # for personal vaults (note=memory, MOC=life-area-map)
├── skills/
│   ├── extract/SKILL.md
│   ├── connect/SKILL.md
│   ├── walk/{SKILL.md, tools/topology.py}
│   ├── audit/{SKILL.md, tools/schema-check.py, tools/link-check.sh, tools/health-metrics.py}
│   ├── learn/SKILL.md
│   ├── init/SKILL.md
│   ├── anneal/SKILL.md
│   ├── dream/SKILL.md
│   ├── no-surrender/{SKILL.md, probes.md}
│   └── teach/{SKILL.md, pedagogy.md}
└── reference/
    ├── methodology.md            # editorial conventions
    ├── empirical-grounding/      # ~60 PKM/cognition notes (consulted on demand)
    └── templates/                # frontmatter contracts
```

## Install

Two paths — pick one.

### A. From the marketplace (recommended)

Inside Claude Code:

```
/plugin marketplace add letrplB/second-brain
/plugin install second-brain@second-brain
```

The first command registers this repo as a marketplace; the second installs the `second-brain` plugin from it. Both verbs (`/extract`, `/walk`, …) and presets become available immediately. Update later with `/plugin marketplace update second-brain`.

### B. Clone locally (for development or pinned versions)

```bash
git clone https://github.com/letrplB/second-brain.git ~/Code/second-brain
```

Then in Claude Code:

```
/plugin marketplace add ~/Code/second-brain
/plugin install second-brain@second-brain
```

Skills auto-discover from `skills/<name>/SKILL.md`. Edit files in the cloned directory and reload — no rebuild step.

### After install

Pick a vault location and scaffold it:

```
/init
```

`/init` is guided by default (asks for vault path, preset, options). For a one-liner: `/init research --at ~/vault` (or `personal`).

### Updating

This plugin is evolving — verbs and conventions change as the design is sharpened by use. Pull updates regularly.

**Marketplace install:**

```
/plugin marketplace update second-brain
/plugin update second-brain@second-brain
```

Then restart Claude Code (the update step prints a `restart required to apply` reminder).

Step 1 re-pulls the latest `marketplace.json` from GitHub. Step 2 fetches the new plugin code based on the refreshed registry — Claude Code tracks the install by git commit SHA, so new commits on `main` are picked up even without a version bump.

To refresh *all* marketplaces at once: `/plugin marketplace update` (no name).

**Clone-local install:** `git pull` in the cloned directory. Claude Code re-reads the skill files on next reload — no plugin update command needed since the marketplace source is your local path.

## Walking the graph

Atoms are claims. Titles are prose propositions. Bodies are 150–400 words with inline `[[wikilinks]]` carrying surrounding prose. MOCs are leading-underscore files with bidirectional links to their members. Frontmatter is the contract; `description` is the model's first triage signal when deciding whether to follow a link.

Read `DESIGN.md` and `reference/methodology.md` to understand the conventions. Then `/init` and start writing.
