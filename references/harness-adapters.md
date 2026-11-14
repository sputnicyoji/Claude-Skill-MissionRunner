# Multi-Harness Adapter Notes

`mission-runner` is self-contained inside its cloned repository and resolves `<skill-dir>/scripts/mission_ctl.py` identically across coding harnesses.

## Harness Locations & Subagent Mapping

| Harness | Default Skill Path | Archive Root | Subagent Mechanism |
| :--- | :--- | :--- | :--- |
| **Claude Code** | `~/.claude/skills/mission-runner` | `~/.claude/mission-archive` | `Agent` / `Task` tool (inherits `CLAUDE_CODE_SUBAGENT_MODEL` when set) |
| **Codex CLI** | `~/.agents/skills/mission-runner` | `~/.claude/mission-archive` | Native subagent delegation respecting global reasoning cap (use `inline` if single-agent) |
| **Antigravity / Gemini CLI** | `~/.gemini/config/skills/mission-runner` (symlinked to `~/.agents/skills`) | `~/.claude/mission-archive` | `invoke_subagent` (passing default `inherit` unless host specifies otherwise) or `inline` |

Override the archive root in any harness or evaluation sandbox via `--archive-dir <path>` (defaults to `~/.claude/mission-archive`).

## Slug Resolution & Git Worktree Behavior

`mission_ctl.py slug` resolves canonical archive namespaces consistently across main checkouts and linked worktrees:

1. Checks `<worktree_root>/.mission-slug` then `<main_root>/.mission-slug` (`git rev-parse --git-common-dir`).
2. Computes normalized `dir_slug` from the main repository directory name and `origin_slug` from `git remote get-url origin`.
3. Preserves an existing `dir_slug` archive directory if `<archive_dir>/<dir_slug>/lessons` exists while `<archive_dir>/<origin_slug>/lessons` does not; otherwise uses `origin_slug` (falling back to `dir_slug` for local repos without remotes).

Linked worktrees automatically write `_planning/` exclusion into the shared `<git-common-dir>/info/exclude` file and read/write the shared project archive namespace without splitting lessons across temporary worktree directory names.

## Subagent Fallback Rules

When running inside a single-agent harness or under a strict subagent quota/cap:
- Execute all tasks cleanly in `inline` mode via `task-start` and `task-done`.
- Perform the Step 3 review by inspecting `python3 <ctl> diff --mission <dir>` with a fresh checklist pass before running `review-result --verdict pass`.
