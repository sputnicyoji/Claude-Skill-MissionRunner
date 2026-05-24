# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed (2026-05-24)

**Cursor support dropped**
- Deleted `.cursorrules`, `.cursor/rules/mission-runner.mdc`, `.cursor/rules/mission-runner-lite.mdc`, and the now-empty `.cursor/` directory.
- README.md / README_zh-CN.md / README_ja.md: Cursor badge, Cursor installation section, Cursor entries in Repository Structure, and Cursor acknowledgement removed.
- **Rationale**: the Cursor rule files were never updated to the v1.1 protocol (Compliance Check, Pre-Promise Audit, Phase 5 Distill, Prior Lessons glob, Mandates 4/5). Maintaining a v1.0 fork in the same repo was a long-standing inconsistency — see the "v1.0 → v1.1 sync-pending banners" entry in the v1.1 Hardening Pass below. The right move was to delete the half-supported variant rather than ship a permanently stale alternate skin.
- Going forward the skill targets Claude Code only.

### Fixed (2026-05-24)

- **SKILL.md Phase 0 step 4 `mkdir -p _planning` broke on PowerShell.** Phase 5.2 already split this into Unix-like vs PowerShell forms (F21 in the v1.1 hardening pass), but Phase 0 step 4 was missed in the same sweep. Now matches Phase 5.2 with both shell variants and an explicit "do not mix" note. Without the fix, the very first command of a mission would error out (`A positional parameter cannot be found`) on Windows.
- **SKILL.md `Task(subagent_type=...)` shown as Python code.** The Tool Selection Strategy section rendered subagent invocations as Python function calls — a representation that risks the agent serialising them as text strings rather than issuing actual `Task` tool calls. Rewritten as a neutral field-mapping description ("call Task tool, set `subagent_type` to ...") with an explicit warning not to emit the lines as string output.
- **`examples/_planning/workflow_state.json` timestamp 2024-01-15 contradicted `mission_plan.md` (2026-05-15 lesson reference, Iter 4 in progress).** Bumped to `2026-05-15T15:30:00Z` so the three example files share one timeline.

### Added

