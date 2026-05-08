#!/usr/bin/env bash
# link-check.sh — find dangling [[wikilinks]] and bare-link sequences in second-brain notes.
#
# Usage:
#   link-check.sh <note-path>        # check one note
#   link-check.sh --vault            # check all notes/**/*.md
#
# Exit code: 0 if clean, 1 if any issue.
# Output: human-readable report. Re-run with `--json` (not implemented yet) for tooling.

set -euo pipefail

usage() { echo "usage: $0 <note-path> | --vault" >&2; exit 2; }
[[ $# -ge 1 ]] || usage

vault_root="${SECOND_BRAIN_VAULT:-$PWD}"
notes_dir="$vault_root/notes"

[[ -d "$notes_dir" ]] || { echo "notes/ not found under $vault_root" >&2; exit 2; }

# Collect existing slugs (filenames without .md) under notes/
existing=$(find "$notes_dir" -type f -name '*.md' -exec basename {} .md \; | sort -u)

check_file() {
  local file="$1"
  local issues=0
  # Extract every [[wikilink]] (without alias pipe content)
  local links
  links=$(grep -oE '\[\[[^]|]+(\|[^]]*)?\]\]' "$file" 2>/dev/null \
    | sed -E 's/^\[\[([^]|]+).*\]\]$/\1/' \
    | sort -u || true)
  if [[ -n "$links" ]]; then
    while IFS= read -r target; do
      [[ -n "$target" ]] || continue
      if ! grep -qx "$target" <<<"$existing"; then
        printf "  dangling: [[%s]]\n" "$target"
        issues=$((issues + 1))
      fi
    done <<<"$links"
  fi
  # Bare-link sequences: lines with 2+ [[..]] and no other words/punctuation
  local bare
  bare=$(grep -nE '^[[:space:]]*\[\[[^]]+\]\][[:space:]]*[.,;]?[[:space:]]*\[\[[^]]+\]\][[:space:]]*[.,;]?[[:space:]]*$' "$file" || true)
  if [[ -n "$bare" ]]; then
    while IFS= read -r line; do
      printf "  bare-link sequence: %s\n" "$line"
      issues=$((issues + 1))
    done <<<"$bare"
  fi
  echo "$issues"
}

if [[ "$1" == "--vault" ]]; then
  total=0
  files_with_issues=0
  while IFS= read -r f; do
    out=$(check_file "$f")
    n=$(tail -n1 <<<"$out")
    body=$(sed '$d' <<<"$out")
    if [[ "$n" -gt 0 ]]; then
      printf "\n%s\n%s\n" "$f" "$body"
      total=$((total + n))
      files_with_issues=$((files_with_issues + 1))
    fi
  done < <(find "$notes_dir" -type f -name '*.md')
  echo
  echo "files-with-issues: $files_with_issues  total-issues: $total"
  [[ "$total" -eq 0 ]] && exit 0 || exit 1
else
  file="$1"
  [[ -f "$file" ]] || { echo "not found: $file" >&2; exit 2; }
  out=$(check_file "$file")
  n=$(tail -n1 <<<"$out")
  body=$(sed '$d' <<<"$out")
  printf "%s\n%s\n" "$file" "$body"
  echo "issues: $n"
  [[ "$n" -eq 0 ]] && exit 0 || exit 1
fi
