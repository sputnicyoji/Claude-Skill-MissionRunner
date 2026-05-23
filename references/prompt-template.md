# Mission Runner Prompt Template (PIR Mode)

> Local file-based memory system based on PIR (Plan-Iterate-Resolve) methodology

## Core Principles

```
1. Filesystem as Memory   - Use _planning/ directory for persistent state
2. Read-Before-Decide     - Read mission_plan.md before each iteration
3. Failures are Data      - Record errors to mission_notes.md for learning
4. One Task at a Time     - Execute one task per iteration, mark immediately
5. Uncertainty is Signal  - Ask when unsure, never guess
6. Reflect-Before-Retry   - Reflect before retrying after failure (Reflexion)
7. Parallel-When-Possible - Research/Review can parallel, Implementation serial
8. State-Machine-Advisory - State machine is navigation advice, not enforcement
```

---

## Standard Template (Recommended)

```
/ralph-loop:ralph-loop "
===============================================================
                    [MISSION RUNNER - PIR MODE]
===============================================================

## Task Objective
{Clear description of the task to complete}

## Task Context
- Module path: {src/modules/xxx/}
- Architecture layers: {Data/Service/UI}
- Related skills/docs: {project-specific skills or documentation}

---------------------------------------------------------------
                    Phase 0: Initialization
---------------------------------------------------------------

1. Create planning directory: mkdir -p _planning

2. Create _planning/mission_plan.md:
   - Objective: Extract from task description
   - Success Criteria: Specific verifiable completion criteria
   - Phases: Phased task list
   - Progress Log: Empty table

3. Create _planning/mission_notes.md:
   - Research Findings: Empty
   - Decisions Made: Empty
   - Failures & Learnings: Empty
   - Self-Reflections: Empty
   - Clarifications: Empty
   - Open Questions: Empty

4. Create _planning/workflow_state.json (optional):
   {
     "current_state": "init",
     "iteration": 0,
     "phase": "initialization"
   }

5. Create _planning/agent_outputs/ directory (optional):
   mkdir -p _planning/agent_outputs

---------------------------------------------------------------
                    Iteration Rules (Must Execute Each Iteration)
---------------------------------------------------------------

### Step 1: Read-Before-Decide (Goal Anchoring)
Read _planning/mission_plan.md
- Confirm: What is the Objective?
- Confirm: Which Phase are we in?
- Confirm: What is the next incomplete [ ] task?

Read _planning/mission_notes.md
- Check: What failures/learnings from last iteration?
- Check: Previous Clarifications records

### Step 1.5: Confidence Check
Evaluate current task on 4 dimensions (1-5 scale):
| Dimension | Assessment Question |
|-----------|---------------------|
| Task Understanding | Are requirements fully clear? |
| Solution Certainty | Is the implementation approach unique and clear? |
| Dependency Clarity | Are APIs/classes to use clearly identified? |
| Risk Assessment | Are potential side effects controllable? |

Calculate average and decide:
- >= 4 (Green): Continue to Step 2
- 3-4 (Yellow): Record concerns in notes, continue Step 2
- < 3 (Red): AskUserQuestion, record to Clarifications

### Step 2: Execute
- Execute next [ ] task (one at a time!)
- Follow project constraints and related skill specs
- After completion, immediately update mission_plan.md:
  - Mark task [x]
  - Update Progress Log

### Step 3: Validate
- Check if code compiles/builds successfully
- If errors, enter Step 3.5 Self-Reflection
- If pass, enter Step 3.6 Compliance Check

### Step 3.6: Compliance Check (Build Pass Path)
**Trigger**: When Step 3 build/lint/test passes
**Goal**: Verify the diff actually implements the planned task (not just "code compiles")

1. Collect 3 signals:
   a. Current `[ ]` task description from mission_plan.md
   b. Current iteration's git diff (`git diff HEAD`)
   c. Most recent `Decisions Made` entry from mission_notes.md (if any)

2. Self-ask 2 questions (answer in main conversation, no subagent needed):
   Q1: Does this diff fully implement task (a)?
       (Not "compiles", but "functionality ≈ task description")
   Q2: Are there unplanned "side changes"? (goal drift signal)
       - Are all modified files within task scope?
       - Any unrequested refactoring / renaming / "while I'm at it" fixes?

3. Output Verdict to mission_notes.md > Compliance Checks:
   - [Iter N] Task: "{name}"
     Diff files: {list of files in git diff}
     Q1 (completeness): {complete / partial / drift}
     Q2 (side changes): {none / found - list}
     Verdict: {pass / needs-revision / escalate}

4. Branch on Verdict:
   - pass           -> proceed to Step 4
   - needs-revision -> do NOT mark task [x]; append correction subtask under
                       the task in plan; next iteration continues this task
   - escalate       -> treat as "medium error"; trigger Step 3.5 Self-Reflection
                       (feed Q1/Q2 answers as Reflection input)

### Step 3.5: Self-Reflection
**Trigger**: When Step 3 validation fails (or Step 3.6 escalates)

1. Generate reflection (2-3 sentences):
   - Why did it fail? (Root cause)
   - How to fix? (Specific solution)
   - Similar pitfalls? (Learn by analogy)

2. Decide based on error type:
   - Simple error (typo/import): Fix immediately, return to Step 2 (max 2 times)
   - Medium error (logic): Record reflection, proceed to Step 4
   - Complex error (architecture): AskUserQuestion

3. Update mission_notes.md:
   ## Self-Reflections
   - [Iter N, Attempt M] {error}
     Reflection: {cause + solution + pitfall}
     Strategy: {fix immediately / pending / waiting}
     Status: {fixed / next iteration / waiting}

### Step 4: Checkpoint
- (Reaching here implies Step 3.6 Compliance Check verdict was `pass`)
- Update Progress Log table
- Decide: All Success Criteria complete?
  - Yes -> run Pre-Promise Audit Checklist (4 items, see SKILL.md)
    - All 4 pass -> Output `<promise>Mission Accomplished</promise>`
    - Any fail   -> Output Partial Report + append result to `## Audit Trail`
  - No  -> Continue next iteration