**Cross-mission learning layer (Task 3B — Phase 0 historical lesson glob, consumer side)**
- **Phase 0 step 2 — `{project-slug}` derivation** at mission start (in addition to Task 3A's Phase 5 derivation), unifying namespace use across producer and consumer sides.
- **Phase 0 step 3 — historical lesson glob**: read all `*.md` frontmatter in `~/.claude/mission-archive/{slug}/lessons/`, match `keywords[]` and `description` against current task description (case-insensitive substring), cache up to 5 hits with full lesson body. Skips silently when directory doesn't exist (first mission for the project).
- **`## Prior Lessons` section in mission_plan.md template** (between Context and Phases). Populated by Phase 0 step 3; written as `(no historical lessons matched this task)` when there are no hits.
- **Step 1 Read-Before-Decide** now explicitly reads `## Prior Lessons` and feeds triggered lessons into Step 1.5 Confidence Check (lessons that warned about a known trap should lower Solution Certainty / Risk Assessment scores).
- **Step 1 Read-Before-Decide** also checks `Compliance Checks` and `Audit Trail` (introduced in Task 1/2/3A) so previous-iteration evidence informs the next decision.
- Closes the cross-mission learning loop: Task 3A produced lessons (production side); Task 3B consumes them (consumer side).

**Cross-mission learning layer (Task 3A — Phase 5 Distill)**
- **Phase 5: Distill** — new phase after Phase 4 Debrief, runs as a HARD prereq for `<promise>Mission Accomplished</promise>`. Scans this mission's `Decisions Made`, `Self-Reflections`, `Compliance Checks (verdict != pass)` and produces 1-3 reusable lessons (each ≤150 chars) written to `~/.claude/mission-archive/{project-slug}/lessons/{YYYY-MM-DD}-{topic}.md`.
- **Lesson file structure** — frontmatter (`name`, `description`, `mission_date`, `keywords`) + `# Lesson:` headline + `Context` + `Lesson (≤150 字)` body + `Source: Iter N` provenance. Documented in SKILL.md `## 文件结构` section.
- **`{project-slug}` derivation rule** — `git rev-parse --show-toplevel` last segment, lowercase + kebab-case; falls back to `pwd` basename when not in a git repo.
- **`## Distilled Lessons` section in mission_notes.md template** (between Open Questions and Audit Trail), recording the lesson files produced this mission with one-sentence summaries.

**Goal-drift detector (Task 2 — Step 3.6 Compliance Check)**
- **Step 3.6 Compliance Check (Build Pass Path)** — prompt-level self-check inserted between Step 3 Validate (pass) and Step 4 Checkpoint. After build/lint/test passes, the agent collects 3 signals (current `[ ]` task description + `git diff HEAD` + most recent `Decisions Made` entry) and self-asks 2 questions in the main conversation (no subagent needed):
  - Q1: Does the diff fully implement the task? (functionality ≈ task description, not just "compiles")
  - Q2: Are there unplanned side changes? (goal drift signal — out-of-scope file edits, unrequested refactoring, "while I was at it" fixes)
- Structured Verdict written to `mission_notes.md > Compliance Checks`: `pass` / `needs-revision` / `escalate`.
- Verdict branching: `pass` → Step 4; `needs-revision` → don't mark task `[x]`, add correction subtask, next iteration; `escalate` → treat as medium error, route into Step 3.5 Self-Reflection with Q1/Q2 answers as input.
- **`## Compliance Checks` section in mission_notes.md template** (between Self-Reflections and Clarifications).

**Anti-hallucinated-completion gate (Task 1 — Pre-Promise Audit Checklist)**
- **Pre-Promise Audit Checklist (5-item gate)** before outputting `<promise>Mission Accomplished</promise>`:
  1. All `- [ ]` tasks in mission_plan.md marked `[x]` (internal signal)
  2. All Success Criteria marked `[x]` (internal signal)
  3. `git diff --stat` shows non-empty changes (**external signal** — strongest anti-hallucination check, LLM cannot fabricate)
  4. Build/lint/test executed and passed, traceable in Progress Log (external signal)
  5. Phase 5 Distill produced at least 1 lesson file in `~/.claude/mission-archive/{slug}/lessons/` (**external signal** — filesystem state; closes the cross-mission learning loop)
- **`## Audit Trail` section in mission_notes.md template**, recording rejected promise attempts and the audit failures that triggered them.
- **Partial Report fallback**: when any audit item fails, output Partial Report listing the failed item + reason + next step instead of false promise.

**Mandates (SKILL.md MUST section)**
- **强制4 (Mandate 4)**: must pass all Pre-Promise Audit items before promise.
- **强制5 (Mandate 5)**: must run Step 3.6 Compliance Check after every build pass; `[x]` marking forbidden when Verdict ≠ pass.

### Changed
- SKILL.md Phase 0 expanded from 5 steps to 7 steps (Task 3B): adds step 2 `project-slug` derivation, step 3 historical lesson glob, and step 5 now creates `mission_plan.md` with a `## Prior Lessons` section populated by step 3.
- SKILL.md Step 1 Read-Before-Decide gains explicit Prior Lessons / Compliance Checks / Audit Trail reads (Task 3B).
- `references/prompt-template.md` Standard Template Phase 0 mirrors SKILL.md's new 6-mandatory + 2-optional layout.
- `references/prompt-template.md` Step 1 in iteration rules mirrors SKILL.md's Prior Lessons + Compliance Checks + Audit Trail reads.
- `references/prompt-template.md` mission_plan.md template gains `## Prior Lessons` section between Context and Phases.
- SKILL.md `## 三大强制` heading bumped through `四大` (Task 1) → `五大` (Task 2) to track new mandates.
- SKILL.md Pre-Promise Audit Checklist: 4-item gate (Task 1) → 5-item gate (Task 3A); rationale paragraph extended to cover items 3/4/5; item 5 hard-prereq rationale added.
- SKILL.md Step 3 Validate ASCII frame: `如无错误 -> 跳过 Step 3.5` changed to `如无错误 -> 进入 Step 3.6 Compliance Check`.
- SKILL.md Step 4 Checkpoint ASCII diagram now branches through audit before issuing promise.
- `references/prompt-template.md` Completion Criteria section rewritten to require 5-item audit (replacing the looser "all [ ] marked + builds successfully" check).
- `references/prompt-template.md` Step 4 in iteration rules: added preamble `(Reaching here implies Step 3.6 Compliance Check verdict was pass)` and routes promise through Pre-Promise Audit Checklist.

### Fixed (Hardening Pass — 2026-05-23)

Following an extra-high effort recall-mode code review that surfaced 15 verified findings across the v1.1 changes, the following fixes landed in a single hardening commit:

**Critical flow / structural bugs**
- **F13 — Phase 5 trigger flow unreachable**: Phase 5 Distill was positioned AFTER Phase 4 Debrief but Pre-Promise Audit item 5 (which gates the promise) requires Phase 5 to have already run. The workflow never instructed the agent to enter Phase 5 prior to the audit, deadlocking any iteration that reached "all tasks complete". Fixed by inlining the sequence `Phase 4 Debrief → Phase 5 Distill → Pre-Promise Audit` into Step 4 Checkpoint's "all done" branch.
- **F11 — `[x]` timing contradiction between Mandate 2 and Mandate 5**: Step 2 Execute marked `[x]` immediately, but Mandate 5 required Verdict=pass before `[x]`. Fixed by moving the `[x]` mark from Step 2 to Step 3.6 verdict=pass branch; Mandate 2 reworded; Step 2 ASCII updated. `[x]` is now the composed signal of "code runs (Step 3) + functionality matches plan (Step 3.6)" rather than a verbal claim.
- **F4 — Step 3.5 trigger silently missed `Step 3.6 escalate` caller**: Self-Reflection box only documented "Step 3 validation fails" as the trigger, even though Step 3.6 explicitly routes `escalate` verdicts to Step 3.5. Fixed by listing both triggers (a) build/lint/test fail, (b) Step 3.6 escalate.

**Numeric / count drift after audit grew from 4 to 5 items (F1, 5 sites)**
- `SKILL.md` Mandate 4 `4 项` → `5 项`.
- `SKILL.md` Step 4 Checkpoint ASCII `(4 项)` / `4 项全通过` → `(5 项)` / `5 项全通过`.
- `references/prompt-template.md` Step 4 `(4 items, see SKILL.md)` → `(5 items, see SKILL.md)` and `All 4 pass` → `All 5 pass`.
- `references/prompt-template.md` Completion Criteria `ALL 4 Pre-Promise Audit items pass` → `ALL 5 ...`; added item 5 enumeration.
- `references/prompt-template.md` Audit Trail example `All 4 items passed` → `All 5 items passed`.

**Template completeness (F2, F3, S1, S2)**
- `SKILL.md` inline `mission_notes.md` template: added missing sections `## Compliance Checks` (Task 2), `## Distilled Lessons` (Task 3A), `## Audit Trail` (Task 1).
- `SKILL.md` inline `mission_plan.md` template: added `## Prior Lessons` section between Context and Phases.
- `examples/_planning/mission_plan.md`: added populated `## Prior Lessons` example (with a sample lesson hit).
- `examples/_planning/mission_notes.md`: added `## Compliance Checks` (with pass + escalate examples), `## Distilled Lessons`, `## Audit Trail` sections.

**Placeholder / shell / Phase 5 hardening (F7, F18, F19, F15, S8)**
- F7 `{today}` placeholder unbound → audit item 5 now defines `TODAY = ISO date` and provides both Bash and PowerShell command forms.
- F18 lesson filename collision → Phase 5.4 gains mandatory collision guard: pre-write `ls` check, on conflict rename to `{date}-{topic}-r2.md` / `-r3.md` etc.
- F19 `Verdict ≠ pass` ambiguity → Phase 5.3 now scans `Verdict = escalate` only (needs-revision is transient, not stable lesson material).
- F15 + S8 — Phase 5.1 silently `cd`'d to git root and had a weaker slug normalization than Phase 0 → Phase 5.1 rewritten to (a) NOT cd (just read `git rev-parse` output), (b) explicitly apply `lowercase + kebab-case` to both git and no-git fallback, matching Phase 0 step 2 exactly.
- F21 — Phase 5.2 mkdir command Windows compatibility → split into explicit `Unix-like (Bash/zsh)` and `Windows PowerShell` forms with a note "agent should select based on shell tool type; do not mix".

**State machine modernization (S6)**
- `SKILL.md` State Machine YAML bumped to v2.1: added states `compliance_check`, `checkpoint_mark`, `debrief`, `distill`, `audit`; `validate.pass` now routes to `compliance_check` (was `checkpoint`); `checkpoint.all_tasks_complete` now routes to `debrief` (was `done`).
- ASCII visualization replaced with a simpler arrow-flow diagram covering all new states (the old box-drawing diagram was harder to maintain and had alignment drift).
- `workflow_state.json` schema example updated with new fields (`task_marked_done`, `compliance_verdict`); valid `current_state` enumeration documented.

**Scenario template simplification (F9)**
- `references/prompt-template.md` Scenarios 1/2/3 no longer duplicate (stale) Phase 0 / Iteration Rules / Completion Criteria. Each scenario now contains only domain-specific Task Breakdown + Constraint Reminders, with an explicit banner instructing users to compose against the Standard Template at the top of the file (which carries the canonical 7-step Phase 0, full Iteration Rules including Step 3.6, and 5-item Completion Criteria).

**Discovery surface (S3, S4, S5)**
- `README.md`: Key Features table gains rows for Compliance Check / Pre-Promise Audit / Phase 5 Distill + archive. Core Workflow diagram updated to show the v1.1 flow including Step 3.6, Phase 5, and the 5-item audit gate.
- `README_zh-CN.md`: synced with README.md (Key Features + Core Workflow translated).
- `README_ja.md`: Key Features gains v1.1 rows (translated); a notice section directs Japanese readers to `SKILL.md` and English `README.md` for canonical v1.1 spec (Core Workflow diagram in this file remains at v1.0 wording pending a proper translation pass). *(Resolved 2026-05-24: Core Workflow translated to v1.1; v1.0 fallback notice removed. See the "Cursor support dropped" Removed entry at the top of this section.)*
- `.cursorrules`, `.cursor/rules/mission-runner.mdc`, `.cursor/rules/mission-runner-lite.mdc`: added prominent v1.0 → v1.1 sync-pending banners pointing Cursor users to `SKILL.md` for canonical v1.1 spec. Cursor rule file rewrite is tracked as future work. *(Resolved 2026-05-24 by deletion: Cursor support dropped rather than re-synced; see the Removed entry at the top of this section.)*

**Other (F5, F6)**
- F5 — `references/prompt-template.md` Step 4 preamble previously asserted "Reaching here implies Step 3.6 verdict=pass", which is false on the Step 3 fail → Step 3.5 medium → Step 4 path. Reworded to "Reached on either path: (a) Step 3.6 verdict=pass and `[x]` just marked, or (b) Step 3.5 medium error returning to checkpoint with task left as `[ ]`".
- F6 — `references/prompt-template.md` Completion Criteria item 3 (`git diff --stat` must show changes) previously rejected verify-only missions whose deliverable is empty diff. Added explicit waiver clause: item 3 may be waived IF mission_plan.md Success Criteria explicitly declares "no code change expected"; waiver must be recorded in Audit Trail.

### Removed
- **RiderMcp legacy purge**: removed Kotlin Plugin / Unity / PSI / TypeScript Bridge specific content inherited from a previous incarnation of this skill. Affected:
  - `SKILL.md` frontmatter description (removed the "RiderMcp projects" activation line)
  - `SKILL.md` "RiderMcp Project-Specific Error Patterns" section (9 Kotlin/Unity error categories)
  - `SKILL.md` "RiderMcp Project-Specific Validation" section (gradle build / Plugin Verifier / Rider 2025.3.1 notes)
  - `references/error-patterns.md` (entire file, 9 Kotlin/Unity error pattern templates)
  - `references/ridermcp-constraints.md` (entire file)
- **Rationale**: mission-runner is a general-purpose multi-file automation skill; the RiderMcp content was context noise in non-RiderMcp projects (every skill activation injected unrelated concepts like ReadAction, WriteCommandAction, Unity Play mode).

## [1.0.0] - 2024-01-15

### Added

- Initial public release
- **Core PIR Methodology**
  - Filesystem as Memory - persistent state using `_planning/` directory
  - Read-Before-Decide - goal anchoring before each iteration
  - Failures as Data - structured failure recording for learning

- **Confidence Check Protocol**
  - 4-dimension assessment (Understanding, Certainty, Clarity, Risk)
  - Automatic decision routing based on confidence level
  - User clarification flow for low-confidence scenarios

- **Self-Reflection Protocol (Reflexion)**
  - Based on NeurIPS 2023 Reflexion paper
  - Semantic gradient learning from failures
  - Error classification (Simple/Medium/Complex)
  - Max 3 reflection memory management

- **Advisory State Machine**
  - Guided workflow with clear state transitions
  - Escape hatch mechanism for flexibility
  - State persistence for interrupt recovery

- **Multi-Platform Support**
  - Claude Code: `SKILL.md` + `references/`
  - Cursor: `.cursorrules` + `.cursor/rules/*.mdc`

- **Documentation**
  - Comprehensive SKILL.md for Claude Code
  - Full and lite versions for Cursor
  - Prompt templates with scenario examples
  - Example planning files

### Theoretical Foundations

- Manus AI Context Engineering
- Reflexion (NeurIPS 2023)
- CrewAI Flows
- LangGraph State Machine

---

## Future Roadmap

### Planned for v1.1.0

- [ ] Enhanced parallel execution support
- [ ] Tool registry integration
- [ ] More scenario templates

### Planned for v2.0.0

- [ ] Multi-agent composition
- [ ] Cross-session memory
- [ ] Analytics and metrics
