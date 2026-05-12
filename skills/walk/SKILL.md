---
name: walk
description: Query the graph. Semantic search + topology operations. The model's primary navigation tool over the vault.
version: "0.1"
user-invocable: true
allowed-tools: Read, Glob, Grep, Bash, mcp__qmd__query, mcp__qmd__multi_get, mcp__qmd__get
argument-hint: "[query] [--orphans|--bridges <topic>|--neighbors <claim>|--centrality] — natural language query (semantic) or topology mode."
---

# /walk

**Intent.** Walk the graph and return what's relevant. Semantic search is the default; topology operations are opt-in via flags.

## Modes

### Semantic mode (default)

User asks: `/walk how does annealing relate to crystallisation in dmsn synthesis?`

1. Route to `qmd` MCP. Use `lex` (BM25) + `vec` (semantic) sub-queries. Pass `intent` so qmd's snippets are useful.
2. Optionally augment with `hyde` (hypothetical document) if the query is abstract.
3. Score and merge results. Filter by `minScore: 0.5` to drop low-confidence hits.
4. Return a ranked list:
   ```
   [[claim-title-1]] (claim, confidence: probable)
     description...
     why-it-matched: ...
   [[claim-title-2]] ...
   ```

### Topology mode

Specific operations on the graph structure. Each is a flag; tools/topology.py provides the computation.

| Flag | What it returns |
|---|---|
| `--orphans` | claims with no inbound or outbound `[[wikilinks]]` |
| `--bridges <topic>` | claims with high betweenness centrality bridging the named topic to others |
| `--neighbors <claim> [--depth N]` | claims within N hops of the named claim |
| `--centrality` | ranked list of high-centrality (hub) claims |
| `--moc-coverage` | list of claims that aren't in any `_<topic>.md` MOC |
| `--disconnected-clusters [--min-size N]` | pairs of MOCs that share no member claims and no 1-hop cross-edges. Meta-MOCs (frontmatter `meta: true`) are excluded so they don't pollute the lonely-pair signal. |

### Mixed mode

A semantic query with a topology constraint, e.g. `/walk crystallisation --neighbors-of dmsn-synthesis --depth 2`. Run topology to get a candidate set, then semantic-rank within it.

## Behaviour

1. Parse the argument: query string, flags.
2. **Read `vault/vault.yaml`. Check `qmd.enabled`, `surrender.enabled`, `surrender.walk_integration`.** Re-read every invocation; never cache any flag.
3. If topology flag → invoke `tools/topology.py` with the appropriate sub-command. Parse result.
4. If semantic and `qmd.enabled: true` → invoke `qmd` searches. Parse + filter. Continue at step 6.
5. If semantic and `qmd.enabled: false` → use the **grep-fallback path** (see "Grep fallback" section below). Continue at step 6.
6. If topology + semantic → constrain semantic to topology-result subset.
7. Format the output as a ranked list with descriptions and a short *why-it-matched* annotation.
8. **If `surrender.enabled && surrender.walk_integration`: read engagement frontmatter from each result claim, compute decay, render the engagement column and the weakest-grip panel.** Else: skip surrender rendering entirely; output is byte-identical to the gated-off behaviour.
9. Print, with a one-line preamble noting which retrieval path was used (qmd / grep-fallback) and the surrender state (enabled / off).

## Grep fallback (qmd disabled or unavailable)

Used when `qmd.enabled: false` in `vault.yaml`, OR when `qmd` is configured-on but unreachable / returns sparse results (≤2 hits on a non-trivial query). The fallback is honest, not silent — always announce it in the preamble so the user knows ranking quality differs.

### Approach

1. Extract content tokens from the query: drop English stopwords (the, of, and, to, a, in, is, for, etc.), drop punctuation, lowercase.
2. For each content token, run `grep -l -i -F "<token>"` over `notes/claims/*.md` and `notes/synthesis/*.md`. Collect matched paths.
3. Score each path by **number of distinct query tokens it matches**. Tiebreak by total match count (`grep -c`).
4. Take top-15 by score. Read each file's frontmatter (first ~30 lines) to extract title, type, confidence, description.
5. Filter to claims/synthesis whose description or title plausibly answers the query — if the score is high but the description is unrelated (false-positive token match), drop it. State the filtering rationale internally.
6. Truncate to top-10.