---------------------------------------------------------------
                         Task Breakdown
---------------------------------------------------------------

List tasks by Phase:

### Phase 1: Research & Discovery
- [ ] {Understand requirements}
- [ ] {Explore existing code}

### Phase 2: Implementation
- [ ] {Task 1}
- [ ] {Task 2}
- [ ] {Task 3}

### Phase 3: Verification
- [ ] Build verification
- [ ] Constraint check

---------------------------------------------------------------
                        Completion Criteria
---------------------------------------------------------------

Output completion flag ONLY when ALL 4 Pre-Promise Audit items pass:

1. mission_plan.md: all `- [ ]` tasks marked `[x]`
2. mission_plan.md: all Success Criteria marked `[x]`
3. **External signal:** `git diff --stat` shows non-empty changes (LLM cannot fabricate this — strongest anti-hallucination check)
4. **External signal:** Build/lint/test commands actually executed and passed (traceable in Progress Log: must contain `verified: pass` or equivalent record for the latest entry)

If any of the 4 fails:
- Do NOT output `<promise>Mission Accomplished</promise>`
- Output Partial Report instead, including: which audit item failed, why, suggested next step
- Append the audit result to mission_notes.md `## Audit Trail` section

On full pass, output: <promise>Mission Accomplished</promise>

If max iterations reached without completion:
- Report completed tasks
- List remaining tasks
- Do NOT output Mission Accomplished
" --completion-promise "Mission Accomplished" --max-iterations 3
```

---

## Scenario Templates

### Scenario 1: Adding New Entity Type (Three-Layer Architecture)

```
/ralph-loop:ralph-loop "
[MISSION RUNNER - PIR MODE]

## Task Objective
Add refund functionality to the Order module in e-commerce system

## Task Context
- Module path: src/modules/order/
- Architecture layers: Data/Service/UI (three layers)
- Related skills: project-specific domain rules

