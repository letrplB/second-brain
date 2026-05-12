#!/usr/bin/env python3
"""
topology.py — graph operations on a second-brain vault.

Reads notes/**/*.md, parses frontmatter + [[wikilinks]], builds an in-memory graph,
runs the operation requested via CLI subcommand.

Usage:
  topology.py orphans
  topology.py centrality [--top N]
  topology.py bridges <topic>
  topology.py neighbors <claim-slug> [--depth N]
  topology.py moc-coverage
  topology.py moc-density [--threshold N]
  topology.py disconnected-clusters [--min-size N]

Run from the vault root (the directory containing notes/).

Dependencies: stdlib only. No networkx — kept lightweight on purpose.
"""

import argparse
import os
import re
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path

WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def slug_of(path: Path, vault_root: Path) -> str:
    """Filename without extension, used as the canonical node id."""
    return path.stem


def normalize_target(target: str) -> str:
    """Normalize a wikilink target (prose-with-spaces or already-slug) to canonical lowercase-kebab form for lookup.

    Filenames in the vault use kebab-case but may preserve some uppercase (e.g. acronyms like cryo-ET).
    Wikilinks in note bodies sometimes use prose form ('cognitive surrender is path-dependent...').
    This function lowercases + collapses whitespace to single hyphen + strips non-alphanumeric (except hyphens),
    producing a stable lookup key.
    """
    target = target.strip().lower()
    # Common transliterations used in filenames (e.g. SPION@MSN → spion-at-msn)
    target = target.replace("@", "-at-")
    target = target.replace("&", "-and-")
    target = re.sub(r"\s+", "-", target)
    target = re.sub(r"[^a-z0-9-]", "", target)
    target = re.sub(r"-+", "-", target).strip("-")
    return target


def parse_frontmatter(text: str) -> dict:
    """Tiny YAML-ish parser. Only handles top-level scalar/list fields seen in second-brain notes."""
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    block = m.group(1)
    out: dict = {}
    current_list_key = None
    for raw in block.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith("  - ") and current_list_key:
            val = line[4:].strip().strip("\"'")
            out.setdefault(current_list_key, []).append(val)
            continue
        if ":" not in line:
            current_list_key = None
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val == "":
            current_list_key = key
            continue
        # inline list "[a, b, c]"
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            items = [s.strip().strip("\"'") for s in inner.split(",")] if inner else []
            out[key] = items
        else:
            out[key] = val.strip("\"'")
        current_list_key = None
    return out


def discover_notes(vault_root: Path) -> list[Path]:
    return list((vault_root / "notes").rglob("*.md"))


def build_graph(vault_root: Path) -> tuple[dict, dict]:
    """Returns (nodes_by_slug, adjacency).

    nodes_by_slug: {slug: {path, frontmatter, body}}
    adjacency: {slug: set(neighbour_slugs)} (undirected for centrality, separate-tracked for direction if needed)

    Wikilink targets are resolved against actual filenames: a prose-form `[[cognitive surrender is path-dependent...]]`
    is normalized and looked up against the kebab-case file slug. If no real file matches, the raw target is kept
    (it'll be a phantom edge — useful for diagnosing dangling links).
    """
    nodes: dict = {}
    adj: dict = defaultdict(set)
    paths = list(discover_notes(vault_root))
    real_slugs = {p.stem for p in paths}
    norm_to_real = {normalize_target(s): s for s in real_slugs}

    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        body = FRONTMATTER_RE.sub("", text, count=1)
        slug = slug_of(path, vault_root)
        nodes[slug] = {"path": path, "frontmatter": fm, "body": body}
        for m in WIKILINK_RE.finditer(text):
            raw = m.group(1).strip()
            if raw in real_slugs:
                target = raw
            else:
                target = norm_to_real.get(normalize_target(raw), raw)
            if target == slug:
                continue
            adj[slug].add(target)
            adj[target].add(slug)
    return nodes, dict(adj)


def cmd_orphans(nodes: dict, adj: dict) -> None:
    orphans = [s for s in nodes if not adj.get(s)]
    print(f"Orphans: {len(orphans)}")
    for s in sorted(orphans):
        desc = nodes[s]["frontmatter"].get("description", "")
        print(f"  {s} — {desc[:120]}")


def cmd_centrality(nodes: dict, adj: dict, top: int) -> None:
    """Crude degree centrality. Sufficient for small/medium vaults; swap for betweenness if vault grows."""
    degree = Counter({s: len(adj.get(s, ())) for s in nodes})
    print(f"Top {top} by degree centrality:")
    for slug, deg in degree.most_common(top):
        desc = nodes[slug]["frontmatter"].get("description", "")
        print(f"  {deg:4d}  {slug} — {desc[:100]}")


