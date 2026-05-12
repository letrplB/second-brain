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
2. If topology flag → invoke `tools/topology.py` with the appropriate sub-command. Parse result.
3. If semantic → invoke `qmd` searches. Parse + filter.
4. If both → constrain semantic to topology-result subset.
5. Format the output as a ranked list with descriptions and a short *why-it-matched* annotation.
6. Print.

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