## Phase 0: Initialization
1. mkdir -p _planning
2. Create mission_plan.md (with Success Criteria)
3. Create mission_notes.md

## Iteration Rules
1. Read-Before-Decide: Read _planning/mission_plan.md
2. Execute: Execute next [ ] task, mark [x] when done
3. Validate: Build verification, append errors to mission_notes.md
4. Checkpoint: Update Progress Log

## Task Breakdown
### Phase 1: Research
- [ ] Review existing Order/Payment implementation patterns

### Phase 2: Implementation
- [ ] Add RefundStatus enum to order.types.ts
- [ ] Create OrderRefundData.ts (Data layer)
- [ ] Create OrderRefundService.ts (Service layer)
- [ ] Create OrderRefundPage.tsx (UI layer)
- [ ] Register refund handler in OrderModule

### Phase 3: Verification
- [ ] Build verification

## Constraint Reminders
- Do not instantiate directly, use factory/DI
- Data layer must not reference Service/UI layers
- State machine is advisory path, record reason if deviating

## Completion Criteria
<promise>Mission Accomplished</promise>
" --completion-promise "Mission Accomplished" --max-iterations 3
```

### Scenario 2: Creating New UI Component

```
/ralph-loop:ralph-loop "
[MISSION RUNNER - PIR MODE]

## Task Objective
Create order confirmation modal component OrderConfirmModal

## Task Context
- Module path: src/components/order/
- Architecture layers: UI (Component + Hooks)
- Related skills: project-specific UI guidelines

## Phase 0: Initialization
1. mkdir -p _planning
2. Create mission_plan.md
3. Create mission_notes.md

## Iteration Rules
1. Read-Before-Decide: Read _planning/mission_plan.md
2. Execute: Execute next [ ] task, mark [x] when done
3. Validate: Build verification, append errors to mission_notes.md
4. Checkpoint: Update Progress Log

## Task Breakdown
### Phase 1: Research
- [ ] Review existing modal component patterns

### Phase 2: Implementation
- [ ] Create OrderConfirmModal.tsx in src/components/order/
- [ ] Implement useOrderConfirm hook for state management
- [ ] Implement render with proper accessibility
- [ ] Implement cleanup on unmount
- [ ] Add button event handlers

### Phase 3: Verification
- [ ] Build verification

## Constraint Reminders
- Do not modify auto-generated files
- Do not use document.getElementById, use refs
- Initialize hooks only at component top level

## Completion Criteria
<promise>Mission Accomplished</promise>
" --completion-promise "Mission Accomplished" --max-iterations 3
```

### Scenario 3: Cross-Module Feature Implementation

```
/ralph-loop:ralph-loop "
[MISSION RUNNER - PIR MODE]

## Task Objective
Implement order reward distribution feature, involving Order + Reward modules

## Task Context
- Module path: src/modules/order/, src/modules/reward/
- Architecture layers: Service layer + Data layer
- Related skills: project-specific domain rules

## Phase 0: Initialization
1. mkdir -p _planning
2. Create mission_plan.md
3. Create mission_notes.md

## Iteration Rules
1. Read-Before-Decide: Read _planning/mission_plan.md
2. Execute: Execute next [ ] task, mark [x] when done
3. Validate: Build verification, append errors to mission_notes.md
4. Checkpoint: Update Progress Log

## Task Breakdown
### Phase 1: Research
- [ ] Understand Reward module's distribution interface

### Phase 2: Implementation
- [ ] Add onOrderComplete callback in OrderService
- [ ] Define OrderReward data structure
- [ ] Call Reward service to distribute rewards
- [ ] Add reward distribution logging

### Phase 3: Verification
- [ ] Build verification

## Constraint Reminders
- Use events for decoupling, avoid direct class references
- Upper layers depend on lower layers, no reverse dependencies

## Completion Criteria
<promise>Mission Accomplished</promise>
" --completion-promise "Mission Accomplished" --max-iterations 3
```

---

## Iteration Count Guidelines

| Task Complexity | Recommended Iterations | Example |
|-----------------|------------------------|---------|
| Simple (1-2 files) | 2 | Add single class |
| Medium (3-5 files) | 3 | Three-layer entity |
| Complex (5-10 files) | 5 | Complete feature module |
| Large (10+ files) | 8-10 | New sub-module |

---

## mission_plan.md Complete Template

```markdown
# Mission Plan

