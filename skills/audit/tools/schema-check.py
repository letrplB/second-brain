#!/usr/bin/env python3
"""
schema-check.py — frontmatter validator for second-brain notes.

Reads vault.yaml to determine the active preset and the per-type contract,
then validates the given notes against that contract.

Usage:
  schema-check.py <note-path>
  schema-check.py --vault [--type claim|paper|method|topic-map|domain-map]
  schema-check.py --json <note-path>      # machine-readable output

Exit codes:
  0 if all checked notes pass
  1 if any issue is found
  2 if invocation error (missing file, malformed vault.yaml, etc.)
"""

import argparse
import json
import re
import sys
from pathlib import Path

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Per-type required fields. Kept in code (not vault.yaml) so the contract is the same across vaults
# unless a vault explicitly extends it. Add fields here as the contract evolves.
REQUIRED = {
    "claim": {"description", "type", "confidence", "created"},
    "synthesis": {"description", "type", "confidence", "created"},
    "paper": {"description", "type", "year"},
    "method": {"description", "type", "method_type"},
    "topic-map": {"description", "type"},
    "domain-map": {"description", "type"},
    "index": {"description", "type"},
    "memory": {"description", "type", "confidence", "created"},
    "life-area-map": {"description", "type"},
}

ENUMS = {
    "confidence": {
        "claim": {"established", "probable", "speculative", "contested"},
        "synthesis": {"established", "probable", "speculative", "contested"},
        "memory": {"vivid", "clear", "hazy", "reconstructed"},
    },
    "evidence_type": {
        "claim": {"experimental", "observational", "computational", "theoretical", "meta-analysis"},
        "synthesis": {"experimental", "observational", "computational", "theoretical", "meta-analysis"},
        "memory": {"direct-experience", "witnessed", "reported", "inferred"},
    },
    "type": {
        "*": {"claim", "synthesis", "paper", "method", "topic-map", "domain-map", "index", "memory", "life-area-map"},
    },
    "method_type": {
        "method": {"characterization", "synthesis", "analysis", "experimental", "computational", "statistical"},
    },
}

# Optional numeric confidence overlay: a 0..1 score. The enum stays required; the
# numeric field lets claims with replication data or statistical evidence carry
# precision the enum cannot. /audit warns if score and enum disagree heavily.
CONFIDENCE_SCORE_BUCKETS = {
    "speculative": (0.0, 0.4),
    "probable": (0.4, 0.75),
    "established": (0.75, 1.0),
    # contested is a special category: high disagreement, not a low number.
    # We don't bucket it; mismatch detection skips contested claims.
}

DESCRIPTION_MAX = 240
DESCRIPTION_MIN = 30


def parse_frontmatter(text: str) -> tuple[dict, str]:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    block = m.group(1)
    rest = text[m.end():]
    out: dict = {}
    current_key = None
    for raw in block.splitlines():
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith("  - ") and current_key:
            out.setdefault(current_key, []).append(line[4:].strip().strip("\"'"))
            continue
        if ":" not in line:
            current_key = None
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        if val == "":
            current_key = key
            continue
        if val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            items = [s.strip().strip("\"'") for s in inner.split(",")] if inner else []
            out[key] = items
        else:
            out[key] = val.strip("\"'")
        current_key = None
    return out, rest


def title_from_path(path: Path) -> str:
    return path.stem.replace("-", " ").replace("_", " ").strip()


def is_paraphrase(description: str, title_text: str) -> bool:
    """Heuristic: description is a paraphrase if it shares >= 80% of its content words with the title."""
    def tokens(s: str) -> set[str]:
        return {w.lower() for w in re.findall(r"[a-zA-Z]{3,}", s)}
    d, t = tokens(description), tokens(title_text)
    if not d or not t:
        return False
    overlap = d & t
    return len(overlap) >= 0.8 * len(d)


def check_note(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(text)
    if not fm:
        return ["no frontmatter (or unparsable)"]
    note_type = fm.get("type", "")
    if note_type not in REQUIRED:
        issues.append(f"unknown type '{note_type}'")
        return issues
    # required fields
    missing = REQUIRED[note_type] - set(fm)
    for f in sorted(missing):
        issues.append(f"missing required field: {f}")
    # enums
    for field, enum_map in ENUMS.items():
        if field not in fm:
            continue
        allowed = enum_map.get(note_type) or enum_map.get("*")
        if allowed is None:
            continue
        val = fm[field]
        if isinstance(val, list):
            bad = [v for v in val if v not in allowed]
            for b in bad:
                issues.append(f"{field}: '{b}' not in allowed values {sorted(allowed)}")
        else:
            if val not in allowed:
                issues.append(f"{field}: '{val}' not in allowed values {sorted(allowed)}")
    # description quality
    desc = fm.get("description", "")
    if isinstance(desc, str):
        if len(desc) < DESCRIPTION_MIN:
            issues.append(f"description too short ({len(desc)} < {DESCRIPTION_MIN}): a description should layer heuristic→mechanism→implication")
        if len(desc) > DESCRIPTION_MAX:
            issues.append(f"description too long ({len(desc)} > {DESCRIPTION_MAX})")
        if is_paraphrase(desc, title_from_path(path)):
            issues.append("description appears to paraphrase the title (must add information beyond title)")
    # body length (claims/synthesis/memories)
    if note_type in {"claim", "synthesis", "memory"}:
        words = len(re.findall(r"\S+", body))
        if words < 100:
            issues.append(f"body short ({words} words): expand mechanism or evidence; aim for 150-400")
        if words > 500:
            issues.append(f"body long ({words} words): consider splitting; aim for 150-400")
    # Optional confidence_score: must be a number in [0,1] and roughly agree with enum
    if "confidence_score" in fm:
        score_raw = fm["confidence_score"]
        try:
            score = float(score_raw)
        except (TypeError, ValueError):
            issues.append(f"confidence_score: '{score_raw}' is not a number")
        else:
            if not (0.0 <= score <= 1.0):
                issues.append(f"confidence_score: {score} out of [0, 1]")
            else:
                conf = fm.get("confidence", "")
                bucket = CONFIDENCE_SCORE_BUCKETS.get(conf)
                if bucket is not None and not (bucket[0] <= score <= bucket[1]):
                    issues.append(
                        f"confidence_score {score:.2f} disagrees with enum '{conf}' "
                        f"(expected within {bucket[0]:.2f}-{bucket[1]:.2f})"
                    )
    return issues


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("path", nargs="?")
    p.add_argument("--vault", action="store_true")
    p.add_argument("--type")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    if args.vault:
        roots = list(Path("notes").rglob("*.md"))
    elif args.path:
        roots = [Path(args.path)]
    else:
        print("usage: schema-check.py <path> | --vault", file=sys.stderr)
        return 2

    if args.type:
        roots = [p for p in roots if "type: " + args.type in p.read_text(encoding="utf-8", errors="replace")]

    results: dict = {}
    bad = 0
    for path in roots:
        if not path.exists():
            print(f"not found: {path}", file=sys.stderr)
            return 2
        issues = check_note(path)
        if issues:
            bad += 1
            results[str(path)] = issues

    if args.json:
        print(json.dumps({"checked": len(roots), "with_issues": bad, "issues": results}, indent=2))
    else:
        print(f"checked: {len(roots)}  with issues: {bad}")
        for path, issues in results.items():
            print(f"\n{path}")
            for issue in issues:
                print(f"  - {issue}")

    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
