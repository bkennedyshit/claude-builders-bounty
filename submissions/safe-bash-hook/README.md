# Claude Code Safe Bash Hook

Pre-tool-use hook that intercepts and blocks destructive bash commands before Claude executes them.

## Install (2 commands)

```bash
mkdir -p ~/.claude/hooks
cp safe_bash_hook.py ~/.claude/hooks/
```

Then add to `~/.claude/settings.json`:
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/safe_bash_hook.py" }]
      }
    ]
  }
}
```

## What It Blocks

| Pattern | Reason |
|---|---|
| `rm -rf` | Irreversible recursive file deletion |
| `DROP TABLE` | Permanently deletes a database table |
| `git push --force` | Overwrites remote git history |
| `TRUNCATE` | Removes all rows from a table |
| `DELETE FROM` without WHERE | Deletes all rows in a table |

## Logging

Every blocked attempt is logged to `~/.claude/hooks/blocked.log`:
```
[2026-04-02T09:00:00] BLOCKED | project=/home/user/myapp | reason=rm -rf is destructive | cmd=rm -rf /tmp/test
```

## Normal Commands

All non-destructive bash commands pass through unaffected.