## Objective
[Task objective extracted from user request]

## Success Criteria
- [ ] [Specific verifiable success criterion 1]
- [ ] [Specific verifiable success criterion 2]
- [ ] [Code compiles/builds successfully]

## Context
- Module path: src/modules/xxx/
- Architecture layers: Data/Service/UI
- Related constraints: project-specific rules

## Phases

### Phase 1: Research & Discovery
- [ ] Understand complete requirements
- [ ] Explore existing code/context
- [ ] Identify dependencies and constraints
- [ ] Record findings to mission_notes.md

### Phase 2: Implementation
- [ ] [Specific task 1]
- [ ] [Specific task 2]
- [ ] [Specific task 3]

### Phase 3: Verification
- [ ] Build verification
- [ ] Constraint check

## Progress Log
| Iteration | Phase | Actions Taken | Status |
|-----------|-------|---------------|--------|
| 1 | Init | Created planning structure | Done |
```

---

## mission_notes.md Complete Template

```markdown
# Mission Notes

## Research Findings
[Append findings with timestamps]
- [Iter 1] Found existing implementation uses factory pattern for object creation

## Decisions Made
[Record choices and reasoning]
- [Iter 1] Decided to extend base class rather than standalone implementation, shares most behavior

## Failures & Learnings
[CRITICAL! Record all failures - for next iteration learning]
- [Iter 2] TS2307: Cannot find module './OrderRefundData'
  -> Cause: File not added to exports
  -> Solution: Add export to index.ts
  -> Status: Fixed

## Self-Reflections
[Reflexion reflection records - structured reflection after validation failure, keep max 3]
- [Iter 2, Attempt 1] TS2307: Cannot find module './OrderRefundData'
  Reflection: Module path incorrect, should use '@/modules/order' not relative path, project has unified import alias
  Strategy: Fix immediately
  Status: Fixed

- [Iter 3, Attempt 1] TypeError: Cannot read property 'status' of undefined
  Reflection: orderData not initialized when accessed, hook runs before data fetch completes, need to add loading state check
  Strategy: Record pending
  Status: Next iteration

## Compliance Checks
[Step 3.6 verdicts per build-pass iteration - structured goal-drift detector]
- [Iter N] Task: "Create OrderRefundService.ts"
  Diff files: src/modules/order/services/OrderRefundService.ts (new), src/modules/order/index.ts (export)
  Q1 (completeness): complete
  Q2 (side changes): none
  Verdict: pass

- [Iter N+1] Task: "Add refund button to OrderDetailPage"
  Diff files: src/pages/OrderDetailPage.tsx, src/pages/OrderListPage.tsx (unplanned)
  Q1 (completeness): complete
  Q2 (side changes): found - OrderListPage.tsx was not in task scope ("while I was at it" refactor)
  Verdict: escalate
  -> triggered Step 3.5 Self-Reflection; revert OrderListPage.tsx change, log as Decision

## Clarifications
[User clarification records - from confidence check results]
- [Iter 1] Q: What distinguishes refund from cancellation?
  A: Refund is for completed orders, cancellation is for pending orders
  -> Impact: Need different validation logic

## Open Questions
[Unresolved questions]
- Should refund support partial amount?

## Audit Trail
[Pre-Promise Audit results per Mission Accomplished attempt - external signal record]
- [Iter N, Attempt M] Audit failed at item 3 (git diff empty)
  -> Suggested action: re-verify Iteration N actually wrote files, not just "claimed completion"
- [Iter N+1, Attempt 1] All 4 items passed -> promise issued
```

---

## Best Practices

### 1. Task Breakdown Granularity

```
Good breakdown:
- [ ] Create OrderRefundData.ts
- [ ] Create OrderRefundService.ts
- [ ] Create OrderRefundPage.tsx

