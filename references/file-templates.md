# File Templates

Canonical templates for the three mission files + lesson archive entries. The `examples/_planning/` directory has live samples filled in; this file is the schema reference.

## `_planning/mission_plan.md`

```markdown
# Mission Plan

## Objective
[Single-paragraph statement of what success looks like, extracted from the user request.]

## Success Criteria
- [ ] [Concrete, verifiable outcome 1]
- [ ] [Concrete, verifiable outcome 2]
- [ ] Validation passed (build / lint / test)

## Context
- Module path: src/modules/xxx/
- Architecture layers touched: Data / Service / UI
- Constraints: [project-specific]

## Prior Lessons
[Phase 0 step 3 output. List lesson file names + full content of each lesson matched against this task.]
[If none matched: "(no historical lessons matched this task)"]

## Phases

### Phase 1: Research & Discovery
- [ ] Understand the full requirement
- [ ] Explore relevant existing code
- [ ] Identify dependencies and constraints

### Phase 2: Implementation
- [ ] [Concrete task 1]
- [ ] [Concrete task 2]
- [ ] [Concrete task 3]
  - [ ] [Sub-task added by Step 3.6 needs-revision verdict — indent with 2 spaces]
  - [ ] [Sub-tasks inherit the parent's open/closed state for audit purposes]

### Phase 3: Verification
- [ ] Build / lint
- [ ] Constraint check (project-specific)

## Progress Log

| Iteration | Phase | Actions Taken | Status |
|-----------|-------|---------------|--------|
| 0 | Init | Created planning structure | Done |
```

## `_planning/mission_notes.md`

Append-only. Sections may stay empty; do NOT delete a section because it's empty — it's a slot for future entries.

```markdown
# Mission Notes

## Research Findings
[Discoveries during exploration, with iteration tag.]

## Decisions Made
[Choices and rationale. Source of Phase 5 lesson candidates.]

## Failures & Learnings
[Build/test failures with root cause and what changed.]
- [Iter N] [what failed] -> [root cause] -> [what was changed]

## Self-Reflections
[Reflexion records — see references/self-reflection.md for format.]
[Max 3 retained; older ones are dropped or promoted to Decisions Made / lesson files.]

## Compliance Checks
[Step 3.6 verdict per build-pass iteration.]
- [Iter N] Task: "..."
  Diff files: [...]
  Q1 (completeness): complete / partial / drift
  Q2 (unintended changes): none / [list]
  Verdict: pass / needs-revision / escalate

## Clarifications
[User answers to Low-confidence AskUserQuestion calls.]
- [Iter N] Q: [the question]
  A: [user answer]
  -> Impact: [how this changes implementation]

## Open Questions
[Things noted but not yet decided.]

## Distilled Lessons
[Phase 5 output — list of files written to ~/.claude/mission-archive/{slug}/lessons/]
[Source-section filter (matches SKILL.md §6 step 3):
   - Decisions Made: any entry is a candidate.
   - Self-Reflections: any entry is a candidate.
   - Compliance Checks: ONLY `Verdict: escalate` entries — `needs-revision` verdicts usually
     self-resolve in the next iteration and don't represent a stable transferable lesson.]
- {YYYY-MM-DD}-{topic-kebab}.md
  "one-line summary"
  Source: Iter N (Decisions Made / Self-Reflections / Compliance Checks-escalate)

## Audit Trail
[Pre-Promise Audit failure records; also Escape-Hatch abandon cross-references.]
- [Iter N, Attempt M] Audit failed at item X (reason)
  -> Suggested action: ...
- [Iter N+1, Attempt 1] All 5 items passed -> promise issued
- [Iter N+2] No promise issued — abandoned, see Deviations & Reasons

## Deviations & Reasons
[Escape Hatch / state-machine deviation records. Empty if never triggered.]
- [Iter N] Trigger: {agent_confidence<0.3 / iteration>max / user:free_form / path_conflict}
  Original current_state: {state}
  New mode: free_form
  Reason: {why}
  Still-binding hard constraints: 5-item Pre-Promise Audit / Rule 0 ([x] timing) / Phase 5 Distill
  Outcome: completed / abandoned
```

## `_planning/workflow_state.json` (optional)

See `references/state-machine.md` for the canonical schema. Only maintain this file if you want crash-recovery; most missions don't need it.

## Lesson file format (cross-mission archive)

Path: `~/.claude/mission-archive/{project-slug}/lessons/{YYYY-MM-DD}-{topic-kebab}.md`

```markdown
---
name: {topic-kebab-case}
description: One-line description used by Phase 0 step 3 fuzzy-match against the next mission's task description.
mission_date: YYYY-MM-DD
keywords: [keyword1, keyword2, ...]
---

# Lesson: {one-line core insight}

**Context:** {brief background of the mission that produced this lesson}

**Lesson (<= 150 words):**
{The actually-transferable insight, not an action checklist.}
{Frame as "next time you see situation X, try Y" — emphasize transferability.}

**Source:** Iter N, from {Decisions Made / Self-Reflections / Compliance Checks}
```

### Why the strict 150-word cap

Phase 0 step 3 of a *future* mission injects matched lessons into `mission_plan.md > Prior Lessons`. Long lessons pollute the next mission's prompt. If a lesson genuinely needs more than 150 words, that's a signal it's actually multiple lessons mixed together — split into separate files instead of cramming.

### Slug derivation rule (consistent across Phase 0 and Phase 5)

- Inside a git repo: `git rev-parse --show-toplevel` → take basename → lowercase + kebab-case.
- Outside a git repo: `pwd` → take basename → lowercase + kebab-case.
- Do NOT `cd` — just read the command output, keep cwd as-is.

Examples:
- `E:\Yoji\Prism-OS` → `prism-os`
- `/Users/foo/My App` → `my-app`

### Collision protection (required)

When writing a lesson, check if `{YYYY-MM-DD}-{topic-kebab}.md` already exists.

- Not present → write as is.
- Already present → suffix `-r2`, then `-r3`, etc. until a free name is found.

Two same-day missions producing the same topic can otherwise silently overwrite each other, losing the second lesson's nuance.
