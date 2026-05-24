---
name: mission-runner
description: |
  Multi-iteration mission orchestrator for complex tasks (3+ files, multi-layer refactors,
  large feature builds, anything the user frames as a "mission" or wants you to "auto-iterate"
  on). Provides filesystem-as-memory across iterations (survives /compact), Read-Before-Decide
  goal anchoring, a Compliance Check that gates [x] marking on objective evidence rather than
  LLM self-report, and Phase 5 lesson distillation that builds cross-mission learning. Use
  whenever a task is too big to hold in chat alone — including when the user says "mission",
  "iterate on this", "for me to come back to", or describes work that will span more than a
  few obvious steps.
---

# Mission Runner

Long-running mission orchestrator. Files are the memory; build outputs and `git diff` are the
truth; LLM self-report is not.

---

## Rule 0 — The one rule you cannot skip

**A task is marked `[x]` only when BOTH are true:**
1. Step 3 (build / lint / test) passed.
2. Step 3.6 (Compliance Check) verdict = `pass`.

LLM saying "I did X" is a *hope*, not a *signal*. The `[x]` is the synthesis of "code runs"
plus "code does the right thing". Skip this and the whole anti-hallucination design collapses
into ordinary self-report.

This rule survives the Escape Hatch. There is no mode in which "I did the work" alone
justifies `[x]`.

> Cross-mapping: legacy docs and `references/prompt-template.md` call this **Mandate 5** /
> **[x] timing**. Same rule.

---

## At-a-glance: the four prohibitions + five mandates

These are the named protocol anchors that older docs (including the still-canonical
`references/prompt-template.md`) and Escape-Hatch cross-references resolve to. The detail
behind each lives in the corresponding section of this file or in `references/`.

**Four Prohibitions** (never do this):

| # | Prohibition | Anchor |
|---|---|---|
| 1 | Do NOT skip Read-Before-Decide at iteration start | §3 Step 1 |
| 2 | Do NOT silently skip validation; every failure goes to `mission_notes.md > Failures & Learnings` | §3 Step 3 + Step 3.5 |
| 3 | Do NOT close an iteration without updating `mission_plan.md` Progress Log AND `mission_notes.md` | §3 Step 4 + §4 micro-audit |
| 4 | Do NOT guess on Low confidence; AskUserQuestion and record the answer | §3 Step 1.5 |

**Five Mandates** (always do this):

| # | Mandate | Anchor |
|---|---|---|
| 1 | Read-Before-Decide at iteration start (every iteration, no exceptions) | §3 Step 1 |
| 2 | Validate by running real build/lint/test, never by claim | §3 Step 3 |
| 3 | Issue `<promise>Mission Accomplished</promise>` ONLY after 5-item Pre-Promise Audit all pass | §5 |
| 4 | Pre-Promise Audit applies even under Escape Hatch | §5 + §7 |
| 5 | `[x]` is marked ONLY after Step 3 pass AND Step 3.6 verdict = pass — **this is Rule 0 above** | §3 Step 3.6 + §3 Step 4 |

Mandates 2 / 4 / 5 remain binding under Escape Hatch (see §7). Mandates 1 / 3 are the
default per-iteration loop and can pause only if the mission is paused.

---

## 1. When to activate

Use when the task is one of:

- Multi-file / multi-layer implementation (typically 3+ files).
- Refactor that touches several subsystems.
- Anything framed as a "mission", "auto-iterate", "implement this end-to-end", or "iterate on this for me".
- Work that will plausibly span a `/compact` boundary.

Do **not** use for: single-file edits, one bug fix, Q&A, configuration tweaks.

---

## 2. Filesystem as memory

Three files (gitignored, single-mission scope) plus one cross-mission archive:

| File | Purpose | Lifecycle |
|---|---|---|
| `_planning/mission_plan.md` | Objective + Success Criteria + task list + Progress Log | Lives for the mission |
| `_planning/mission_notes.md` | Append-only: findings, decisions, failures, compliance verdicts, audit trail, deviations | Lives for the mission |
| `_planning/workflow_state.json` | OPTIONAL — crash-recovery cursor | Optional, most missions skip |
| `~/.claude/mission-archive/{slug}/lessons/*.md` | Phase 5 lessons; future missions glob these in Phase 0 step 3 | Persists across missions |

