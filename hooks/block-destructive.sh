#!/usr/bin/env bash
# Claude Code PreToolUse hook — blocks destructive bash commands
# Install: cp block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh

set -euo pipefail

INPUT=$(cat)
TOOL=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Only inspect Bash tool calls
[[ "$TOOL" == "Bash" ]] || exit 0

CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')
[[ -n "$CMD" ]] || exit 0

CWD=$(echo "$INPUT" | jq -r '.cwd // "unknown"')
LOG="$HOME/.claude/hooks/blocked.log"

block() {
  local reason="$1"
  mkdir -p "$(dirname "$LOG")"
  echo "[$(date -Iseconds)] BLOCKED | reason: $reason | command: $CMD | project: $CWD" >> "$LOG"
  jq -n --arg reason "$reason" '{
    hookSpecificOutput: {
      hookEventName: "PreToolUse",
      permissionDecision: "deny",
      permissionDecisionReason: $reason
    }
  }'
  exit 0
}

# --- Pattern checks (case-insensitive) ---
CMD_UPPER=$(echo "$CMD" | tr '[:lower:]' '[:upper:]')

echo "$CMD" | grep -qE 'rm\s+-[a-zA-Z]*r[a-zA-Z]*f|rm\s+-[a-zA-Z]*f[a-zA-Z]*r' \
  && block "Blocked: 'rm -rf' is a destructive filesystem command"

echo "$CMD_UPPER" | grep -qE '\bDROP\s+TABLE\b' \
  && block "Blocked: 'DROP TABLE' is a destructive SQL operation"

echo "$CMD" | grep -qiE 'git\s+push\s+.*--force\b|git\s+push\s+-f\b' \
  && block "Blocked: 'git push --force' can destroy remote history"

echo "$CMD_UPPER" | grep -qE '\bTRUNCATE\b' \
  && block "Blocked: 'TRUNCATE' is a destructive SQL operation"

# DELETE FROM without WHERE
if echo "$CMD_UPPER" | grep -qE '\bDELETE\s+FROM\b'; then
  echo "$CMD_UPPER" | grep -qE '\bDELETE\s+FROM\b.*\bWHERE\b' || \
    block "Blocked: 'DELETE FROM' without a WHERE clause deletes all rows"
fi

# All clear
exit 0
