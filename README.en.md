# claude-code-update-notify

A hook that automatically displays release notes when Claude Code has been updated.

[日本語](README.md)

## What is this?

Claude Code auto-updates silently — you never know what changed. This hook:

1. Checks the version on every session start
2. If it differs from last time, fetches release notes from GitHub
3. Injects them into the session so your agent summarizes the changes

Nothing is displayed when the version hasn't changed.

## Demo

On session start, the agent reads the release notes and summarizes them for you:

```
Claude Code has been updated from 2.1.47 to 2.1.49. Key changes:

- Fixed Ctrl+C/ESC being ignored while background agents are running
- Fixed memory leaks in long-running sessions (WASM/Yoga)
- Added ConfigChange hook event — you can now fire hooks when settings change

The ConfigChange hook might be useful for you — it enables
auditing configuration changes in managed environments.
```

Raw release notes are not displayed directly. The agent reads them and provides a natural language summary.

## Installation

### 1. Copy the hook script

```bash
mkdir -p ~/.claude/hooks
cp hooks/update_notify.py ~/.claude/hooks/
```

Windows:
```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\hooks"
Copy-Item hooks\update_notify.py "$env:USERPROFILE\.claude\hooks\"
```

### 2. Add hook configuration

Add the following to `~/.claude/settings.json` (merge with existing `hooks` section if present):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python -X utf8 ~/.claude/hooks/update_notify.py"
          }
        ]
      }
    ]
  }
}
```

**Windows**: Replace the path with a full path:
```json
"command": "python -X utf8 C:\\Users\\YourName\\.claude\\hooks\\update_notify.py"
```

### 3. Requirements

- Python 3.10+ (standard library only, no dependencies)
- [GitHub CLI](https://cli.github.com/) (`gh`) — installed and authenticated

```bash
python --version
gh auth status
```

## How it works

```
Session starts (new / /resume / post-compaction)
  → SessionStart hook fires
  → Gets current version via claude --version
  → Compares with ~/.claude/.claude-code-last-version
  → If different, fetches release notes via gh release view
  → Injects into session (agent summarizes for user)
  → Updates version file
```

## Files

| File | Purpose |
|------|---------|
| `hooks/update_notify.py` | Version comparison + release notes fetcher |
| `settings.example.json` | Example hook configuration |

## Cost

- API cost: Zero (uses `gh` CLI only, no Claude API calls)
- Runtime: A few seconds only when version changes. Instant skip when unchanged

## License

MIT
