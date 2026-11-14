# Mission Runner

A standalone, mechanically verified full-loop task orchestrator for AI coding agents across Claude Code, Codex CLI, and Antigravity / Gemini CLI.

Mission Runner v3 replaces prompt-heavy state machines and self-graded compliance checklists with a concise positive-framed spine ([SKILL.md](SKILL.md)) backed by a zero-dependency Python 3.9+ stdlib control plane ([scripts/mission_ctl.py](scripts/mission_ctl.py)).

## Why v3

- **Mechanical Verification Gates Instead of Self-Grading**: `mission_ctl.py task-done` runs real commands, logs full output, verifies a non-empty `git write-tree` diff, and flips `- [x]` checkboxes only on verified success.
- **Zero-Interference Git Snapshots**: Uses a temporary `GIT_INDEX_FILE` + `git write-tree` so clean, dirty, staged, worktree, and unborn-HEAD repositories can be tracked without touching `.git/index` or polluting `.gitignore` (excludes `_planning/` via `.git/info/exclude`).
- **Adaptive Topology (`inline` vs `subagent` vs `worktree`)**: Executes 1-3 tightly coupled tasks directly inline without over-delegation, and fans out 4+ cross-file tasks to fresh per-task Implementer subagents while keeping the controller lean.
- **Fresh Read-Only Review**: Replaces same-context grading with cumulative `mission_ctl.py diff` inspection by one fresh read-only Reviewer before final audit.
- **Rulings, Not Stalls**: Resolves local design ambiguities pragmatically with logged `[Ruling]` receipts and pauses only on destructive actions, public contract ambiguity, missing secrets, or two failed fix attempts on the same blocker.
- **Stopword-Safe Bilingual Lesson Archive**: `match-lessons` pairs word-boundary English tokens (filtering noise stopwords) with CJK bigrams to recall `<= 3` pointed lessons per run; `distill` enforces bilingual keywords and grounded evidence on runs with blockers, while `skip-distill` skips trivial clean runs.

## Installation

Clone the repository and symlink it into your active skill directory so local updates apply immediately:

```bash
git clone https://github.com/sputnicyoji/Claude-Skill-MissionRunner.git ~/Projects/Claude-Skill-MissionRunner

# Claude Code
ln -s ~/Projects/Claude-Skill-MissionRunner ~/.claude/skills/mission-runner

# Codex CLI / shared agent skills
ln -s ~/Projects/Claude-Skill-MissionRunner ~/.agents/skills/mission-runner
```

Requires Python 3.9+ and Git; uses only Python standard library modules.

## Quick Start

Trigger via natural requests ("execute this mission", "auto-iterate through these specs") or invoke `mission-runner` explicitly on multi-file tasks:

```text
Implement idempotent order refunds across refund service and unit tests.
```

Behind the scenes, the orchestrator drives `scripts/mission_ctl.py`:

```
init (slug + snapshot + match-lessons)
  └─▶ task-start T1 ──▶ implement ──▶ task-done T1 -- <verify cmd>
        │                                  │
        ▼                                  ▼
   ruling (if needed)            next task / mid-run review
                                           │
                                           ▼
                    diff + fresh read-only review (pass | revise)
                                           │
                                           ▼
                 distill / skip-distill ──▶ audit (cleans logs/)
```

## Control Plane CLI (`scripts/mission_ctl.py`)

| Command | Role |
| :--- | :--- |
| `slug` | Resolve worktree-safe lowercase kebab archive slug (preserving existing namespaces). |
| `init` | Protect `_planning/` via `.git/info/exclude`, snapshot baseline tree, match lessons, create compact `plan.md`. |
| `task-start` | Snapshot current workspace tree before starting a task. |
| `task-done` | Run verification command, record output log, assert non-empty diff, flip `- [x]` on exit `0`. |
| `diff` | Show `git diff` / `--stat` across the whole mission or a single task. |
| `ruling` | Append a pragmatic design ruling and log JSONL receipt. |
| `review-result` | Record fresh read-only Reviewer verdict (`pass` or `revise`). |
| `check-criteria` | Mark verified items in `## Success Criteria`. |
| `match-lessons` | Bilingual stopword-filtered lesson search (`<= 3` pointers). |
| `distill` / `skip-distill` | Trigger-gated saving of bilingual 10-150 unit lessons (or explicit skip). |
| `audit` | Enforce zero unchecked tasks/criteria, mechanical receipts, net diff, passing review, and clean `logs/`. |
| `doctor-archive` | Backup, deduplicate duplicate repo slugs, and repair legacy YAML frontmatter in `~/.claude/mission-archive`. |

## Testing

Run the pure-stdlib unit test suite (including ASCII purity, temporary-index preservation, unborn HEAD, bilingual matching, trigger gating, and archive repair):

```bash
python3 -m unittest discover -s tests -v
```

## Repository Structure

```text
Claude-Skill-MissionRunner/
├── SKILL.md                             # Compact orchestrator spine (<= 160 lines)
├── README.md                            # Project overview and usage
├── CHANGELOG.md                         # Release history
├── scripts/
│   └── mission_ctl.py                   # Python 3.9+ stdlib control plane CLI
├── tests/
│   └── test_mission_ctl.py              # Unit and lifecycle integration suite
├── references/
│   ├── subagent-briefs.md               # Implementer & fresh read-only Reviewer templates
│   ├── schemas.md                       # plan.md, .events.jsonl, lesson YAML contracts
│   └── harness-adapters.md              # Claude Code, Codex CLI, Gemini/Antigravity notes
└── examples/
    └── _planning/
        └── 20261114-order-refund/
            └── plan.md                  # Sample v3 completed mission artifact
```

## Contributing

Keep `scripts/mission_ctl.py` zero-dependency Python 3.9+ stdlib and pure ASCII (`\u4e00-\u9fff` escapes in code), and run `python3 -m unittest discover -s tests -v` before committing.

## License

MIT
