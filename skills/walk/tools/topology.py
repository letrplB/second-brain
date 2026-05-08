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
    """
    nodes: dict = {}
    adj: dict = defaultdict(set)
    for path in discover_notes(vault_root):
        text = path.read_text(encoding="utf-8", errors="replace")
        fm = parse_frontmatter(text)
        body = FRONTMATTER_RE.sub("", text, count=1)
        slug = slug_of(path, vault_root)
        nodes[slug] = {"path": path, "frontmatter": fm, "body": body}
        for m in WIKILINK_RE.finditer(text):
            target = m.group(1).strip()
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


if __name__ == "__main__":
    main()
