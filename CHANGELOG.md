# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed (2026-05-24 — post v2-spine code review)

A 5-angle code review on the v2 spine rewrite surfaced 15 confirmed issues. All fixed in this pass:

**P0 — Rule 0 violations (silent regression to v1.0 self-report)**
- `README.md:78` ("Execute next [ ] task, mark [x]") and `references/prompt-template.md:11` ("mark immediately") both instructed marking [x] at Step 2 Execute — directly contradicting Rule 0. Both rewritten to require Step 3.6 verdict=pass before [x].
- `README_zh-CN.md` and `README_ja.md` had the same violation. Per user direction, **the zh-CN and ja README variants were deleted** — they had drifted from the English canonical version (state-machine diagrams missing compliance_check, Repository Structure missing references/, v1.0 Iteration Rules) and a 3-way sync was not maintainable. The English README is now the single source.
- The consolidated **Four Prohibitions / Five Mandates** tables were dispersed into prose during the v2 spine rewrite, leaving downstream docs (`prompt-template.md` still naming "Mandate 5", Escape Hatch cross-references) with no anchor to resolve to. Added an **"At-a-glance: the four prohibitions + five mandates"** digest section to SKILL.md immediately after Rule 0 — recovers the named anchors without re-bloating the body.

**P1 — Cross-file inconsistency**
- `references/prompt-template.md:629` pointed `workflow_state.json` schema readers at the Chinese section `## 工作流状态机 > 状态持久化` that the v2 rewrite deleted. Redirected to `references/state-machine.md "workflow_state.json schema (v2.2 canonical)"`.
- `references/prompt-template.md` §8 State Machine Best Practices diagram and `README.md` State Machine diagram both showed the v1.0 path `validate -> checkpoint`, missing the v1.1 `compliance_check` state. Both diagrams updated to show `validate(pass) -> compliance_check -> checkpoint_mark` with `[x]` annotated as applied only at `checkpoint_mark`.
- `README.md` Repository Structure listed only `prompt-template.md` under `references/`; updated to list all 6 (added `state-machine.md`, `self-reflection.md`, `confidence-check.md`, `file-templates.md`, `status-output.md`).
- SKILL.md Rule 0 section now carries an explicit cross-mapping note: "legacy docs and `references/prompt-template.md` call this **Mandate 5** / **[x] timing**. Same rule." — so the two vocabularies don't silently disagree.

**P1 — Behavior loss in v2 rewrite**
- **Phase 0 lesson-glob matching algorithm was missing** from all new files (the v1 SKILL.md had a concrete spec: parse frontmatter, ≥1 keyword OR description-substring match case-insensitive, cap at 5 hits). Added a full "Phase 0 — Initialization (one-shot, at mission start)" section to SKILL.md with: slug derivation (Bash + PowerShell), `mkdir -p _planning` cross-shell branches, the lesson-glob match algorithm with explicit threshold + cap, mission_plan.md / mission_notes.md write steps.
- **Pre-Promise Audit probes (item 1 grep, item 4 `verified: pass` grep) were Bash-only**, contradicting item 5 which already had both shells. All probes now carry explicit Bash + PowerShell forms, with a `Do NOT mix shells` warning. Same fix applied to §4 mid-iteration micro-audit item 2 (`grep -n` → added `Select-String` form) and §6 Phase 5 step 1 slug derivation (no longer just `basename $(pwd)`).
- **Step 3.6 Compliance Check** in the SKILL.md compact form jumped straight to Q1/Q2 without `git diff HEAD` retrieval, letting Q1/Q2 be answered from LLM memory — exactly the failure mode Step 3.6 exists to prevent. Restored the "(a) Collect 3 signals first: task description re-read + `git diff HEAD` + most recent Decisions Made entry; (b) Then ask 2 questions" structure from `prompt-template.md`.