def cmd_neighbors(nodes: dict, adj: dict, slug: str, depth: int) -> None:
    if slug not in nodes:
        print(f"Not found: {slug}", file=sys.stderr)
        sys.exit(1)
    seen = {slug: 0}
    q: deque = deque([slug])
    while q:
        cur = q.popleft()
        d = seen[cur]
        if d >= depth:
            continue
        for nb in adj.get(cur, ()):
            if nb not in seen and nb in nodes:
                seen[nb] = d + 1
                q.append(nb)
    by_dist: dict = defaultdict(list)
    for s, d in seen.items():
        if d == 0:
            continue
        by_dist[d].append(s)
    for d in sorted(by_dist):
        print(f"distance {d} ({len(by_dist[d])}):")
        for s in sorted(by_dist[d]):
            desc = nodes[s]["frontmatter"].get("description", "")
            print(f"  {s} — {desc[:100]}")


def cmd_bridges(nodes: dict, adj: dict, topic: str) -> None:
    """Find claims that link the given topic-MOC to other topic-MOCs.

    Heuristic: a claim 'bridges' topic T if it has a [[T]] reference AND a [[T2]] reference for some T2 != T,
    and T2 is also a topic-map slug (starts with _).
    """
    target = topic if topic.startswith("_") else f"_{topic}"
    if target not in nodes:
        print(f"Topic MOC not found: {target}", file=sys.stderr)
        sys.exit(1)
    bridges = []
    for slug, neighbours in adj.items():
        if slug not in nodes:
            continue
        if target not in neighbours:
            continue
        other_topics = [n for n in neighbours if n.startswith("_") and n != target]
        if other_topics:
            bridges.append((slug, other_topics))
    print(f"Claims bridging {target}: {len(bridges)}")
    for slug, others in sorted(bridges, key=lambda x: -len(x[1])):
        desc = nodes[slug]["frontmatter"].get("description", "")
        print(f"  {slug} — bridges to {', '.join(sorted(others))}")
        print(f"      {desc[:100]}")


def cmd_moc_coverage(nodes: dict, adj: dict) -> None:
    """List claims that don't link to any topic-MOC (slug starts with '_')."""
    uncovered = []
    for slug, info in nodes.items():
        if slug.startswith("_") or info["frontmatter"].get("type") in {"index", "topic-map", "domain-map", "life-area-map"}:
            continue
        if any(n.startswith("_") for n in adj.get(slug, ())):
            continue
        uncovered.append(slug)
    print(f"Claims without MOC membership: {len(uncovered)}")
    for s in sorted(uncovered):
        desc = nodes[s]["frontmatter"].get("description", "")
        print(f"  {s} — {desc[:120]}")