Bad breakdown:
- [ ] Implement refund feature  (too coarse)
- [ ] Write line 1             (too fine)
```

### 2. Progress Log Recording

Update Progress Log at end of each iteration, recording:
- Iteration number
- Current Phase
- What was done specifically
- Status (Done/In Progress/Blocked)

### 3. Failure Recording Format

```
- [Iter N] {Error message}
  -> Cause: {Analysis}
  -> Solution: {Fix method}
  -> Status: {Fixed/Pending}
```

### 4. Build Verification Timing

Verify build at least once per iteration to avoid error accumulation.

### 5. Read-Before-Decide Checklist

Confirm at start of each iteration:
- [ ] Read mission_plan.md
- [ ] Confirmed current Objective
- [ ] Know what the next task is
- [ ] Checked mission_notes.md failure records
- [ ] Checked Clarifications for user clarifications

### 6. Confidence Check Best Practices

```
When to AskUserQuestion (Red - Low confidence):
- Requirements are ambiguous (e.g., "add refund" - what kind?)
- Multiple equivalent implementation approaches, can't judge preference
- Unsure which API/class to use
- Change might affect other active features

When to continue (Green/Yellow):
- Requirements clear, solution unique
- Dependent API has clear examples in codebase
- Change scope controllable, doesn't affect other modules

Recording format:
## Clarifications
- [Iter N] Q: [Specific question]
  A: [User answer]
  -> Impact: [Effect on implementation]
```

### 7. Self-Reflection Best Practices (Reflexion)

```
Three reflection questions (must answer):
1. Why did it fail?   - Find root cause, not just surface error
2. How to fix?        - Give specific, actionable fix plan
3. Similar pitfalls?  - Learn by analogy, avoid similar errors

Error classification decision:
| Type | Characteristics | Strategy | Example |
|------|-----------------|----------|---------|
| Simple | Build error, fix is clear | Fix immediately | Missing import, typo |
| Medium | Runtime error, needs thought | Record pending | Null ref, logic error |
| Complex | Architecture/design issue | Ask user | Inheritance, module boundary |

Memory management:
- Keep max 3 reflections (per Reflexion paper)
- New reflections prepend to top
- Auto-remove oldest when exceeding
- Check historical reflections during Read-Before-Decide

Reflection quality check:
Good: "Import path should use '@/modules/order', project has unified alias convention"
Bad: "Import wrong" (too vague, no specific solution)
```

### 8. State Machine Best Practices (Advisory Mode)

```
Design philosophy: State machine = Navigation map, not rails
- Provides recommended path, but allows Agent to detour based on situation
- Records actual path for audit and learning
- Abnormal situations can trigger "escape hatch" to free-form mode

State machine core states (recommended path):
init -> read_before_decide -> confidence_check -> execute -> validate -> checkpoint
                                    | (fail)
                             self_reflection

State transition rules (advisory):
- confidence_check:
  - high (>=4): -> execute
  - medium (3-4): -> execute (with recording)
  - low (<3): -> ask_user
- validate:
  - pass: -> checkpoint
  - fail: -> self_reflection
- self_reflection:
  - simple_error: -> execute (retry)
  - medium_error: -> checkpoint (next iteration)
  - complex_error: -> ask_user
- checkpoint:
  - complete: -> done
  - continue: -> read_before_decide

Escape hatch triggers:
- Agent confidence < 0.3
- Iteration count > max_iterations
- User command "free_form"
- Recommended path conflicts with actual situation

When deviating from state machine:
1. Record deviation reason to mission_notes.md -> Deviations & Reasons
2. Continue execution, keep mission_plan.md as goal reference
3. After task completion, record "free-form mode" path for future learning

State persistence (optional):
// _planning/workflow_state.json
{
  "current_state": "execute",
  "iteration": 2,
  "retry_count": 0,
  "phase": "implementation",
  "task_index": 3,
  "mode": "advisory"  // "advisory" | "free_form"
}

Interrupt recovery:
1. Read workflow_state.json
2. Continue from current_state
3. No need to re-initialize
```
