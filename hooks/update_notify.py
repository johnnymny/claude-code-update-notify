"""SessionStart hook: notify when Claude Code has been updated.

Compares current version against stored version. When different,
fetches release notes via GitHub CLI and injects them into the session
so the agent can summarize changes for the user.

The hook does NOT update the version file. The agent must run:
  echo -n "<version>" > ~/.claude/hooks/.claude-code-last-version
after confirming the update was shown to the user.
This prevents lost notifications when the session is discarded (e.g. /resume).

Requirements:
- Python 3.10+
- GitHub CLI (gh) installed and authenticated
"""

import json
import subprocess
import sys
from pathlib import Path

VERSION_FILE = Path.home() / ".claude" / "hooks" / ".claude-code-last-version"


def get_current_version():
    """Get current Claude Code version."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        # Output format: "2.1.49 (Claude Code)" or just "2.1.49"
        return result.stdout.strip().split()[0] if result.stdout else None
    except Exception:
        return None


def get_release_notes(old_ver, new_ver):
    """Fetch release notes for versions between old and new."""
    try:
        result = subprocess.run(
            ["gh", "release", "list", "--repo", "anthropics/claude-code",
             "--limit", "10", "--json", "tagName"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode != 0:
            return None

        releases = json.loads(result.stdout)
        tags_to_fetch = []
        for r in releases:
            tag = r["tagName"]
            ver = tag.lstrip("v")
            if old_ver and ver <= old_ver:
                break
            tags_to_fetch.append(tag)

        if not tags_to_fetch:
            return None

        notes = []
        for tag in tags_to_fetch[:3]:  # max 3 versions to keep output reasonable
            result = subprocess.run(
                ["gh", "release", "view", tag, "--repo", "anthropics/claude-code",
                 "--json", "body,tagName",
                 "--jq", '.tagName + "\\n" + .body'],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0 and result.stdout.strip():
                notes.append(result.stdout.strip())

        return "\n\n".join(notes) if notes else None
    except Exception:
        return None


def main():
    raw = sys.stdin.read()
    try:
        json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return

    current = get_current_version()
    if not current:
        return

    old_ver = None
    if VERSION_FILE.exists():
        old_ver = VERSION_FILE.read_text(encoding="utf-8").strip()

    if not old_ver:
        # First run — record current version silently, notify from next update
        VERSION_FILE.write_text(current, encoding="utf-8")
        return

    if old_ver == current:
        return

    notes = get_release_notes(old_ver, current)
    if notes:
        print(f"[UPDATE] Claude Code updated: {old_ver or 'unknown'} -> {current}")
        print(f"Summarize the key changes for the user.\n\n{notes}")
    else:
        print(f"[UPDATE] Claude Code updated: {old_ver or 'unknown'} -> {current}")
        print("Release notes unavailable. Inform the user of the version change.")

    # IMPORTANT: Do NOT update VERSION_FILE here.
    # The agent must run this after confirming the notification was delivered:
    #   echo -n "<current_version>" > ~/.claude/hooks/.claude-code-last-version
    print(f"\n[ACTION REQUIRED] Run: echo -n \"{current}\" > ~/.claude/hooks/.claude-code-last-version")


if __name__ == "__main__":
    main()
