# second-brain

A Claude Code plugin for personal knowledge graphs that **LLMs walk natively as semantic engines**.

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
│   ├── audit/{SKILL.md, tools/schema-check.py, tools/link-check.sh}
│   ├── learn/SKILL.md
│   ├── init/SKILL.md
│   └── anneal/SKILL.md
└── reference/
    ├── methodology.md            # editorial conventions
    ├── empirical-grounding/      # ~60 PKM/cognition notes (consulted on demand)
    └── templates/                # frontmatter contracts
```

## Install

(WIP — install instructions land when the plugin packs into a marketplace bundle.)

For local development: this directory is the plugin source. Point Claude Code at `second-brain/` as a custom plugin directory; skills auto-discover from `skills/<name>/SKILL.md`.

## Walking the graph

Atoms are claims. Titles are prose propositions. Bodies are 150–400 words with inline `[[wikilinks]]` carrying surrounding prose. MOCs are leading-underscore files with bidirectional links to their members. Frontmatter is the contract; `description` is the model's first triage signal when deciding whether to follow a link.

Read `DESIGN.md` and `reference/methodology.md` to understand the conventions. Then `/init` and start writing.