def cmd_moc_density(nodes: dict, adj: dict, threshold: int) -> None:
    """For every topic-MOC, compute a paired observable: member count + internal-edge density.

    The single-axis rule "split MOCs above N claims" can't tell apart three flavours of crowded:
      1. cocktail party (sparse internal links — split candidate)
      2. working group / maturation chamber (claims cross-pressuring each other — splitting kills convergence)
      3. programme-organising thesis (dense links to a generative central claim)

    Internal-edge density distinguishes (1) from (2)+(3). The verdict combines both observables.
    Per-MOC isolated-member list is the optional extension: claims sitting in a MOC tag but not
    epistemically connected to siblings — split candidates regardless of MOC-level density.
    """
    moc_rows = []
    isolated_lists: dict = {}
    # Members of a MOC's density chamber are only the units that *organise* there:
    # claims, synthesis, memories. Papers and methods are referenced from a MOC
    # (often in their own subsections) but aren't themselves units of cross-pressure.
    DENSITY_MEMBER_TYPES = {"claim", "synthesis", "memory"}
    for slug, info in nodes.items():
        fm = info["frontmatter"]
        is_moc = slug.startswith("_") or fm.get("type") in {"topic-map", "domain-map", "life-area-map", "index"}
        if not is_moc:
            continue
        # members: only typed claim/synthesis/memory neighbours that resolve to a real file
        members = []
        for n in adj.get(slug, ()):
            if n not in nodes:
                continue
            if n.startswith("_") or n == slug:
                continue
            ntype = nodes[n]["frontmatter"].get("type", "")
            if ntype not in DENSITY_MEMBER_TYPES:
                continue
            members.append(n)
        member_count = len(members)
        if member_count == 0:
            moc_rows.append((slug, 0, 0, 0.0, 0, 0.0, "empty"))
            continue
        member_set = set(members)
        internal_degree = {m: 0 for m in members}
        internal_edges = 0
        for m in members:
            for nb in adj.get(m, ()):
                if nb in member_set and nb != m:
                    internal_degree[m] += 1
                    if m < nb:
                        internal_edges += 1
        mean_internal_degree = sum(internal_degree.values()) / member_count
        isolated = sorted([m for m, d in internal_degree.items() if d == 0])
        isolation_count = len(isolated)
        non_isolated_pct = 100.0 * (member_count - isolation_count) / member_count
        if member_count < 3:
            verdict = "small"
        elif member_count > threshold and mean_internal_degree < 1.0:
            verdict = "split-candidate"
        elif member_count > threshold:
            verdict = "productive-crowd"
        else:
            verdict = "ok"
        moc_rows.append((slug, member_count, internal_edges, mean_internal_degree, isolation_count, non_isolated_pct, verdict))
        if isolated:
            isolated_lists[slug] = isolated

    moc_rows.sort(key=lambda r: -r[1])
    print(f"MOC density report (threshold={threshold}):")
    print()
    print(f"  {'MOC':<48} {'cnt':>4} {'edges':>5} {'meanDeg':>8} {'isol':>4} {'non-iso%':>8}  verdict")
    print("  " + "-" * 96)
    for slug, count, edges, mean_deg, isol_n, non_iso_pct, verdict in moc_rows:
        print(f"  {slug:<48} {count:>4} {edges:>5} {mean_deg:>8.2f} {isol_n:>4} {non_iso_pct:>7.1f}%  {verdict}")
    print()
    if isolated_lists:
        print("Isolated members (claims listed in a MOC with zero links to siblings in the same MOC):")
        for slug in sorted(isolated_lists, key=lambda s: -len(isolated_lists[s])):
            members = isolated_lists[slug]
            print(f"  {slug} ({len(members)} isolated):")
            for m in members[:10]:
                print(f"    - {m}")
            if len(members) > 10:
                print(f"    ... +{len(members) - 10} more")
    else:
        print("No isolated members across any MOC.")


def cmd_disconnected_clusters(nodes: dict, adj: dict, min_size: int) -> None:
    """Find pairs of MOCs whose member sets are graph-disconnected.

    A pair (A, B) is disconnected if:
      - They share no member claims (no claim sits in both MOCs), AND
      - No member of A links directly to any member of B.

    Both MOCs must have >= min_size members to surface. The `index` MOC is excluded
    because it touches everything by definition and would mask real disconnection.

    Why this matters: dream/walk traverses the graph. If two clusters share no edges,
    no graph-walk can ever surface analogies between them — yet the most valuable
    bridges are often precisely cross-cluster. This subcommand surfaces the structural
    gap without proposing what should fill it (that's a /walk + /connect task).
    """
    DENSITY_TYPES = {"claim", "synthesis", "memory"}
    moc_slugs = []
    for s, info in nodes.items():
        fm = info["frontmatter"]
        is_moc = s.startswith("_") or fm.get("type") in {"topic-map", "domain-map", "life-area-map"}
        if not is_moc or s == "index":
            continue
        # Meta-MOCs (frontmatter meta: true) organize other MOCs rather than claims —
        # they touch many clusters by construction. Including them inflates the
        # disconnected-pair count with noise (a bridge-map appears "disconnected" from
        # every cluster it doesn't yet bridge, which is most of them).
        if str(fm.get("meta", "")).lower() == "true":
            continue
        moc_slugs.append(s)
    moc_slugs.sort()

    moc_members: dict = {}
    for moc in moc_slugs:
        members = set()
        for n in adj.get(moc, ()):
            if n not in nodes or n.startswith("_") or n == moc:
                continue
            ntype = nodes[n]["frontmatter"].get("type", "")
            if ntype in DENSITY_TYPES:
                members.add(n)
        moc_members[moc] = members

    pairs = []
    for i, a in enumerate(moc_slugs):
        ma = moc_members[a]
        if len(ma) < min_size:
            continue
        for b in moc_slugs[i + 1:]:
            mb = moc_members[b]
            if len(mb) < min_size:
                continue
            if ma & mb:
                continue
            cross_edges = 0
            for m in ma:
                for nb in adj.get(m, ()):
                    if nb in mb:
                        cross_edges += 1
                        break
                if cross_edges:
                    break
            if cross_edges == 0:
                pairs.append((a, b, len(ma), len(mb)))

    pairs.sort(key=lambda p: -(p[2] + p[3]))
    print(f"Disconnected MOC pairs (no shared members, no 1-hop cross-edges, both >={min_size}): {len(pairs)}")
    if not pairs:
        return
    for a, b, sa, sb in pairs:
        desc_a = nodes[a]["frontmatter"].get("description", "")[:70]
        desc_b = nodes[b]["frontmatter"].get("description", "")[:70]
        print(f"  {a} ({sa})  ↔  {b} ({sb})")
        print(f"    A: {desc_a}")
        print(f"    B: {desc_b}")


