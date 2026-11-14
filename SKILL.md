---
name: mission-runner
description: Standalone full-loop task orchestrator backed by mechanical verification gates, isolated git tree snapshots, fresh read-only review, and bilingual archive recall. Use for multi-step coding missions (3+ files, cross-module refactors, feature builds, debugging investigations), pre-written implementation plans, or explicit requests like "mission", "auto-iterate", or "execute this plan".
---

# Mission Runner v3

Mechanical control-plane orchestration using zero-dependency `scripts/mission_ctl.py` (Python 3.9+ stdlib) and compact isolated planning (`_planning/<YYYYMMDD>-<slug>/plan.md`).

Let `<ctl>` denote `<skill-dir>/scripts/mission_ctl.py`. Use `<ctl>` subcommands for all state transitions, git diffs, checkboxes, and archive operations rather than hand-editing `plan.md` or parsing YAML/git manually.

## Step 0: Recall & Initialize

1. Parse the user request:
   - **Pre-written spec/plan**: map its concrete deliverables directly to tasks and verifiable criteria.
   - **Fuzzy or one-liner objective**: inspect affected files first so tasks name real modules and checks.
2. Run initialization from the repository root:

```bash
python3 <ctl> init \
  --title "<short mission title>" \
  --objective "<1-3 sentence goal>" \
  --mode <inline|subagent|worktree> \
  --terms "<key symbols, modules, Chinese/English terms>" \
  --task "<T1 concrete action>" \
  --task "<T2 concrete action>" \
  --criteria "<C1 objective check>"
```

   - `init` resolves the canonical slug (worktree-safe), protects `_planning/` via `<git-common-dir>/info/exclude`, snapshots the baseline working tree without disturbing the user's git index, writes `plan.md` + `logs/.events.jsonl`, and prints matched lesson pointers (`<= 3`).
3. If `init` printed lesson pointers, read those specific lesson files before editing code.

## Step 1: Select Execution Topology

Choose the simplest topology matching task coupling:

| Scope | Mode | Execution & Commit Policy |
| :--- | :--- | :--- |
| `<= 3` coupled or algorithmic tasks | `inline` | Main agent executes sequentially; keep changes uncommitted for user review. |
| `4+` modular or cross-file tasks | `subagent` | Controller stays lean and delegates each task to a fresh Implementer subagent; when `CleanStart` is `true`, commit each verified task atomically via explicit file paths. |
| Parallel or risky cross-branch work | `worktree` | Execute in isolated worktree/branch; merge verified work back explicitly. |

When spawning subagents, follow [references/subagent-briefs.md](references/subagent-briefs.md) and inherit host-configured subagent model and reasoning caps. See [references/harness-adapters.md](references/harness-adapters.md) if subagents are unavailable.

## Step 2: Execute & Verify Each Task

For each task `T<N>` in `## Tasks`:

1. Snapshot task baseline:
   ```bash
   python3 <ctl> task-start T<N> --mission <mission_dir>
   ```
2. Implement the task (`inline` directly, or via a fresh Implementer subagent brief containing only the task slice, target files, and required test command).
3. **Rulings, not stalls**: resolve minor local design or naming choices pragmatically and log them immediately:
   ```bash
   python3 <ctl> ruling --mission <mission_dir> --decision "<choice>" --why "<reason>" --cost "<reversal effort>"
   ```
   Pause and ask the user only on four hard boundaries:
   - Destructive or irreversible external actions (schema drops, force pushes, remote state mutation).
   - Incompatible interpretations of a public API, schema, or user-visible contract.
   - Missing runtime secret, credential, or environment access.
   - Two failed repair attempts on the same blocker.
4. Run mechanical verification:
   ```bash
   python3 <ctl> task-done T<N> --mission <mission_dir> -- <verification command>
   ```
   `task-done` logs full command output to `logs/task-T<N>.log`, prints exit code plus the last 15 lines, requires exit `0`, and requires a non-empty diff since task start (pass `--verify-only` for purely diagnostic/doc checks). Only passing `task-done` checks `- [x]` in `plan.md`.
5. In `subagent` mode with `CleanStart=true`, stage only files changed in `T<N>` (via `diff --task T<N>`) and create a clean atomic commit. In `inline` mode, skip git commits unless the user asks.

## Step 3: Fresh Read-Only Review

1. Inspect cumulative changes (`git write-tree` diff from mission start):
   ```bash
   python3 <ctl> diff --mission <mission_dir> --stat
   python3 <ctl> diff --mission <mission_dir>
   ```
2. Dispatch ONE fresh read-only Reviewer subagent (clean context, separate from implementation) using the Reviewer brief in [references/subagent-briefs.md](references/subagent-briefs.md). For high-risk schema, auth, or state-transition tasks, also run a mid-mission review after that task.
   - Single-agent harnesses without subagents run a cold-read self-review over `diff --mission <dir>` checking every item in the Reviewer brief.
3. Record verdict:
   ```bash
   python3 <ctl> review-result --mission <mission_dir> --verdict <pass|revise> --summary "<findings>"
   ```
   If `revise`, fix blocking defects, re-verify via `task-done`, and re-review until `pass`.
4. Verify all success criteria and mark them complete:
   ```bash
   python3 <ctl> check-criteria --mission <mission_dir> --all
   ```

## Step 4: Trigger-Gated Distillation & Final Audit

1. Check whether learning triggers occurred (`task_attempt` failure, review `revise`, or non-trivial `ruling`):
   - **Clean zero-trigger run**: record skip and move straight to `audit`:
     ```bash
     python3 <ctl> skip-distill --mission <mission_dir> --reason "<why nothing generalizable surfaced>"
     ```
   - **Triggered run**: distill 1-2 concrete lessons grounded in observed evidence (or pass `skip-distill --local-only` only when blockers were strictly environment-specific):
     ```bash
     python3 <ctl> distill --mission <mission_dir> \
       --name "<kebab-case-lesson-name>" \
       --description "<one-line trigger + rule>" \
       --keywords "<english-term, 中文关键词, ...>" \
       --evidence "<failing command, log file, or line reference>" \
       --body "<10-150 effective EN words + CJK chars>"
     ```
2. Run final mechanical audit (verifies 0 unchecked tasks/criteria, `task_done` backing every `[x]`, non-empty net diff unless `--verify-only`, passing review, and distillation decision; updates status to `completed` and cleans up `logs/`, preserving `plan.md`):
   ```bash
   python3 <ctl> audit --mission <mission_dir>
   ```
3. Present a concise final report citing only verified commands, changed files, rulings made, and distilled lesson paths.

## References

- [references/subagent-briefs.md](references/subagent-briefs.md) -- Implementer & fresh Reviewer prompt templates + host cap rules
- [references/schemas.md](references/schemas.md) -- `plan.md`, `.events.jsonl`, YAML lesson schemas, and `mission_ctl.py` CLI map
- [references/harness-adapters.md](references/harness-adapters.md) -- Multi-harness paths, subagent invocation, and worktree/archive conventions
