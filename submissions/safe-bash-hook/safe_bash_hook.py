#!/usr/bin/env python3
"""
Claude Code pre-tool-use hook — blocks destructive bash commands.
Place at: ~/.claude/hooks/safe_bash_hook.py
"""
import json
import sys
import re
import os
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / ".claude/hooks/blocked.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

BLOCKED_PATTERNS = [
    (r'\brm\s+-[^\s]*r[^\s]*\s+-[^\s]*f|rm\s+-[^\s]*f[^\s]*\s+-[^\s]*r|\brm\s+-rf\b|\brm\s+-fr\b', "rm -rf is destructive and irreversible"),
    (r'\bDROP\s+TABLE\b', "DROP TABLE permanently deletes a database table"),
    (r'\bgit\s+push\s+--force\b|\bgit\s+push\s+-f\b', "git push --force can overwrite remote history"),
    (r'\bTRUNCATE\b', "TRUNCATE permanently removes all rows from a table"),
    (r'\bDELETE\s+FROM\s+\w+\s*(?:;|$)', "DELETE without WHERE clause removes all rows"),
]

def check_command(command: str) -> tuple[bool, str]:
    """Returns (is_blocked, reason)."""
    for pattern, reason in BLOCKED_PATTERNS:
        if re.search(pattern, command, re.IGNORECASE):
            return True, reason
    return False, ""

def log_blocked(command: str, reason: str, project_path: str):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] BLOCKED | project={project_path} | reason={reason} | cmd={command}\n")

def main():
    try:
        hook_input = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    project_path = hook_input.get("cwd", os.getcwd())

    blocked, reason = check_command(command)

    if blocked:
        log_blocked(command, reason, project_path)
        print(json.dumps({
            "decision": "block",
            "reason": f"🚫 Blocked: {reason}. Command: `{command[:100]}`. Check ~/.claude/hooks/blocked.log for full log."
        }))
        sys.exit(0)

    sys.exit(0)

if __name__ == "__main__":
    main()