**Schemas + ready-to-copy templates:** see [`references/file-templates.md`](references/file-templates.md). Live examples filled in: see `examples/_planning/`.

Why files (not chat scrollback or memory tools): files survive `/compact`, survive subagent boundaries, and let mid-mission audits run against an external source of truth rather than what the LLM happens to remember.

---

## Phase 0 — Initialization (one-shot, at mission start)

Before the per-iteration loop starts, do these in order:

1. **Derive project slug** (no `cd` — just read command output):
   - Bash / Git Bash:
     ```bash
     slug=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" | tr '[:upper:]' '[:lower:]' | tr ' _' '--')
     ```
   - PowerShell:
     ```powershell
     $root = (git rev-parse --show-toplevel 2>$null); if (-not $root) { $root = (Get-Location).Path }
     $slug = (Split-Path -Leaf $root).ToLower() -replace '[ _]', '-'
     ```
   - Examples: `E:\Yoji\Prism-OS` → `prism-os`; `/Users/foo/My App` → `my-app`.

2. **Glob historical lessons** from `~/.claude/mission-archive/{slug}/lessons/` (the cross-mission learning consumption end):
   - If the directory does not exist → first mission for this project, skip to step 3.
   - Otherwise, read every `*.md` file's frontmatter (`name`, `description`, `keywords`).
   - **Match algorithm**: a lesson is a hit when AT LEAST ONE of:
     - Any `keywords[i]` (case-insensitive substring) appears in the user's task description, OR
     - Any whitespace-tokenized word of `description` (case-insensitive substring) appears in the task description.
   - **Cap**: keep at most 5 hits (highest-relevance by keyword count first, ties broken by `mission_date` descending). Drop the rest — Prior Lessons block must not pollute context.
   - Cache the full body of each hit for step 4.

3. **Create `_planning/` directory**:
   - Bash: `mkdir -p _planning`
   - PowerShell: `New-Item -ItemType Directory -Force -Path _planning | Out-Null`
   - **Do not mix shells**: `mkdir -p` raises `A positional parameter cannot be found` in PowerShell; the agent must pick the form matching its current shell tool.

4. **Write `_planning/mission_plan.md`** using the template in `references/file-templates.md`. The `## Prior Lessons` block content:
   - Hits in step 2 → list each lesson's file name + full body verbatim + a one-line "Source:" footer.
   - No hits → write the literal line `(no historical lessons matched this task)`.

5. **Write `_planning/mission_notes.md`** with all standard sections empty (Research Findings / Decisions Made / Failures & Learnings / Self-Reflections / Compliance Checks / Clarifications / Open Questions / Distilled Lessons / Audit Trail / Deviations & Reasons). See `references/file-templates.md` for the canonical empty form.

6. **Start the loop** (§3 Step 1 Read-Before-Decide kicks in).

---

## 3. The loop (per iteration)

```
Step 1   Read-Before-Decide      Read plan + notes + Prior Lessons block
Step 1.5 Confidence Check        High / Medium / Low + one-line reason
Step 2   Execute                 One task only. Do NOT mark [x] here.
Step 3   Validate                build / lint / test
Step 3.5 Self-Reflection         Only if Step 3 failed OR Step 3.6 escalated
Step 3.6 Compliance Check        diff matches task description?
                                 verdict in {pass, needs-revision, escalate}
Step 4   Checkpoint              If 3.6=pass → NOW mark [x] → next task or all done
```

### Step 1 — Read-Before-Decide

Read `_planning/mission_plan.md`:
- What's the Objective?
- What Phase am I in?
- What is the next unchecked `[ ]` task?
- **Read the `## Prior Lessons` block** (filled in Phase 0 step 3). If any matched lesson warns about a trap that applies to the current task, downgrade Solution Certainty / Risk Estimate accordingly in Step 1.5.