### Preamble line

When grep-fallback is used, the first line of output must be:

```
retrieval: grep-fallback (qmd disabled in vault.yaml) | surrender: enabled (λ=0.4)
```

Or when qmd is on:

```
retrieval: qmd | surrender: enabled (λ=0.4)
```

Or when surrender is off:

```
retrieval: qmd | surrender: off
```

The preamble is one line, terse, always there. Users should be able to tell at a glance which retrieval path ran.

### When grep-fallback is honest

- The user knows it's not semantic. The why-it-matched annotation now reads "token match: X, Y, Z" rather than "semantically related to ...".
- Re-ranking by surrender (v2) is invalid on grep-fallback results because there's no semantic relevance score to combine with; surrender stays informational only.
- If grep-fallback returns < 3 hits, say so clearly: "grep-fallback returned only N results — broaden the query or re-enable qmd via `qmd embed && set qmd.enabled: true`."

## Surrender integration (gated)

This block only runs when both `surrender.enabled: true` AND `surrender.walk_integration: true` in `vault.yaml`. Otherwise it is **not executed** — not run-with-zero-output, but skipped entirely.

### Reading engagement from a claim

For each result claim:

1. Read the claim file's frontmatter (`Read` tool, small range to capture the YAML head).
2. If `engagement` block is absent: aggregate engagement = 0, last_tested = none.
3. Else: for each scored axis (value not null):
   - Compute decayed engagement: `e_now = e₀ · 0.9 ^ (Δt / s)` where `Δt` = days from `last_tested` to today, `s` = `stability[axis]` (default per-evidence-type if missing: theoretical/meta-analysis → 180, experimental/observational → 90, computational → 60, synthesis → 90).
   - Treat unscored axes (null or absent) as 0.
4. Aggregate over all four axes (`mechanism`, `implications`, `falsifiability`, `bounds`) using **mean** (sum of decayed values for scored axes plus zeros for unscored, divided by 4).
5. Compute `weight = (1 − λ) + λ · aggregate` where `λ = surrender.default_harshness` from `vault.yaml`.

### Engagement column in results

Add a `engagement` column to each result. Format:

```
[[claim-title]] (claim, confidence: probable, engagement: 0.45)
  description...
  why-it-matched: ...
  surrender: mechanism:0.6, falsifiability:0.85 — 2 axes engaged, last tested 12d ago
```

The `engagement` value shown is the aggregate (post-decay, all 4 axes). The `surrender` line shows only the scored axes with their current decayed values plus how stale the test is.

For claims with no engagement data at all: show `engagement: 0.00 (untested)` — explicit, not blank.

### Weakest-grip panel

After the ranked results, print a panel surfacing the **3 lowest-engagement claims among the top-10 results**:

```
─── weakest grip in this walk ────────────────────────────────────
[[claim-a]] — engagement 0.00 (untested) / confidence 0.85
[[claim-b]] — engagement 0.12 / confidence 0.7 — only mechanism engaged 47d ago (decayed)
[[claim-c]] — engagement 0.20 / confidence 0.8 — implications and bounds untested
─── you may be reasoning from premises you have not engaged with ─

suggest: /no-surrender [[claim-a]]
```

- Only show the panel when at least one of the top-10 has aggregate engagement < 0.5
- Suggest a `/no-surrender` invocation for the single weakest claim in the panel
- If all top-10 are engaged (aggregate ≥ 0.5 each), skip the panel entirely

### Deployment-safety footer

After the panel (or in its place if not shown), two lines: the value, and a verbal band:

```
aggregate deployment_safety (λ=0.4, top-5): 0.62   ┃ mixed engagement (3 of 5 engaged)
```

Format: `aggregate deployment_safety (λ=<value>, top-<N>): <value>   ┃ <band> (<engaged>/<N> engaged)`

