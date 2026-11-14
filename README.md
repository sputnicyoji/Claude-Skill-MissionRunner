# Mission Runner

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/github/v/release/sputnicyoji/Claude-Skill-MissionRunner)](https://github.com/sputnicyoji/Claude-Skill-MissionRunner/releases)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B%20stdlib-blue.svg)](scripts/mission_ctl.py)

Mechanically verified full-loop task orchestrator skill for AI coding agents across Claude Code, Codex CLI/App, Antigravity / Gemini CLI, and Cursor.

Mission Runner v3 pairs a compact positive-framed orchestrator spine ([SKILL.md](SKILL.md), `<= 160` lines) with a zero-dependency Python 3.9+ standard-library control plane ([scripts/mission_ctl.py](scripts/mission_ctl.py)), replacing brittle prompt-only loops and self-graded checklists with deterministic command receipts and fresh read-only review.

## Key Capabilities

| Capability | Mechanism | Why It Matters |
| :--- | :--- | :--- |
| **Mechanical Task Gates** | `mission_ctl.py task-done` runs verification commands, writes full logs, asserts non-empty tree diff, and logs `.events.jsonl` before flipping `- [x]`. | Prevents premature or hallucinated task completion without external receipts. |
| **Zero-Interference Git Snapshots** | Uses temporary `GIT_INDEX_FILE` + `git write-tree` and excludes `_planning/` via `<git-common-dir>/info/exclude`. | Tracks clean, dirty, staged, linked-worktree, and unborn-HEAD repos without touching `.git/index` or `.gitignore`. |
| **Adaptive Execution Topology** | Chooses `inline` (`<= 3` coupled tasks), `subagent` (`4+` cross-file tasks), or `worktree` per scope. | Avoids subagent overhead on small fixes while keeping controller context lean on large builds. |
| **Fresh Read-Only Reviewer** | Inspects cumulative `mission_ctl.py diff` in a clean read-only subagent context before completion. | Eliminates same-context confirmation bias; distinguishes blocking defects from minor nits. |
| **Rulings, Not Stalls** | Logs pragmatic local decisions via `ruling` and escalates only on four hard boundaries. | Maintains autonomous momentum on minor choices while honoring high-risk boundaries. |
| **Stopword-Safe Bilingual Archive** | `match-lessons` combines word-boundary English tokens (filtered against stopwords) with CJK bigrams (`<= 3` pointers). | Prevents stopword false positives while accurately recalling prior English and Chinese lessons. |
| **Trigger-Gated Distillation** | Requires 1-2 evidenced lessons (`distill`) on runs with failures, `revise` verdicts, or rulings; allows `skip-distill` on clean runs. | Avoids empty boilerplate lessons while capturing hard-won insights with bilingual keywords. |

## When to Use vs. When to Skip

| Recommended | Skip / Use Lighter Workflow |
| :--- | :--- |
| Multi-file feature builds (`3+` files or cross-layer modules) | Single-line edits or trivial typo fixes |
| Cross-module refactoring or bug investigations needing end-to-end verification | Pure Q&A, code reading, or research requests |
| Executing pre-written implementation plans / specs end to end | Rapid throwaway spikes with no acceptance checks |

## Installation & Multi-Harness Setup

Clone the repository once and symlink it so all local harnesses share the exact same version:

```bash
git clone https://github.com/sputnicyoji/Claude-Skill-MissionRunner.git ~/Projects/Claude-Skill-MissionRunner

# Shared agent skills root (Codex CLI / Codex App reads ~/.agents/skills)
ln -s ~/Projects/Claude-Skill-MissionRunner ~/.agents/skills/mission-runner

# Claude Code
ln -s ../../.agents/skills/mission-runner ~/.claude/skills/mission-runner

# Cursor
ln -s ~/.claude/skills/mission-runner ~/.cursor/skills/mission-runner

# Gemini CLI / Antigravity (~/.gemini/config/skills shares ~/.agents/skills by default;
# if separate on your machine, link explicitly):
# ln -s ~/.agents/skills/mission-runner ~/.gemini/config/skills/mission-runner
```

Requires Python 3.9+ and Git; uses only Python standard library modules (`scripts/mission_ctl.py`).

## Quick Start & Lifecycle

Ask the agent naturally ("execute this mission", "auto-iterate through these requirements") or invoke `mission-runner` explicitly:

```text
Implement idempotent order refunds across the refund service and unit tests.
```

The orchestrator drives `scripts/mission_ctl.py` through isolated workspace initialization, mechanical per-task verification, fresh review, distillation, and final audit:

```text
init (slug + git write-tree baseline + match-lessons)
  └─▶ task-start T1 ──▶ implement ──▶ task-done T1 -- <verify cmd>
        │                                  │
        ▼                                  ▼
   ruling (minor calls)          next task / optional mid-run review
                                           │
                                           ▼
                    diff + fresh read-only review (pass | revise)
                                           │
                                           ▼
                 distill / skip-distill ──▶ audit (removes logs/, keeps plan.md)
```

See a real control-plane-generated mission artifact at [examples/_planning/20261114-order-refund/plan.md](examples/_planning/20261114-order-refund/plan.md).

## Execution Modes & Escalation Boundaries

| Mode | Typical Scope | Delegation & Git Commit Policy |
| :--- | :--- | :--- |
| `inline` | `<= 3` coupled or algorithmic tasks | Main agent executes sequentially; working tree stays uncommitted for user inspection. |
| `subagent` | `4+` modular or cross-file tasks | Controller dispatches fresh Implementer briefs per task; when `CleanStart=true`, commits each verified task via explicit file paths. |
| `worktree` | Isolated or parallel branch refactors | Runs inside a linked git worktree while resolving the shared repository slug and `.git/info/exclude`. |

Minor local choices are decided autonomously and logged via `ruling`. The orchestrator pauses and asks the user only on four hard boundaries:
1. Destructive or irreversible external actions (schema drops, force pushes, remote state mutation).
2. Incompatible interpretations of a public API, schema, or user-visible contract.
3. Missing runtime secrets, credentials, or environment access.
4. Two consecutive failed repair attempts on the same blocker.

## Control Plane CLI (`scripts/mission_ctl.py`)

| Subcommand | Role |
| :--- | :--- |
| `slug` | Resolve worktree-safe lowercase kebab archive slug (preserving existing archive namespaces). |
| `init` | Guard `_planning/` via `<git-common-dir>/info/exclude`, snapshot baseline tree, match lessons, write `plan.md`. |
| `task-start` | Snapshot current workspace tree before starting a task. |
| `task-done` | Execute verification command, log full output, assert non-empty diff, mark `- [x]` only on exit `0`. |
| `diff` | Render `git diff` or `--stat` from mission baseline or task start to current state. |
| `ruling` | Record an autonomous local ruling and append JSONL receipt. |
| `review-result` | Record fresh read-only Reviewer verdict (`pass` or `revise`). |
| `check-criteria` | Mark verified items under `## Success Criteria`. |
| `match-lessons` | Search archive lessons with stopword-filtered English + CJK bigram scoring (`<= 3` pointers). |
| `distill` | Save a bilingual (`10-150` unit), evidence-backed lesson with JSON-safe YAML frontmatter. |
| `skip-distill` | Record intentional skip on zero-trigger runs (or `--local-only` for machine-specific blockers). |
| `audit` | Enforce zero unchecked tasks/criteria, mechanical receipts, net diff, passing review, and log cleanup. |
| `doctor-archive` | Backup, reconcile duplicate repo slugs, and repair legacy YAML frontmatter in `~/.claude/mission-archive`. |

## Upgrading Legacy v2 Lesson Archives

Existing `~/.claude/mission-archive/` directories created by v2 may contain scalar `keywords`, nested `metadata.mission_date`, unquoted colons/backticks in YAML, or split directories from renamed git remotes vs local folder names. Preview and repair safely with automatic backup:

```bash
# 1. Dry-run inspection (zero writes)
python3 scripts/mission_ctl.py doctor-archive --scan-repos ~/Projects --dry-run

# 2. Backup first, then reconcile namespaces and repair YAML frontmatter
python3 scripts/mission_ctl.py doctor-archive \
  --scan-repos ~/Projects \
  --backup-dir ~/Backups/mission-archive-backup \
  --apply
```

## Testing & Verification

Run the pure-stdlib unit and lifecycle suite (verifies ASCII purity, real index preservation, unborn HEAD, empty-diff rejection, anti-tamper audit, bilingual matching, trigger gating, and archive repair):

```bash
python3 -m unittest discover -s tests -v
```

## Reference Guides & Repository Structure

- [SKILL.md](SKILL.md) -- Concise orchestrator instructions loaded by coding agents (`<= 160` lines)
- [references/subagent-briefs.md](references/subagent-briefs.md) -- Implementer & fresh read-only Reviewer templates and host model/effort cap policy
- [references/schemas.md](references/schemas.md) -- `plan.md`, `logs/.events.jsonl`, YAML lesson frontmatter, and CLI reference
- [references/harness-adapters.md](references/harness-adapters.md) -- Multi-harness path resolution, git worktrees, and fallback guidance
- [CHANGELOG.md](CHANGELOG.md) -- Release history (v3.0.0 migration notes included)
- [examples/_planning/20261114-order-refund/plan.md](examples/_planning/20261114-order-refund/plan.md) -- Sample completed v3 mission plan

```text
Claude-Skill-MissionRunner/
├── SKILL.md
├── README.md
├── CHANGELOG.md
├── LICENSE
├── scripts/
│   └── mission_ctl.py
├── tests/
│   └── test_mission_ctl.py
├── references/
│   ├── subagent-briefs.md
│   ├── schemas.md
│   └── harness-adapters.md
└── examples/
    └── _planning/
        └── 20261114-order-refund/
            └── plan.md
```

## Contributing

Keep `scripts/mission_ctl.py` and `tests/test_mission_ctl.py` zero-dependency Python 3.9+ stdlib and pure ASCII (`\u4e00-\u9fff` escapes in code), and verify `python3 -m unittest discover -s tests -v` passes before committing.

## License

[MIT](LICENSE)
