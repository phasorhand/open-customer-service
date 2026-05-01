#!/usr/bin/env bash
# OSS-First gate: block source-code writes under src/<module>/ when the module
# lacks RESEARCH.md. See CLAUDE.md for policy. Exit 2 = block (stderr → model).
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

input="$(cat)"
file_path="$(printf '%s' "$input" | jq -r '.tool_input.file_path // empty')"

# No file path → nothing to check (some Edit edge cases). Allow.
[[ -z "$file_path" ]] && exit 0

# Normalize: make path relative to project root if absolute.
case "$file_path" in
  "$PROJECT_ROOT"/*) rel="${file_path#"$PROJECT_ROOT"/}" ;;
  /*)                rel="$file_path" ;;
  *)                 rel="$file_path" ;;
esac

# Only gate writes under src/.
[[ "$rel" == src/* ]] || exit 0

# Only gate source files (not docs, fixtures, data, etc. that might live in src/).
case "$rel" in
  *.py|*.ts|*.tsx) ;;
  *) exit 0 ;;
esac

# Always allow writing the RESEARCH.md file itself.
[[ "$(basename "$rel")" == "RESEARCH.md" ]] && exit 0

# Determine the module root: src/<first-segment>/.
module="$(printf '%s' "$rel" | awk -F/ '{print $1"/"$2}')"
research="$PROJECT_ROOT/$module/RESEARCH.md"

if [[ ! -f "$research" ]]; then
  printf '[OSS-First] 模块 %s 缺少 RESEARCH.md，请先按 CLAUDE.md 规定完成 OSS 调研。\n' "$module" >&2
  printf '期望路径: %s\n' "$research" >&2
  exit 2
fi

exit 0
