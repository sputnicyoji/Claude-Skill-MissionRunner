# State Machine (optional deep reference)

> Most missions never need to read this file. The compact loop in `SKILL.md` §3
> is sufficient. Read here only if you (a) need crash-recovery via
> `workflow_state.json`, (b) want to understand why the loop has the exact
> shape it has, or (c) are extending the skill.

## Philosophy: Advisory, Not Mandatory

The state machine is a **navigation map, not rails**:

- It recommends a path; the agent may deviate when conditions demand.
- Deviations are logged (so a future review can understand the path actually taken).
- Protocol-level hard constraints (Rule 0, Phase 5 Distill, 5-item Audit) are NOT part of the state machine — they live above it and are not relaxed by deviation.

When to deviate:
- Agent confidence conflicts with the recommended next state.
- A more efficient path is visible from current evidence.
- The user explicitly skips a step.
- External environment changed (e.g., target code was modified by another process).

## States (compact)

```yaml
name: mission-runner-pir
version: "2.2"

states:
  init:                  next: read_before_decide
  read_before_decide:    next: confidence_check
  confidence_check:
    transitions:
      high:   execute
      medium: execute    # with recorded concern
      low:    ask_user
  ask_user:              next: confidence_check    # re-evaluate after answer
  execute:               next: validate            # SKILL.md Step 2 — do NOT mark [x] here
  validate:
    transitions:
      pass: compliance_check
      fail: self_reflection
  compliance_check:                                # SKILL.md Step 3.6 — the [x] gate
    transitions:
      pass:           checkpoint_mark
      needs_revision: read_before_decide           # do not mark [x]; next iteration retries
      escalate:       self_reflection              # treat as medium error
  self_reflection:                                 # SKILL.md Step 3.5
    transitions:
      simple_error:  execute        # immediate retry, same iteration (max 2)
      medium_error:  checkpoint     # log, do not mark [x], next iteration
      complex_error: ask_user
  checkpoint_mark:       next: checkpoint           # NOW [x] is marked
  checkpoint:                                       # SKILL.md Step 4
    transitions:
      all_tasks_complete: debrief
      continue:           read_before_decide
      max_iterations:     report
  debrief:               next: distill              # Phase 4 — confirm Success Criteria
  distill:               next: audit                # Phase 5 — write lesson files
  audit:                                            # 5-item Pre-Promise Audit
    transitions:
      all_pass: done
      any_fail: report                              # Partial Report + Audit Trail entry
  done:                  output: "<promise>Mission Accomplished</promise>"
  report:                output: "Partial Report with remaining work and audit failures"
```

## Path diagram

```
init
  v
read_before_decide <----------------------------+
  v                                              |
confidence_check --(low)--> ask_user             |
  | (high/medium)              | (answered)      |
  v <-------------------------+                  |
execute                                          |
  v                                              |
validate --(fail)--> self_reflection             |
  | (pass)                |                      |
  v                       | (simple_error)       |
compliance_check          | -> execute (retry <=2)
  | (pass)                | (medium_error)
  | (escalate) -----------+ -> checkpoint (next iter)
  v       (needs_revision) ----------------------+
  v                       | (complex_error)
checkpoint_mark           | -> ask_user
  v   [x] applied here, never earlier
checkpoint
  | (all_tasks_complete)
  v
debrief
  v
distill   (writes ~/.claude/mission-archive/{slug}/lessons/*.md)
  v
audit (5 items)
  | (all_pass)         | (any_fail)
  v                    v
done                report
```

The `(simple_error / medium_error / complex_error)` transitions all exit `self_reflection` — none of them exit `checkpoint_mark`, which has a single unconditional `-> checkpoint` transition. (Earlier versions of this diagram placed the annotation between `checkpoint_mark` and `checkpoint`, suggesting the wrong source state.)

Reading paths:

- **Ideal**: init -> read -> confidence -> execute -> validate(pass) -> compliance(pass) -> mark[x] -> checkpoint -> debrief -> distill -> audit(pass) -> done
- **Build failed**: validate(fail) -> self_reflection -> execute(retry) OR checkpoint(next iteration)
- **Goal drift**: compliance(escalate) -> self_reflection -> same as build failed
- **Small rework**: compliance(needs_revision) -> NO [x] -> read (next iteration continues same task)

## workflow_state.json schema (v2.2 canonical)

