#!/usr/bin/env bash
# md-ratio.sh — the markdown budget (AGENTS.md: 80 % code / 20 % markdown), two modes.
#   tree             print md % of tracked lines (evidence, journals, research, archives, reference, prototypes, assets, public excluded)
#   commit <msgfile> print staged md %; refuse > 40 % except docs/design commits
set -uo pipefail
mode="${1:-tree}"
excl='^(docs/evidence|docs/research|project/archive|project/journal|reference|prototypes|assets|public|harness/out|tmp)/'
count() { awk -v md=0 -v code=0 '{ if ($2 ~ /\.md$/) md += $1; else if ($2 ~ /\.(ts|tsx|js|mjs|mts|py|html|css|sh|glsl|json)$/) code += $1 } END { printf "%d %d\n", md, code }'; }
if [ "$mode" = "tree" ]; then
  read -r md code < <(git ls-files | grep -vE "$excl" | grep -E '\.(md|ts|tsx|js|mjs|mts|html|css|sh|glsl)$' | xargs wc -l 2>/dev/null | grep -v ' total$' | count)
  total=$((md + code)); pct=$(( total > 0 ? md * 100 / total : 0 ))
  echo "tree: md ${md} / code ${code} lines → ${pct} % markdown (budget 20 %)"
  exit 0
fi
msgfile="${2:-}"; subject="$(git stripspace --strip-comments < "$msgfile" | head -1)"
read -r md code < <(git -c core.quotePath=false diff --cached --numstat | awk -F '\t' -v excl="$excl" '$3 !~ excl { if ($3 ~ /\.md$/) md += $1 + $2; else if ($3 ~ /\.(ts|tsx|js|mjs|mts|py|html|css|sh|glsl|json)$/) code += $1 + $2 } END { printf "%d %d\n", md, code }')
total=$((md + code)); [ "$total" -gt 0 ] || exit 0
pct="$(awk -v md="$md" -v total="$total" 'BEGIN { printf "%.1f", md * 100 / total }')"
echo "commit: md ${md} / code ${code} changed lines → ${pct} % markdown"
if [ "$((md * 100))" -gt "$((total * 40))" ] && ! printf '%s' "$subject" | grep -qE '^(docs|design)(\([a-z0-9][a-z0-9/-]*\))?!?:'; then
  echo "REFUSED: > 40 % markdown. Use docs(scope): or design(scope): for a documentation/design round, or split the prose out. See docs/git/COMMITS.md." >&2
  exit 1
fi
exit 0