The value is the product of weights across the top-N results — a sanity check on the walk as a whole. Compute over top-5 (not top-10) so the multiplicative product isn't dominated by long tails of untested claims; top-5 is "what the user is realistically about to deploy."

**Verbal bands** (mandatory — number alone undersignals; near-zero numbers look broken when the diagnostic is "you have low engagement"):

| Range | Band |
|---|---|
| ≥ 0.70 | high engagement — walk is built on engaged ground |
| 0.40–0.70 | mixed engagement — some premises engaged, others not |
| 0.15–0.40 | low engagement — most premises untested |
| < 0.15 | very high surrender exposure — you are about to reason from un-engaged premises |

If only one result was returned (degenerate case), suppress the footer entirely — the chain math is uninformative.

### Re-ranking

For v1, engagement **does not re-rank** the results. The column is informational only. v2 may add `--harsh=<λ>` to re-rank by `relevance × confidence × weight(engagement, λ)`.

### Failure modes

- **Stale `last_tested` causing nonsense.** If `last_tested` is a future date (clock skew, manual edit), treat `Δt = 0` and proceed without warning. Don't crash on bad data.
- **Reading too many claims for a wide walk.** For `/walk` returning 30+ results, only compute engagement for the top-10 to bound friction. The panel still works on the top-10.
- **Gated check skipped accidentally.** The output divergence between `surrender.enabled: true` and `false` must be visible — a leaky integration breaks the deliberate-activation contract. If you're not sure whether the flag is on, re-read `vault.yaml`.

## When to spawn a subagent

- If the candidate set returned to the lead is so large (≥50 candidates) that summarising them inline would degrade context: spawn a filterer with the candidate descriptions + the user's intent, return only ~10.
- Otherwise inline.

## Tools

- `tools/topology.py` — reads `notes/**/*.md`, parses frontmatter and `[[wikilinks]]`, builds an in-memory graph, runs centrality / bridge / orphan / neighbour queries. See `tools/topology.py` for the CLI.
- `qmd` MCP — semantic + lex search over the indexed vault.

## Failure modes to resist

- **Returning everything.** If the query is broad, narrow it: ask the user a clarifying question rather than dumping 100 hits.
- **Phantom matches.** qmd may surface notes that match the query string but not the meaning. The *why-it-matched* annotation is a forcing function — if you can't articulate it, drop the hit.
- **Stale topology.** Topology results depend on the on-disk graph state. If notes have been edited mid-session, the in-memory graph in `tools/topology.py` may be stale. Re-run if necessary.
- **Reinventing the bridge-map.** When the user asks for "non-obvious cross-cluster connections" or similar, consult `notes/_cross-domain-bridges.md` *first* — its `## Wired bridges` section is the authoritative index of what's already been synthesised across clusters, and `## Open bridges` is the candidate list. Re-deriving bridges from semantic search is wasted work when the answer is already indexed.

## Cross-cluster queries

When the user asks about connections *between* clusters (not within one), the topology check is the right primitive:

1. Run `--disconnected-clusters` to enumerate pairs the graph keeps separate.
2. Read `notes/_cross-domain-bridges.md` to see which pairs already have an anchor synthesis (`## Wired bridges`) and which are candidates (`## Open bridges`).
3. For wired pairs: surface the anchor synthesis with its bridge-character (substrate / dynamics / analogy / structural parallel / counter-example) — that vocabulary is the right register for cross-cluster answers.
4. For candidates the user wants to wire: produce a proposed synthesis claim with `composed_from` listing source claims on each side. `/walk` proposes; `/connect` wires.

## Output

- A ranked list (default 10, configurable) with: title, type, confidence, description (≤200 chars), why-it-matched
- Total candidate count + filtered count
- For topology modes: the structural metric (e.g. centrality score, hop distance)

## Cross-references

- `reference/empirical-grounding/betweenness centrality identifies bridge notes connecting disparate knowledge domains.md`
- `reference/empirical-grounding/small-world topology requires hubs and dense local links.md`
- Tool: `tools/topology.py`