Optional. Use only if you want crash recovery — most missions don't need it. The single source of truth for this schema lives here; `references/prompt-template.md` and `examples/_planning/workflow_state.json` must match.

```json
{
  "current_state": "compliance_check",
  "iteration": 2,
  "retry_count": 0,
  "phase": "implementation",
  "task_index": 3,
  "task_marked_done": false,
  "compliance_verdict": null,
  "mode": "advisory",
  "confidence_scores": {
    "understanding": 5,
    "certainty": 4,
    "dependencies": 4,
    "risk": 4
  },
  "timestamp": "2026-05-23T15:30:00Z"
}
```

Fields:

- `current_state`: one of `init / read_before_decide / confidence_check / ask_user / execute / validate / compliance_check / self_reflection / checkpoint_mark / checkpoint / debrief / distill / audit / done / report`
- `iteration`: current iteration number. Phase 0 init is 0; first entry to Step 1 is 1.
- `retry_count`: Step 3.5 immediate-retry counter for this iteration (cap: 2).
- `phase`: `initialization / research / implementation / verification / debrief / distill`.
- `task_index`: 0-based index within the current Phase.
- `task_marked_done`: ONLY true after Step 3.6 verdict=pass.
- `compliance_verdict`: most recent Step 3.6 result — `null / "pass" / "needs-revision" / "escalate"`.
- `mode`: `"advisory"` (default) / `"free_form"` (Escape Hatch — state machine paused, but protocol-level hard constraints still apply).
- `confidence_scores`: only filled in Step 1.5 Low-confidence cases that need a structured AskUserQuestion (see `confidence-check.md`).
- `timestamp`: ISO 8601, updated on every state transition.

## Escape Hatch

When the state machine doesn't fit the situation, switch to free-form execution. Trigger conditions:

- Agent confidence is below a threshold and asking the user is not productive.
- Iteration count exceeds the planned max.
- User explicitly requests free-form mode.
- Recommended path conflicts with observable reality.

What happens:

- `mode` flips to `"free_form"`; `current_state` stops updating.
- mission_plan.md remains the goal reference.
- On exit, append one entry to mission_notes.md > Deviations & Reasons (trigger, original state, why deviated, outcome).

What the Escape Hatch does NOT excuse (these are protocol-level, not state-machine suggestions — they appear in `SKILL.md` § "Rule 0" and § "Pre-Promise Audit"):

| Hard constraint | Reason it cannot be bypassed |
|---|---|
| `[x]` timing (Rule 0) | `[x]` is the synthesis of "build pass + Compliance pass". Bypassing it lets LLM self-report drift back in. |
| Phase 5 Distill | Cross-mission learning's production end. Skipped = next missions get no Prior Lessons. |
| 5-item Pre-Promise Audit | Items 3/4/5 are external signals (git, command output, filesystem); item 5 transitively depends on Phase 5. |

If the Escape Hatch concludes "this mission cannot be completed":

1. Append `Outcome: abandoned` to mission_notes.md > Deviations & Reasons (authoritative record).
2. Append a cross-reference line to mission_notes.md > Audit Trail: `[Iter N] No promise issued — abandoned, see Deviations & Reasons`.
3. Leave unmarked `[ ]` tasks in mission_plan.md as-is, so a future mission can pick up.
4. Output Partial Report (NOT `<promise>Mission Accomplished</promise>`).

## Anti-hallucination design (why this skill looks like it does)

The bedrock fact: an LLM saying "I did X" is not evidence that X happened. Common observed failure modes:

- All checkboxes `[x]`, but `git diff --stat` is empty.
- "Phase 5 complete, lessons distilled" — but the archive directory is empty.
- "Tests pass" — but no test command was actually run in the transcript.

The skill defends against this with external signals that cannot be hallucinated:

- **Rule 0** ties `[x]` to a real build output AND a structured diff review (Step 3.6).
- **Mid-iteration micro-audit** (`SKILL.md` §4) makes per-task transitions as honest as the final promise.
- **Pre-Promise Audit items 3/4/5** require git state, real command output, and filesystem state respectively.
- **Phase 5 Distill + Audit item 5** force the lesson files to physically exist before any promise is allowed.

If you ever feel tempted to "simplify" by dropping one of these, look at the symptom it prevents (see `SKILL.md` § "Anti-patterns"). Each one is a fix for a real observed failure mode.
