# Destructive Command Guard — Claude Code PreToolUse Hook

A lightweight bash hook that blocks dangerous commands before Claude Code executes them.

## Blocked Patterns

| Pattern | Why |
|---|---|
| `rm -rf` | Recursive force-delete |
| `DROP TABLE` | SQL table destruction |
| `git push --force` | Overwrites remote history |
| `TRUNCATE` | SQL table wipe |
| `DELETE FROM` (no `WHERE`) | Deletes all rows |

## Install

```bash
cp block-destructive.sh ~/.claude/hooks/ && chmod +x ~/.claude/hooks/block-destructive.sh
```

Then add the hook to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/block-destructive.sh"
          }
        ]
      }
    ]
  }
}
```

That's it. Blocked attempts are logged to `~/.claude/hooks/blocked.log`.

## Log Format

```
[2026-04-05T13:00:00+00:00] BLOCKED | reason: Blocked: 'rm -rf' is a destructive filesystem command | command: rm -rf / | project: /home/user/myproject
```

## How It Works

The hook receives JSON on stdin from Claude Code's `PreToolUse` event. It checks the `tool_input.command` field against the blocked patterns. If a match is found, it returns a JSON `permissionDecision: "deny"` response and logs the attempt. Normal commands pass through with `exit 0`.

## Requirements

- `jq` (pre-installed on most systems, required by Claude Code)
- `bash`

## License

MIT
