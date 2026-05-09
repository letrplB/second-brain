#!/usr/bin/env python3
"""
health-metrics.py — vault-level health dashboard.

Implements the per-session eval the claim-fact-gradient essay calls for:
four metric families covering coherence, connectivity, boundary precision,
and confidence distribution. Designed to be run by /audit --vault.

Run from the vault root.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_fm(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    block = m.group(1)
    rest = text[m.end():]
    out: dict = {}
    cur = None
    for raw in block.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith("  - ") and cur is not None:
            out.setdefault(cur, []).append(line[4:].strip().strip("\"'"))
            continue
        if ":" not in line:
            cur = None
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if v == "":
            cur = k
            continue
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            out[k] = [s.strip().strip("\"'") for s in inner.split(",")] if inner else []
        else:
            out[k] = v.strip("\"'")
        cur = None
    return out, rest


def collect_notes(vault: Path) -> dict:
    notes = {}
    for f in (vault / "notes").rglob("*.md"):
        text = f.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_fm(text)
        notes[f.stem] = {"path": f, "fm": fm, "body": body, "text": text}
    return notes


def build_adj(notes: dict) -> dict:
    adj: dict = {s: set() for s in notes}
    for s, info in notes.items():
        for m in WIKILINK_RE.finditer(info["text"]):
            target = m.group(1).strip().replace(" ", "-").lower()
            # try direct slug + display-form-slugified
            for cand in (m.group(1).strip(), target):
                if cand in notes and cand != s:
                    adj[s].add(cand)
                    adj[cand].add(s)
                    break
    return adj


def is_moc(slug: str, fm: dict) -> bool:
    return slug.startswith("_") or fm.get("type") in {
        "topic-map", "domain-map", "index", "life-area-map"
    }


# ─── Metric families ─────────────────────────────────────────────────────────

def coherence(notes: dict) -> dict:
    """Dangling links + contested-unresolved + MOC orphans."""
    existing = set(notes.keys())
    dangling = 0
    dangling_files = 0
    contested_unresolved = 0
    for s, info in notes.items():
        text = info["text"]
        local_dangling = 0
        for m in WIKILINK_RE.finditer(text):
            target_raw = m.group(1).strip()
            slug = target_raw.replace(" ", "-").lower()
            if target_raw not in existing and slug not in existing:
                local_dangling += 1
        if local_dangling:
            dangling_files += 1
            dangling += local_dangling
        # contested-unresolved: confidence==contested and no contradicts populated
        fm = info["fm"]
        if fm.get("confidence") == "contested":
            contradicts = fm.get("contradicts", [])
            if not contradicts or contradicts == [""]:
                contested_unresolved += 1
    return {
        "dangling_links": dangling,
        "files_with_dangling": dangling_files,
        "contested_unresolved": contested_unresolved,
    }


def connectivity(notes: dict, adj: dict) -> dict:
    claim_like = {s for s, info in notes.items()
                  if info["fm"].get("type") in {"claim", "synthesis", "memory"}
                  and not s.startswith("_")}
    orphans = [s for s in claim_like if not adj.get(s)]
    degrees = [len(adj.get(s, ())) for s in claim_like]
    mean_deg = sum(degrees) / len(degrees) if degrees else 0
    moc_uncovered = []
    for s in claim_like:
        if not any(n.startswith("_") for n in adj.get(s, ())):
            moc_uncovered.append(s)
    return {
        "total_claims": len(claim_like),
        "orphans": len(orphans),
        "orphan_rate": (len(orphans) / len(claim_like)) if claim_like else 0,
        "mean_degree": round(mean_deg, 2),
        "moc_uncovered": len(moc_uncovered),
    }


def boundary_precision(notes: dict) -> dict:
    short = 0
    long = 0
    paraphrase = 0
    for s, info in notes.items():
        if info["fm"].get("type") not in {"claim", "synthesis", "memory"}:
            continue
        desc = info["fm"].get("description", "")
        if not isinstance(desc, str):
            continue
        if len(desc) < 30:
            short += 1
        if len(desc) > 240:
            long += 1
        # crude paraphrase check: shared content words >=80% of desc tokens
        title_text = s.replace("-", " ").lower()
        d_tokens = set(re.findall(r"[a-z]{4,}", desc.lower()))
        t_tokens = set(re.findall(r"[a-z]{4,}", title_text))
        if d_tokens and t_tokens and len(d_tokens & t_tokens) >= 0.8 * len(d_tokens):
            paraphrase += 1
    return {
        "descriptions_short": short,
        "descriptions_long": long,
        "descriptions_paraphrase": paraphrase,
    }


def confidence_distribution(notes: dict) -> dict:
    enum_dist: Counter = Counter()
    score_values = []
    score_score_pairs = 0
    enum_score_disagree = 0
    BUCKETS = {
        "speculative": (0.0, 0.4),
        "probable": (0.4, 0.75),
        "established": (0.75, 1.0),
    }
    for s, info in notes.items():
        fm = info["fm"]
        if fm.get("type") not in {"claim", "synthesis", "memory"}:
            continue
        c = fm.get("confidence")
        if c:
            enum_dist[c] += 1
        if "confidence_score" in fm:
            try:
                score = float(fm["confidence_score"])
            except (TypeError, ValueError):
                continue
            if 0.0 <= score <= 1.0:
                score_values.append(score)
                if c in BUCKETS:
                    score_score_pairs += 1
                    lo, hi = BUCKETS[c]
                    if not (lo <= score <= hi):
                        enum_score_disagree += 1
    mean_score = (sum(score_values) / len(score_values)) if score_values else None
    return {
        "enum_distribution": dict(enum_dist),
        "score_count": len(score_values),
        "score_mean": round(mean_score, 3) if mean_score is not None else None,
        "score_enum_disagreements": enum_score_disagree,
    }


def render(stats: dict) -> str:
    out = []
    out.append("## Health Metrics\n")
    c = stats["coherence"]
    out.append("**Coherence**")
    out.append(f"  dangling links:           {c['dangling_links']} (across {c['files_with_dangling']} files)")
    out.append(f"  contested unresolved:     {c['contested_unresolved']}\n")
    n = stats["connectivity"]
    out.append("**Connectivity**")
    out.append(f"  claims/synthesis total:   {n['total_claims']}")
    out.append(f"  orphans:                  {n['orphans']} ({n['orphan_rate']*100:.1f}%)")
    out.append(f"  mean degree:              {n['mean_degree']}")
    out.append(f"  MOC coverage gaps:        {n['moc_uncovered']}\n")
    b = stats["boundary_precision"]
    out.append("**Boundary precision**")
    out.append(f"  descriptions <30 chars:   {b['descriptions_short']}")
    out.append(f"  descriptions >240 chars:  {b['descriptions_long']}")
    out.append(f"  paraphrase-of-title:      {b['descriptions_paraphrase']}\n")
    cd = stats["confidence_distribution"]
    out.append("**Confidence distribution**")
    enums = " | ".join(f"{k}: {v}" for k, v in sorted(cd['enum_distribution'].items()))
    out.append(f"  enum:                     {enums}")
    if cd["score_count"] > 0:
        out.append(f"  numeric score (n={cd['score_count']}):    mean {cd['score_mean']}")
        out.append(f"  enum/score disagreements: {cd['score_enum_disagreements']}")
    else:
        out.append("  numeric scores:           none set yet (optional confidence_score field)")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=".")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    vault = Path(args.vault).resolve()
    if not (vault / "notes").is_dir():
        print(f"no notes/ at {vault}", file=sys.stderr)
        return 2

    notes = collect_notes(vault)
    adj = build_adj(notes)

    stats = {
        "coherence": coherence(notes),
        "connectivity": connectivity(notes, adj),
        "boundary_precision": boundary_precision(notes),
        "confidence_distribution": confidence_distribution(notes),
    }

    if args.json:
        print(json.dumps(stats, indent=2))
    else:
        print(render(stats))
    return 0


if __name__ == "__main__":
    sys.exit(main())
