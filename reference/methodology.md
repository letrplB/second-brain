# Methodology

Core editorial conventions for second-brain vaults. Six sections; each one names a principle the model is expected to honour. Detailed empirical backing lives in `empirical-grounding/`.

This file is consulted on demand by skills (especially `/audit` and `/anneal`). It is **not** loaded into every session by default.

---

## 1. Atoms

A claim note holds one proposition. The proposition is true or false; it could in principle be wrong; it is sourced to a specific text or experience. Multi-claim summaries belong in a topic-map, not a claim note.

The title is the proposition in prose form, kebab-cased into the filename. `cognitive-surrender-is-path-dependent.md` is a title; `surrender.md` is a topic label and not enough.

Bodies show *why* the claim holds: mechanism, evidence, scope conditions. 150–400 words. Shorter and the model can't tell why the claim earns its node; longer and the claim is doing too much.

See: `empirical-grounding/claims must be specific enough to be wrong.md`, `title as claim enables traversal as reasoning.md`, `elaborative encoding is the quality gate for new notes.md`.

## 2. Descriptions

The `description` field is a retrieval filter, not a summary. It is the first thing the model reads when deciding whether to follow a `[[wikilink]]`. If it merely paraphrases the title, it does no work.

A good description layers:
1. **Heuristic** — the surface signal of the claim
2. **Mechanism** — why the claim holds
3. **Implication** — what follows from it

Length 30–240 chars. Aim for one sentence with a hyphen or em-dash bridging the layers, e.g.:

> "Anneal-style maintenance lowers graph disorder without adding content — it works because structural health is domain-invariant, so periodic patient passes catch drift the creative pipeline can't surface mid-flow."

See: `empirical-grounding/descriptions are retrieval filters not summaries.md`, `good descriptions layer heuristic then mechanism then implication.md`, `distinctiveness scoring treats description quality as measurable.md`.

## 3. Wikilinks

Inline links carry the relationship. `[[wikilink]]` without surrounding prose is bare; bare links are drift. Yes:

> Confidence in inline interpretability holds up [[because the linear-probe results survive across architectures]] but only [[for representations with a single dominant axis of variation]].

No:

> Related: [[a]], [[b]], [[c]].

(Acceptable in MOCs — see §5 — but never in claim bodies.)

Links are bidirectional by convention: `/connect` adds the inverse link in the connected note. Every claim ends with a `## Topics` footer listing the MOCs it belongs to. Every MOC has a `## Core claims` (or equivalent) listing its members. The two stay in sync.

See: `empirical-grounding/inline links carry richer relationship data than metadata fields.md`, `propositional link semantics transform wiki links from associative to reasoned.md`, `forced engagement produces weak connections.md`.

## 4. Frontmatter

The frontmatter is the contract. Skills (especially `/audit`) check it. The model reads it on every triage decision.

Required for claims (research preset): `description`, `type: claim`, `confidence`, `created`, `source`, `evidence_type`, `tags`.

Optional but useful: `supports`, `contradicts`, `methods`, `replication_status`, `read_date`.

Confidence is honest: `established` is rare and earned; `probable` is the typical case; `speculative` is fine and must be marked as such; `contested` is for claims with active counter-evidence (and `contradicts:` should list the counter-claims).

See: `empirical-grounding/schema fields should use domain-native vocabulary not abstract terminology.md`, `progressive schema validates only what active modules require not the full system schema.md`, `schema templates reduce cognitive overhead at capture time.md`.

## 5. MOCs (Maps of Content)

A topic-MOC at `notes/_<topic>.md` synthesises a topic by listing its claims with context phrases:

```markdown
## Core claims
- [[claim-a]] — what it adds to this topic
- [[claim-b]] — why it matters for this topic
```

(Bare wikilinks acceptable here because the context phrase that follows the dash *is* the surrounding prose.)

MOCs split when they exceed ~20–30 claims (basic-level categorisation). MOCs absorb when they have <3 claims that aren't drawing growth. Bidirectional linking is non-negotiable.

A domain-MOC at `notes/_<domain>.md` is one level up: it lists its topic-MOCs, not individual claims.

`notes/index.md` is the root: lists domains.

### Meta-MOCs (the orthogonal layer)

A **meta-MOC** is a topic-map with frontmatter `meta: true` that organizes other MOCs rather than claims. It sits outside the three-tier hierarchy (`index → _domain → _topic → claim`) and aggregates synthesis work that bridges across it.

The canonical instance is `_cross-domain-bridges.md`. The convention:

- Every synthesis claim that bridges two MOCs sharing no other graph edges should appear in `_cross-domain-bridges` under `## Wired bridges`, with the clusters bridged, the anchor synthesis, the source claims on each side, and the bridge's *character* (substrate / dynamics / analogy / structural parallel / counter-example).
- The bridge-map's `## Open bridges` section pairs the wired list with lonely-pair output from `topology.py disconnected-clusters`. Positive and negative space lives in one place.
- The frontmatter `meta: true` is **load-bearing**: `topology.py disconnected-clusters` excludes meta-MOCs from the lonely-pair scan. Without that exclusion, the bridge-map appears "disconnected" from every cluster it doesn't yet bridge — false positives that inflate noise.

Meta-MOCs are rare. The bridge-map is the first and currently only instance. Future candidates: a tensions-map, an open-questions-map. Promote only when the meta-level reaches its own critical mass; do not create them speculatively.

See: `empirical-grounding/MOC construction forces synthesis that automated generation from metadata cannot replicate.md`, `MOCs are attention management devices not just organizational tools.md`, `basic level categorization determines optimal MOC granularity.md`, `complete navigation requires four complementary types that no single mechanism provides.md`.

## 6. The processing skeleton

Every source class shares a four-phase skeleton: capture → process → connect → verify. The plugin's verbs map onto it:

- **Capture** = drop into `inbox/` (manual, no skill)
- **Process** = `/extract`
- **Connect** = `/connect`
- **Verify** = `/audit`

`/learn` composes process+connect+verify. The skeleton is universal across domains; the *intensity* differs (research = heavy; personal = light). Don't apply research-grade processing to personal capture.

See: `empirical-grounding/every knowledge domain shares a four-phase processing skeleton that diverges only in the process step.md`, `adapt the four-phase processing pipeline to domain-specific throughput needs.md`, `continuous small-batch processing eliminates review dread.md`, `generation effect gate blocks processing without transformation.md`.

---

## When to consult `empirical-grounding/`

- `/audit` checking description quality → `empirical-grounding/descriptions are retrieval filters not summaries.md` and adjacent.
- `/learn` calibrating extraction depth → `empirical-grounding/adapt the four-phase processing pipeline to domain-specific throughput needs.md`.
- `/anneal` deciding what counts as drift → `empirical-grounding/maintenance-patterns.md`.
- `/walk` reasoning about graph health → `empirical-grounding/small-world topology requires hubs and dense local links.md`, `betweenness centrality identifies bridge notes connecting disparate knowledge domains.md`.

The notes in `empirical-grounding/` are organised into twelve clusters (cognitive constraints, scaling regimes, failure modes, atom design, wikilinks, MOC design, workflow, capture, maintenance, domain templates, schema, cross-domain). Each is consulted only when relevant — see `ATTRIBUTION.md` at the plugin root for their lineage.