**P1 — Schema gaps**
- `references/file-templates.md` Distilled Lessons template said `Source: Iter N (Decisions Made / Self-Reflections / Compliance Checks)` with no filter — but SKILL.md §6 step 3 requires "Compliance Checks where verdict = escalate only" (`needs-revision` verdicts self-resolve and shouldn't generate lessons). Added the filter to the template + a comment explaining the rationale.
- `references/file-templates.md` mission_plan.md template had no sub-task nesting example, leaving SKILL.md §3.6 `needs-revision` ("Append a sub-task under this task") with no schema. Added a 2-space-indent example. Also updated SKILL.md Pre-Promise Audit item 1 probe from `^- \[ \]` to `^\s*- \[ \]` so indented sub-tasks are caught (without this, a sub-task left open would silently pass audit item 1).

**P2 — Detail bugs**
- README.md "≤150-char" / "≤150-char reusable insights" (3 places) → "≤150-word" to match SKILL.md §6 step 4 and file-templates.md "Why the strict 150-word cap".
- `references/confidence-check.md` Medium band `(avg 3-4)` and High band `(avg >= 4)` overlapped at exactly 4.0. Bands made half-open: `Medium (3 <= avg < 4)` / `High (avg >= 4)`. Also added the **single-dimension override** rule (one dimension at 1-2 forces stop even when average is green) explicitly to confidence-check.md, with a note that the SKILL.md compact form does NOT capture this override.
- `references/state-machine.md` ASCII path diagram placed the `(simple_error / medium_error / complex_error)` annotation between `checkpoint_mark` and `checkpoint`, visually suggesting these transitions exited `checkpoint_mark`. They actually exit `self_reflection`. Diagram re-drawn with annotations on the correct source state.
- CHANGELOG fake link `[user-supplied post-mortem](https://github.com/sputnicyoji/mission-runner)` (pointed to repo root, not any post-mortem document) replaced with honest attribution to direct usage observation.

### Removed (2026-05-24 — non-English README variants)

`README_zh-CN.md` and `README_ja.md` were deleted. They had drifted significantly from `README.md` (v1.0 Iteration Rules, missing `compliance_check` in state-machine diagrams, missing 5 reference files in Repository Structure) and a 3-way sync was not being maintained. SKILL.md and references/* contain the canonical content for all consumers; CLI users go through README.md (English).

Also removed the language-switcher line `**English** | [简体中文](README_zh-CN.md) | [日本語](README_ja.md)` from README.md line 10. Note: the CHANGELOG and `docs/plans/2026-05-23-self-improvement.md` retain historical mentions of these files — those are records of past state and were not retroactively edited.

### Changed (2026-05-24 — v2 spine rewrite)

**SKILL.md compressed 1172 -> 300 lines (-74%); state-machine / Reflexion / 4-dim confidence detail moved to `references/`.**

Rationale: real-world use in Prism-OS (Runtime DAG Refactor mission, 5+ iterations) showed that ~70 % of the always-loaded SKILL.md body was being skipped at execution time. The state-machine YAML + ASCII graph + JSON schema (~250 lines) was documented as "advisory mode" and almost never maintained in practice. The 4-dimension confidence scoring table was being abbreviated to a one-line "Confidence: high/medium/low + why" by every iteration. The iteration-boundary ASCII templates were being replaced with a sentence or two. Long Reflexion records were overkill for simple typo / unused-var fixes.

The five concrete changes (based on direct usage observation in a multi-iteration Prism-OS refactor mission, not from any prior published post-mortem):

1. **Rule 0 promoted to the first section.** "A task is `[x]` only when (build pass) AND (Step 3.6 verdict=pass)" was previously buried in `Mandate 2 of five`. It is now the very first prose after the title, before activation conditions or philosophy — because it is the single rule that, if dropped, collapses the whole anti-hallucination design into ordinary self-report.
2. **Mid-iteration 3-item micro-audit added** (`SKILL.md` §4). The 5-item Pre-Promise Audit was the only place external signals were required, but it only fires at final promise time. Most LLM hallucination of completeness happens *between* tasks. The new 3-item micro-audit (build output exists in transcript / Compliance Check entry exists in notes / `[x]` actually applied) makes per-iteration transitions as honest as the final promise.
3. **Confidence Check simplified** to High / Medium / Low + one-line reason (compact form in SKILL.md). The 4-dimension structured form moved to `references/confidence-check.md`, reframed as the right tool for the narrow case where Low confidence needs a surgical AskUserQuestion to the user.
4. **State machine relocated** to `references/state-machine.md`. SKILL.md now has a 7-step compact loop + a 1-paragraph Escape Hatch summary that links to the deep doc. The advisory-mode philosophy + full state graph + JSON schema all live in the reference for the rare reader who needs them.
5. **Reflexion long-form moved** to `references/self-reflection.md`. SKILL.md keeps a 1-paragraph classifier (Simple / Medium / Complex-or-repeated) with a 4-row table; readers needing the full multi-paragraph reflection template and 3-item memory cap follow the link.

Background docs:
- `references/file-templates.md` — `mission_plan.md` + `mission_notes.md` + lesson schema in one place. SKILL.md links here instead of inlining 80 lines of templates.
- `references/status-output.md` — the verbose iteration-boundary ASCII templates, now flagged as optional for "high-visibility unattended runs".

What was NOT changed:
- `references/prompt-template.md` (the standalone-agent Standard Template) — already canonical, no rewrite needed.
- `examples/_planning/` — live samples remain authoritative.
- `Mandate 2` / `Mandate 4` / `Mandate 5` semantics — all preserved verbatim under Rule 0 + §5 Pre-Promise Audit + §6 Phase 5. No protocol-level behavior change.
- README files — already up-to-date with v1.1 protocol; not touched.

Backup: the original 1172-line SKILL.md is preserved at `SKILL.md.pre-v2-spine.bak` for reference / rollback. Delete after confirming v2 works.

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

### Fixed (2026-05-24 — post-review part 2)

Follow-up sweep after a second pass through the skill surface uncovered seven
more cross-file inconsistencies and protocol omissions:

**P0 — user-copying-paste hazards**
- **`references/prompt-template.md:56` `mkdir -p _planning` (Standard Template Phase 0 step 4) was Bash-only.** More severe than the SKILL.md occurrence fixed above, because this template is what users paste into `/ralph-loop:ralph-loop "..."` — the first command of every mission would error on PowerShell. Now carries Bash + PowerShell branches with explicit "do not mix" guidance.
- **SKILL.md `## 使用方式 > ### 方式二：手动调用` was a v1.0 leftover.** The pasted prompt skeleton lacked Step 1.5 / 3.5 / 3.6, told the agent to `mkdir -p _planning` (Bash-only), and instructed "Execute: 执行下一个 [ ] 任务，更新 [x]" — a direct violation of Mandate 5 (which restricts `[x]` to Step 3.6 verdict=pass after the v1.1 hardening). Replaced with a non-copyable v1.1 outline that explicitly points users to `references/prompt-template.md` Standard Template, with a warning that self-truncating the protocol drops the mission back into v1.0 "I claim done" mode.

**P1 — cross-file schema / orphan references**
- **`workflow_state.json` schema was defined three different ways.** SKILL.md L519 (v2.1 canonical) had `task_marked_done` / `compliance_verdict` / `confidence_scores` but no `mode`; `references/prompt-template.md` L610 had `mode` but none of the v1.1 fields; `examples/_planning/workflow_state.json` was a third partial overlap. Promoted SKILL.md to v2.2 canonical (adds `mode` as a first-class field, documents every field with semantics including the escape-hatch `"free_form"` value), then synced prompt-template and examples to the same shape. CHANGELOG L107 had claimed the schema was already updated; in reality only SKILL.md was touched.
- **`_planning/agent_outputs/` was an orphan reference** (prompt-template.md:75). The directory was never explained in SKILL.md, never written into, never read from. Deleted the line; replaced the surrounding "Optional" block with the canonical v2.2 init shape for `workflow_state.json`.
- **`## Deviations & Reasons` was referenced but never defined.** SKILL.md escape-hatch (L572) and prompt-template.md (L603) both say "append to mission_notes.md → `## Deviations & Reasons`", but the mission_notes.md template in SKILL.md, prompt-template.md, and examples all lacked that section header — an agent triggering the escape hatch would have nowhere to write. Added the section header (with format examples) to all three.

**P2 — protocol gaps**
- **Escape hatch said "agent recovers full autonomy" without scoping it.** SKILL.md L575-578 risked giving the LLM a "free_form = bypass everything" excuse — which would silently void the 5-item Pre-Promise Audit, the Phase 5 Distill prerequisite, and Mandate 5 ([x] timing). Added a CRITICAL subsection listing the three hard constraints that remain binding in `free_form` mode (with rationale: they are protocol-layer, not state-machine, so the state machine going quiet does not silence them), plus an explicit "abandon mission" exit path when completion truly isn't possible (write to `## Audit Trail` rather than issuing a fabricated promise).
- **The "迭代状态输出 (MUST)" template only listed v1.0 sections.** SKILL.md L344-356's "Notes Changes (本轮新增)" subtemplate enumerated Failures & Learnings / Research Findings / Decisions Made — none of the v1.1 sections (Compliance Checks, Self-Reflections, Distilled Lessons, Audit Trail, Deviations & Reasons). Added subsections for each so per-iteration visibility output actually surfaces v1.1 evidence.

### Fixed (2026-05-24 — post-review part 3)

Third-pass self-review surfaced four more issues — three were self-inflicted by
the part 2 sweep, and one was a v1.1 F11 omission missed by both part 2 and
the original hardening pass.

- **`references/prompt-template.md` Step 2 Execute still carried v1.0 `Mark task [x]` instruction.** F11 (v1.1 hardening) moved the `[x]` timing to Step 3.6 verdict=pass and updated SKILL.md Step 2 + Mandate 2, but the prompt-template variant was never touched. Step 2 (L120) and Step 3.6 (L154) inside the same file disagreed; pasting this template into a mission left the LLM with contradictory instructions about when to mark `[x]` — and the obvious "earlier is fine" reading silently regressed to v1.0 "I claim done" mode. Step 2 rewritten with explicit "Do NOT mark `[x]` yet (Mandate 5)" + rationale matching SKILL.md's framing.
- **`examples/_planning/workflow_state.json` `current_state` was inconsistent with the surrounding notes.** Part 2 set it to `"self_reflection"` because `compliance_verdict = "escalate"`. But the matching `mission_notes.md` entry reads "triggered Step 3.5 Self-Reflection; will revert test changes next iteration" — that's the medium-error path (`self_reflection → checkpoint`), where Self-Reflection has already been recorded and the agent is waiting for the next iteration. Corrected `current_state` to `"checkpoint"`; the trio `current_state=checkpoint` + `compliance_verdict=escalate` + `task_marked_done=false` now accurately depicts "task left as `[ ]`, next iteration loops back to read_before_decide".
- **Mandates section and Pre-Promise Audit section had no forward reference to Escape Hatch.** Part 2 added a back-reference from Escape Hatch's "hard constraints" subsection to Mandate 5 / Audit / Phase 5, but reading the Mandates / Audit sections top-down gave no signal that they survive `mode=free_form`. Added a short forward note at the end of "五大强制" and in the Pre-Promise Audit Checklist header so the linkage is bidirectional.
- **The abandon path wrote to `## Audit Trail` but the section header said "Pre-Promise Audit 失败记录" (audit attempt failure records).** Mismatch in semantics: abandon isn't an audit attempt that failed — there is no audit attempt. Reworked the abandon path so the authoritative reason lives in `## Deviations & Reasons` (`Outcome: abandoned`) and `## Audit Trail` only carries a one-line index referencing it (`No promise issued — abandoned, see Deviations & Reasons`). Both section headers updated to describe the new arrangement; the abandon path itself gains an explicit step-4 reminder to output a Partial Report instead of swallowing the situation in silence.

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