def cmd_leverage(nodes: dict, adj: dict, slug: str) -> None:
    """Generative-leverage score for a claim: how many other claims/MOCs depend
    on or organise around this one. From the claim->fact-gradient essay's caveat
    that programme-organising claims may resist factual status while shaping
    decades of work — this metric surfaces them mechanically.

    Components:
      - inbound `supports:` references (other claims that lean on this)
      - inbound `[[wikilink]]` mentions in MOC bodies (MOC memberships)
      - inbound `composed_from:` references from synthesis notes
    """
    if slug not in nodes:
        print(f"Not found: {slug}", file=sys.stderr)
        sys.exit(1)

    inbound_supports = []
    inbound_moc_listings = []
    inbound_composed_from = []

    target_link = f"[[{slug}]]"
    target_display = f"[[{slug.replace('-', ' ')}]]"
    for s, info in nodes.items():
        if s == slug:
            continue
        fm = info["frontmatter"]
        body = info["body"]
        # Frontmatter list fields where this claim might be referenced
        vals = fm.get("supports", [])
        if isinstance(vals, list) and any(slug in v or slug.replace("-", " ") in v for v in vals):
            inbound_supports.append(s)
        cf = fm.get("composed_from", [])
        if isinstance(cf, list) and any(slug in v or slug.replace("-", " ") in v for v in cf):
            inbound_composed_from.append(s)
        # MOC body inclusion (MOCs start with _)
        if s.startswith("_"):
            if target_link in body or target_display in body:
                inbound_moc_listings.append(s)

    score = len(inbound_supports) + len(inbound_moc_listings) + len(inbound_composed_from)
    print(f"leverage score for {slug}: {score}")
    print(f"  inbound supports:        {len(inbound_supports)}")
    for x in inbound_supports[:8]:
        print(f"    {x}")
    if len(inbound_supports) > 8:
        print(f"    ... +{len(inbound_supports) - 8} more")
    print(f"  MOC memberships:         {len(inbound_moc_listings)}")
    for x in inbound_moc_listings:
        print(f"    {x}")
    print(f"  inbound composed_from:   {len(inbound_composed_from)}")
    for x in inbound_composed_from[:8]:
        print(f"    {x}")


def main() -> None:
    p = argparse.ArgumentParser(description="Graph topology operations on a second-brain vault.")
    p.add_argument("--vault", default=".", help="Vault root (containing notes/).")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("orphans")
    p_cent = sub.add_parser("centrality")
    p_cent.add_argument("--top", type=int, default=20)
    p_nb = sub.add_parser("neighbors")
    p_nb.add_argument("slug")
    p_nb.add_argument("--depth", type=int, default=2)
    p_br = sub.add_parser("bridges")
    p_br.add_argument("topic")
    sub.add_parser("moc-coverage")
    p_md = sub.add_parser("moc-density")
    p_md.add_argument("--threshold", type=int, default=30)
    p_dc = sub.add_parser("disconnected-clusters")
    p_dc.add_argument("--min-size", type=int, default=5)
    p_lev = sub.add_parser("leverage")
    p_lev.add_argument("slug")

    args = p.parse_args()
    vault_root = Path(args.vault).resolve()
    if not (vault_root / "notes").is_dir():
        print(f"No notes/ directory under {vault_root}", file=sys.stderr)
        sys.exit(1)

    nodes, adj = build_graph(vault_root)

    if args.cmd == "orphans":
        cmd_orphans(nodes, adj)
    elif args.cmd == "centrality":
        cmd_centrality(nodes, adj, args.top)
    elif args.cmd == "neighbors":
        cmd_neighbors(nodes, adj, args.slug, args.depth)
    elif args.cmd == "bridges":
        cmd_bridges(nodes, adj, args.topic)
    elif args.cmd == "moc-coverage":
        cmd_moc_coverage(nodes, adj)
    elif args.cmd == "moc-density":
        cmd_moc_density(nodes, adj, args.threshold)
    elif args.cmd == "disconnected-clusters":
        cmd_disconnected_clusters(nodes, adj, args.min_size)
    elif args.cmd == "leverage":
        cmd_leverage(nodes, adj, args.slug)


if __name__ == "__main__":
    main()
