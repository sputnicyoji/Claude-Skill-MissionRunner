# Status Output — Long Form (optional)

> The compact form in `SKILL.md` §3 (one or two natural-language sentences
> at iteration boundaries) is the default. Use this verbose ASCII-art form
> only when the user explicitly wants high-visibility progress reporting —
> for example, a long unattended run where the user will scroll the
> conversation to check progress later.

## Iteration-start template

```
====================================================================
ITERATION N | Read-Before-Decide
====================================================================

## Objective
[extracted from mission_plan.md]

## Current progress
Phase 1: Research [2/3 done]
- [x] Understand requirement
- [x] Explore code
- [ ] Identify constraints  <-- current task

Phase 2: Implementation [0/3 done]
- [ ] Task 1
- [ ] Task 2

## Confidence Check (current task)
| Dimension | Score | Note |
|---|---|---|
| Task understanding | 4 | Requirement is clear |
| Solution certainty | 3 | Two approaches under consideration |
| Dependency clarity | 5 | APIs explicit |
| Risk estimate | 4 | Blast radius manageable |
| **Average** | **4.0** | 🟢 proceed |

## Last iteration notes
- [Iter N-1] Found X, decided Y

====================================================================
```

## Iteration-end template

```
--------------------------------------------------------------------
ITERATION N | Checkpoint
--------------------------------------------------------------------

## This iteration
- Done: [what was completed]
- Hit: [problems / discoveries]
- Next: [next task]

## Updated progress
Phase 1: Research [3/3 done] DONE
Phase 2: Implementation [1/3 done]

## Notes changes (this iteration)
### Failures & Learnings
- [Iter N] TS2307: Cannot find module xxx
  -> Cause: missing path alias
  -> Fix: updated tsconfig.json paths
  -> Status: fixed

### Research Findings
- [Iter N] Found xxx module under yyy/

### Decisions Made
- [Iter N] Chose approach zzz because...

### Self-Reflections (this iteration's Step 3.5 output)
- [Iter N, Attempt 1] {error}
  Reflection: {root cause + improvement}
  Strategy: {fix inline / record / ask user}

### Compliance Checks (this iteration's Step 3.6 verdict)
- [Iter N] Task: "{name}"
  Verdict: {pass / needs-revision / escalate}

### Distilled Lessons (only when Phase 5 ran this iteration)
- {YYYY-MM-DD}-{topic-kebab}.md
  "one-line summary"

### Audit Trail (only on promise attempts)
- [Iter N, Attempt M] Audit item X failed (reason) / All 5 passed

### Deviations & Reasons (only when Escape Hatch fired)
- [Iter N] Trigger: ... -> mode=free_form, hard constraints still binding

--------------------------------------------------------------------
```

**Critical**: when using this template, the "Notes changes" section must show the actual *new* entries written this iteration, not just say "files updated". The whole point of the visible report is to externalize what would otherwise be invisible state changes.

## When NOT to use this

If the user is engaged with the conversation in real time, this verbose format becomes noise. The compact form ("Iter N done — built X, hit Y, next is Z") is better. Save the boxed templates for runs where:

- The user will scroll back through history to audit progress.
- The mission is long enough that a quick visual marker between iterations helps navigation.
- The runtime environment (Cowork, headless CI) can't open the eval viewer, so all visibility has to come from the chat log itself.