Read `_planning/mission_notes.md`:
- Last iteration's failures / learnings.
- Prior Clarifications (so you don't re-ask).
- Compliance Checks with verdict ≠ pass (those are unfinished business).
- Audit Trail (so you know which promise attempts already failed).

### Step 1.5 — Confidence Check (compact form)

State confidence in one sentence and proceed:

- **High** — proceed. ("High — plan §4 is explicit + I've already verified the file shape.")
- **Medium** — record one concern to `mission_notes.md > Open Questions`, pick the conservative option, proceed.
- **Low** — STOP. Use AskUserQuestion. Record the answer to `mission_notes.md > Clarifications` before continuing.

When Low confidence needs a *surgical* question to the user, the 4-dimension breakdown (Task understanding / Solution certainty / Dependency clarity / Risk estimate) makes the question much sharper. Full structured form: [`references/confidence-check.md`](references/confidence-check.md).

### Step 2 — Execute

One task at a time. Follow project conventions.

Update `mission_plan.md > Progress Log` with a row for this iteration. **Do not mark `[x]` here**; that happens at Step 4 after Compliance passes (Rule 0).

### Step 3 — Validate

Run the project's build / lint / test commands. Failed → Step 3.5. Passed → Step 3.6.

### Step 3.5 — Self-Reflection (compact form)

Triggered by Step 3 failure or Step 3.6 escalate.

Classify and act:

| Type | Examples | Action |
|---|---|---|
| **Simple** | Typo, missing import, unused-var lint | Fix inline. Max 2 retries this iteration. One-line note to `Failures & Learnings`. |
| **Medium** | Logic bug, missed edge case, wrong assumption | 1-2 sentence written reflection → `Self-Reflections` section → next iteration handles. |
| **Complex / 3rd time same error** | Architecture conflict, requirement ambiguity, repeated failure | AskUserQuestion. Do NOT retry blindly. |

Full Reflexion-paper protocol with structured prompt + record format: [`references/self-reflection.md`](references/self-reflection.md). The compact form above is correct for most cases.

### Step 3.6 — Compliance Check (NOT optional)

This is what makes `[x]` honest. Even if build passes, do BOTH parts:

**(a) Collect 3 signals first** (so Q1/Q2 are answered from evidence, not memory):
1. Current `[ ]` task description from `mission_plan.md` (re-read it; don't paraphrase from memory).
2. Current iteration's diff: `git diff HEAD`.
3. Most recent `Decisions Made` entry in `mission_notes.md`, if any (last decision is the most likely source of in-scope changes).

**(b) Then ask 2 questions in chat**:

1. **Q1 — Completeness**: does this diff implement the task described in the plan? (Not "code compiles" — *feature ≈ description*.)
2. **Q2 — Drift**: did I change anything outside the task scope? (Sneaky refactors, rename-while-you're-there, "drive-by" fixes.)

Step 3.6 without `git diff HEAD` is theatre — the agent can only honestly answer Q1/Q2 against an actual diff readout, not from "I remember what I changed".

Write a verdict to `mission_notes.md > Compliance Checks`:

```
- [Iter N] Task: "{name}"
  Diff files: [...]
  Q1: complete / partial / drift
  Q2: none / [list]
  Verdict: pass / needs-revision / escalate
```

| Verdict | Action |
|---|---|
| `pass` | Mark `[x]`. Proceed to Step 4. |
| `needs-revision` | Do NOT mark `[x]`. Append a sub-task under this task in the plan. Next iteration continues here. |
| `escalate` | Do NOT mark `[x]`. Feed Q1/Q2 answers into Step 3.5. |

### Step 4 — Checkpoint

(Reaching here implies build pass + Step 3.6 = pass + `[x]` now marked.)

- All tasks `[x]` and all Success Criteria `[x]`? → Phase 4 Debrief → Phase 5 Distill → 5-item Pre-Promise Audit.
- Otherwise → next iteration (back to Step 1).

---

## 4. Mid-iteration micro-audit (3 items, per task)

Before moving from one task to the next within the same mission, verify on **external evidence** (not LLM self-report):

1. The build / test command actually ran in this conversation, and its output shows pass. (Not "I ran tests" without the command appearing.)
2. `mission_notes.md > Compliance Checks` has a verdict entry for this iteration. Probe:
   - Bash: `grep -n "Iter $N" _planning/mission_notes.md`
   - PowerShell: `Select-String -Path _planning/mission_notes.md -Pattern "Iter $N"`
3. `mission_plan.md > Progress Log` has a new row for this iteration AND the corresponding task's `[ ]` is now `[x]`. (Both, not just the row.)

Failing any of these means the iteration is *not actually complete*. Do not advance.

This is the small-scale analog of §5's Pre-Promise Audit. The reason it exists: most LLM hallucination of completeness happens *between* tasks, not at final promise time. Catching it per-iteration is much cheaper than catching it at the end.

---

## 5. Pre-Promise Audit — before `<promise>Mission Accomplished</promise>`

All 5 must pass. Items 3 / 4 / 5 are external signals that cannot be hallucinated.

| # | Check | Source | Concrete probe |
|---|---|---|---|
| 1 | Every `- [ ]` (including indented sub-tasks) in `mission_plan.md` is now `[x]` | plan file | Bash: `grep -cE "^\s*- \[ \]" _planning/mission_plan.md` → 0; PowerShell: `(Select-String -Path _planning/mission_plan.md -Pattern '^\s*- \[ \]').Count` → 0 |
| 2 | All Success Criteria are `[x]` | plan file | Scan the Success Criteria block (same probe as #1, scoped to that block) |
| 3 | `git diff --stat` shows a non-empty diff vs base | **git** | At least 1 file modified/added (same command both shells) |
| 4 | Latest Progress Log row references real build output | command output | A row containing `verified: pass` or equivalent. Bash: `tail -n 5 _planning/mission_plan.md \| grep -F "verified: pass"`; PowerShell: `Get-Content _planning/mission_plan.md -Tail 5 \| Select-String -SimpleMatch "verified: pass"` |
| 5 | At least one lesson file exists under today's archive folder | **filesystem** | Bash: `ls ~/.claude/mission-archive/{slug}/lessons/$(date +%Y-%m-%d)-*.md`; PowerShell: `Get-ChildItem "$env:USERPROFILE\.claude\mission-archive\{slug}\lessons\$(Get-Date -Format yyyy-MM-dd)-*.md"` |

The probes for items 1, 2, 4 are cross-shell; the agent picks the form matching its current shell tool. Items 3 and 5 are described above with explicit branches. **Do NOT mix Bash and PowerShell syntax** in the same probe call — the failure mode is silent (command-not-found gets logged to stderr but the agent may interpret an empty stdout as "0 matches" = pass, which silently bypasses the audit).

Any item fails → output Partial Report. Append failure + reason to `mission_notes.md > Audit Trail`. Do NOT issue the promise.

Item 5 is the firewall that prevents skipping Phase 5. Without it, cross-mission learning never accumulates and the next mission inherits nothing from this one.

---

## 6. Phase 5 — Distill (required before promise)

Once all Success Criteria are `[x]`:

1. **Derive slug** (same as Phase 0 step 1; do not re-derive, reuse the value cached at mission start):
   - Bash: `slug=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || pwd)" | tr '[:upper:]' '[:lower:]' | tr ' _' '--')`
   - PowerShell: `$root = (git rev-parse --show-toplevel 2>$null); if (-not $root) { $root = (Get-Location).Path }; $slug = (Split-Path -Leaf $root).ToLower() -replace '[ _]', '-'`
2. **Ensure archive directory exists**:
   - Bash: `mkdir -p ~/.claude/mission-archive/$slug/lessons/`
   - PowerShell: `New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\mission-archive\$slug\lessons"`
3. **Scan `mission_notes.md`** for lesson candidates from:
   - `Decisions Made` — which choice is worth reusing?
   - `Self-Reflections` — which failure root cause has cross-mission transferability?
   - `Compliance Checks` **where verdict = escalate** — which class of drift should future missions watch for? (Skip `needs-revision` verdicts; those usually self-resolve in the next iteration and don't represent a stable lesson.)
4. **Produce 1-3 lessons** — not more. Quality over quantity. Each lesson is `<= 150 words`.
5. **Write each as `{YYYY-MM-DD}-{topic-kebab}.md`** in the archive folder. **Collision protect** — if the file exists, suffix `-r2`, `-r3`, etc. Never silently overwrite.
6. **List the new files in `mission_notes.md > Distilled Lessons`** with a one-line summary each.

Full lesson schema (frontmatter, body shape, why 150 words is strict): [`references/file-templates.md`](references/file-templates.md) § "Lesson file format".

---

## 7. Escape Hatch (when the loop doesn't fit)

If the state-machine recommendation is wrong for the situation (path conflict, user override, requirement collapsed, evidence contradicts the plan), switch to free-form execution. Record the deviation in `mission_notes.md > Deviations & Reasons` with: trigger, original state, why, outcome.

**What the Escape Hatch does NOT excuse** — these are protocol-level, not state-machine suggestions:

1. **Rule 0** (Step 3.6 must still gate every `[x]`).
2. **Phase 5 Distill** (no lesson file → Pre-Promise Audit item 5 fails → no promise).
3. **5-item Pre-Promise Audit** (3 of them are external signals; bypassing them re-introduces self-report).

If the Escape Hatch concludes "this mission cannot be completed": output Partial Report, record `Outcome: abandoned` in Deviations & Reasons. Leave unchecked `[ ]` tasks in the plan for a future mission. Do NOT `<promise>` an abandoned mission.

Detailed state machine (full state graph, transitions, `workflow_state.json` schema): [`references/state-machine.md`](references/state-machine.md). Most missions don't need it.

---

## 8. Subagent strategy

Research phase is where subagents pay off most. Avoid burning main-conversation context on exploratory reads:

| Use case | Tool |
|---|---|
| Explore a module / find symbols / map data flow | `Task(subagent_type="Explore")` |
| Design an implementation approach | `Task(subagent_type="Plan")` |
| Review a specific diff | `Task(subagent_type="code-reviewer")` |

Anti-pattern: 10+ Grep/Read calls in the main conversation to "look around". Spawn one Explore subagent with a focused prompt and consume its structured report instead.

---

## 9. Quick-start prompt skeleton

For a quick mission invocation:

```
[MISSION RUNNER]

## Task
{description}

## Phase 0
Derive {slug} from `git rev-parse --show-toplevel` (or `pwd`) -> lowercase kebab-case.
Glob ~/.claude/mission-archive/{slug}/lessons/ for matching past lessons.
Create _planning/, write mission_plan.md (with Prior Lessons block) and empty mission_notes.md.

## Per iteration
Step 1 read plan + notes + Prior Lessons
Step 1.5 confidence (High / Medium / Low + one-line reason)
Step 2 execute one task (DO NOT mark [x])
Step 3 validate (build / lint / test)
Step 3.5 reflect if Step 3 failed
Step 3.6 compliance verdict {pass / needs-revision / escalate}
Step 4 if 3.6 = pass, NOW mark [x] -> next task or done

## Before next task
3-item micro-audit (see SKILL.md §4): build output / Compliance Check entry / [x] applied.

## Completion
5-item Pre-Promise Audit (see SKILL.md §5). All pass -> <promise>Mission Accomplished</promise>.
Any fail -> Partial Report + Audit Trail entry.
Phase 5 Distill is the precondition (Audit item 5).
```

The full standalone-agent prompt with every step expanded: [`references/prompt-template.md`](references/prompt-template.md).

---

## 10. Anti-patterns (diagnostic table)

| Symptom | Diagnosis |
|---|---|
| All checkboxes `[x]`, `git diff` empty | Rule 0 bypassed + Pre-Promise Audit item 3 skipped |
| `Distilled Lessons` section says "lessons distilled" but archive folder is empty | Pre-Promise Audit item 5 skipped |
| Same kind of error 3 iterations in a row | Step 3.5 escalation rule ignored ("Complex / 3rd time same error" → AskUserQuestion) |
| `<promise>Mission Accomplished</promise>` after 1 iteration of a 10-task plan | Step 4 "all tasks done?" check skipped |
| Iteration narrated in detail in chat but `mission_notes.md` untouched | mistaking chat scrollback for the audit trail; the file is the source of truth |
| Compliance Check verdict says `pass` but the diff has 200 lines outside the task scope | Step 3.6 Q2 not actually asked — only Q1 was checked |

---

## Background and theoretical roots

- **Filesystem as memory + Read-Before-Decide** — [Manus context engineering](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus).
- **Step 3.5 Self-Reflection structure** — [Reflexion (NeurIPS 2023)](https://arxiv.org/abs/2303.11366).
- **State-machine framing** — [LangGraph](https://www.langchain.com/langgraph) (advisory, not enforced).
- **Workflow shaping (deterministic backbone + autonomous pockets)** — [CrewAI Flows](https://docs.crewai.com/concepts/flows).

The combination of Compliance Check + Pre-Promise Audit + Phase 5 Distill is this skill's defense against LLM self-report drift. Each one fixes a real failure mode that came out of real mission runs; deeper notes in [`references/state-machine.md`](references/state-machine.md) § "Anti-hallucination design".
