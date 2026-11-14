# Schemas & `mission_ctl.py` Contract

All runtime artifacts live under `<repo_root>/_planning/<YYYYMMDD>-<slug-title>/`, excluded locally via `<git-common-dir>/info/exclude` without touching tracked `.gitignore`.

## 1. Compact `plan.md` (Target: 40-80 Lines)

Created by `mission_ctl.py init` and updated atomically by `task-done`, `ruling`, `review-result`, `check-criteria`, `distill`, `skip-distill`, and `audit`:

```markdown
# Mission: <title>

- Slug: `<canonical-kebab-slug>`
- Mode: `<inline|subagent|worktree>`
- Status: `<active|completed>`
- RepoRoot: `<absolute workspace root>`
- BaselineTree: `<git write-tree SHA or nongit:sha256>`
- HeadAtStart: `<HEAD SHA | UNBORN | NON_GIT>`
- CleanStart: `<true|false>`

## Objective

<1-3 concise sentences>

## Archive Pointers

- `<lesson-name>` (<YYYY-MM-DD>) -- <description> (`<path>`)

## Tasks

- [ ] **T1**: <concrete deliverable>

## Success Criteria

- [ ] C1: <verifiable acceptance condition>

## Rulings & Verification

- [Init] <timestamp> baseline `<sha8>`
- [Task T1] <timestamp> passed `<command>` (<N> files)
- [Ruling] <timestamp> decision="..." why="..." cost="..."
- [Review] <timestamp> verdict=`pass` summary="..."
- [Distill] saved `<path>` (or skipped reason="...")
- [Audit] pass (<timestamp>, tasks=N, diff=M files)
```

## 2. Mechanical Receipt Log (`logs/.events.jsonl`)

Append-only NDJSON records backing `audit` checks and `skip-distill` trigger detection; removed automatically when `audit` passes (unless `--keep-logs`):

| Event | Fields |
| :--- | :--- |
| `init` | `ts`, `event`, `slug`, `mode`, `repo_root`, `base_tree`, `head_sha`, `clean_start` |
| `task_start` | `ts`, `event`, `task_id`, `tree`, `head_sha` |
| `task_attempt` | `ts`, `event`, `task_id`, `cmd`, `exit_code`, `verify_only` |
| `task_done` | `ts`, `event`, `task_id`, `start_tree`, `end_tree`, `changed_files`, `verify_only` |
| `ruling` | `ts`, `event`, `decision`, `why`, `cost` |
| `review` | `ts`, `event`, `verdict`, `summary` |
| `distill` | `ts`, `event`, `lesson_path`, `name`, `keywords` |
| `skip_distill` | `ts`, `event`, `reason`, `local_only`, `triggers` |

Learning triggers counted by `skip-distill`: `task_attempt` with `exit_code != 0`, `review` with `verdict == "revise"`, and `ruling` events. When total triggers > 0, `skip-distill` exits `2` unless `--local-only` is passed.

## 3. Distilled Lesson Markdown Schema

Saved to `<archive_dir>/<slug>/lessons/<YYYY-MM-DD>-<name>.md` (`-r2`, `-r3` on same-day name collision):

```markdown
---
name: "<kebab-case-name>"
description: "<concise trigger + rule>"
keywords: ["english-term", "中文关键词", "..."]
mission_date: "<YYYY-MM-DD>"
---

# Lesson: <name>

**Lesson:** <10 to 150 units (ASCII words + CJK chars)>

**Evidence:** <verified command, file:line, or log observation>
```

All YAML frontmatter strings and `keywords` arrays are JSON-serialized (`ensure_ascii=False`) so colons `: `, backticks, quotes, and CJK characters remain 100% valid YAML 1.2 without indentation ambiguity.

## 4. `mission_ctl.py` CLI Summary

- `slug [--cwd DIR] [--archive-dir DIR]`
- `init --title T --objective O [--cwd DIR] [--terms K] [--mode inline|subagent|worktree] [--slug S] [--task ...] [--criteria ...]`
- `task-start <task_id> [--mission DIR]`
- `task-done <task_id> [--mission DIR] [--verify-only] -- <cmd...>`
- `diff [--mission DIR] [--task ID] [--stat]`
- `ruling [--mission DIR] --decision D --why W [--cost C]`
- `review-result [--mission DIR] --verdict pass|revise --summary S`
- `check-criteria [--mission DIR] (--all | --index N ...)`
- `match-lessons (--slug S | --cwd DIR) --query Q [--terms T] [--limit 3] [--archive-dir DIR]`
- `distill [--mission DIR] --name KEBAB --description D --keywords CSV --evidence E (--body B | --body-file P) [--ascii-only]`
- `skip-distill [--mission DIR] --reason R [--local-only]`
- `audit [--mission DIR] [--verify-only] [--keep-logs]`
- `doctor-archive [--archive-dir DIR] [--scan-repos DIR] [--merge SRC:DST ...] [--backup-dir DIR] (--dry-run | --apply)`
