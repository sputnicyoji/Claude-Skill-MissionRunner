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

1. Parse user task description.

2. Determine {project-slug} (cross-mission learning layer namespace):
   - In git repo: `git rev-parse --show-toplevel` last segment -> lowercase + kebab-case
   - Not in git: `pwd` basename -> lowercase + kebab-case
   - Example: E:\Yoji\Prism-OS -> prism-os

3. Glob historical lessons (cross-mission learning layer, consumer side):
   - LessonsDir = ~/.claude/mission-archive/{slug}/lessons/
   - If dir doesn't exist -> skip (first mission for this project, no history to read)
   - Otherwise read all *.md frontmatter:
     * Extract each file's keywords[] and description
     * Match against current task description (case-insensitive substring)
     * Hit threshold: task contains >=1 keyword OR description token
   - Cache up to 5 hits with full lesson body

4. Create planning directory (pick the form matching your shell tool;
   do NOT mix — `mkdir -p` errors on PowerShell with
   "A positional parameter cannot be found"):
   - Unix-like (Bash / zsh): `mkdir -p _planning`
   - Windows PowerShell:     `New-Item -ItemType Directory -Force -Path _planning`

5. Create _planning/mission_plan.md:
   - Objective: Extract from task description
   - Success Criteria: Specific verifiable completion criteria
   - **## Prior Lessons** (NEW - populated from step 3):
     * If step 3 had hits: paste full lesson body + filename + Source reference
     * If no hits: write "(no historical lessons matched this task)"
   - Phases: Phased task list
   - Progress Log: Empty table

6. Create _planning/mission_notes.md with all standard sections (all empty at init):
   - Research Findings, Decisions Made, Failures & Learnings
   - Self-Reflections, Compliance Checks, Clarifications
   - Open Questions, Distilled Lessons, Audit Trail

Optional:
- Create _planning/workflow_state.json with the v2.2 canonical schema (see
  "State persistence" later in this file). Init shape:
   { "current_state": "init", "iteration": 0, "phase": "initialization",
     "mode": "advisory", "task_marked_done": false, "compliance_verdict": null }

---------------------------------------------------------------
                    Iteration Rules (Must Execute Each Iteration)
---------------------------------------------------------------

### Step 1: Read-Before-Decide (Goal Anchoring)
Read _planning/mission_plan.md
- Confirm: What is the Objective?
- Confirm: Which Phase are we in?
- Confirm: What is the next incomplete [ ] task?
- **Check `## Prior Lessons` section** (populated by Phase 0 step 3):
  - If >=1 hit: assess whether each lesson's applicability condition is triggered
    by the current task. If triggered, feed lesson content into Step 1.5
    Confidence Check as a signal (if a lesson warned about this trap,
    Solution Certainty / Risk Assessment scores should drop accordingly).
  - If no hits / no section: proceed without historical context.

Read _planning/mission_notes.md
- Check: What failures/learnings from last iteration?
- Check: Previous Clarifications records
- Check: Compliance Checks (verdict != pass) / Audit Trail

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
- After completion, update mission_plan.md:
  - **Do NOT mark `[x]` yet** (Mandate 5). `[x]` is reserved for Step 3.6
    verdict=pass. Marking here would let the LLM claim done before build/lint
    and Compliance Check, which is exactly the v1.0 "I claim done" failure
    mode the v1.1 protocol exists to prevent.
  - Update Progress Log table only (e.g. `Iter N: completed task X, awaiting verify`).

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
- (Reached on either path: (a) Step 3.6 verdict=pass, [x] just marked, or (b) Step 3.5 medium error returning to checkpoint with task left as `[ ]`)
- Update Progress Log table
- Decide: All Success Criteria complete (all `- [ ]` are `[x]` AND Success Criteria all `[x]`)?
  - Yes -> enter Phase 4 Debrief -> enter Phase 5 Distill -> run Pre-Promise Audit Checklist (5 items, see SKILL.md)
    - All 5 pass -> Output `<promise>Mission Accomplished</promise>`
    - Any fail   -> Output Partial Report + append result to `## Audit Trail`
  - No  -> Continue next iteration (back to Step 1 Read-Before-Decide)

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

Output completion flag ONLY when ALL 5 Pre-Promise Audit items pass:

1. mission_plan.md: all `- [ ]` tasks marked `[x]`
2. mission_plan.md: all Success Criteria marked `[x]`
3. **External signal:** `git diff --stat` shows non-empty changes (LLM cannot fabricate this — strongest anti-hallucination check). Exception: a verify-only mission whose deliverable is "confirm no change needed" may waive item 3 IF mission_plan.md Success Criteria explicitly declares "no code change expected"; record waiver in Audit Trail.
4. **External signal:** Build/lint/test commands actually executed and passed (traceable in Progress Log: must contain `verified: pass` or equivalent record for the latest entry)
5. **External signal:** Phase 5 Distill produced ≥1 lesson file under `~/.claude/mission-archive/{slug}/lessons/{TODAY}-*.md` (where TODAY is today's ISO date)

If any of the 5 fails:
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

> **重要：以下 3 个 Scenario 仅展示 domain-specific 的 Task Breakdown 和 Constraint Reminders。**
> **完整 mission prompt 必须包含**：
> - `## Phase 0: Initialization` (7 步, 含 slug 推导 + 历史 lesson glob), 来自 Standard Template
> - `## Iteration Rules` (Step 1 / 1.5 / 2 / 3 / 3.5 / 3.6 / 4), 来自 Standard Template
> - `## Completion Criteria` (5-item audit), 来自 Standard Template
>
> **使用方式**：复制 Standard Template 整体，然后用 Scenario 替换其中的 Task Breakdown 和 Constraint Reminders 段。

### Scenario 1: Adding New Entity Type (Three-Layer Architecture)

```
## Task Objective
Add refund functionality to the Order module in e-commerce system

## Task Context
- Module path: src/modules/order/
- Architecture layers: Data/Service/UI (three layers)
- Related skills: project-specific domain rules

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
```

### Scenario 2: Creating New UI Component

```
## Task Objective
Create order confirmation modal component OrderConfirmModal

## Task Context
- Module path: src/components/order/
- Architecture layers: UI (Component + Hooks)
- Related skills: project-specific UI guidelines

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
```

### Scenario 3: Cross-Module Feature Implementation

```
## Task Objective
Implement order reward distribution feature, involving Order + Reward modules

## Task Context
- Module path: src/modules/order/, src/modules/reward/
- Architecture layers: Service layer + Data layer
- Related skills: project-specific domain rules

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

## Prior Lessons
[Phase 0 step 3 output — lessons globbed from ~/.claude/mission-archive/{slug}/lessons/]
[If no hits at init: "(no historical lessons matched this task)"]

### lesson: refund-flow-architecture (2026-05-23)
> From mission-archive, hit at Phase 0. Read in Step 1 Read-Before-Decide.

**Lesson (≤150 字):**
退款的状态机和 Order 状态机正交（退款审批 / 部分退款 / 退款失败重试 vs 订单创建 / 支付 / 发货）；强行塞进 OrderService 会让单一职责崩溃。下次遇到"X 是 Y 的子流程？"问题时，先画状态机：正交 → 独立 Service；嵌套 → 子方法即可。

**Source:** 2026-05-23 mission Iter 3 Decisions Made
**File:** ~/.claude/mission-archive/prism-os/lessons/2026-05-23-refund-flow-architecture.md

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

## Distilled Lessons
[Phase 5 output - lesson files written to ~/.claude/mission-archive/{slug}/lessons/]
- 2026-05-23-refund-flow-architecture.md
  "退款状态机与订单状态机正交时应独立 Service，不要塞进 OrderService"
  Source: Iter 3 Decisions Made
- 2026-05-23-compliance-check-side-change-pattern.md
  "build pass 不等于 task done; 'while I was at it' refactor 是 Compliance Check 的主要拦截目标"
  Source: Iter 2 Compliance Checks (escalate verdict)

## Audit Trail
[Pre-Promise Audit results per Mission Accomplished attempt - external signal record.
 Also holds a single index line per escape-hatch abandon; the authoritative
 abandon reason lives in `## Deviations & Reasons`.]
- [Iter N, Attempt M] Audit failed at item 3 (git diff empty)
  -> Suggested action: re-verify Iteration N actually wrote files, not just "claimed completion"
- [Iter N+1, Attempt 1] All 5 items passed -> promise issued
- [Iter N+2] No promise issued — abandoned, see Deviations & Reasons

## Deviations & Reasons
[Escape Hatch / state-machine deviation log — used when mode switches to free_form
 or the agent temporarily bypasses the recommended state path.]
[Empty unless escape hatch fired.]
- [Iter N] Trigger: {agent_confidence<0.3 / iteration>max / user:free_form / path_conflict}
  Original current_state: {state}
  New mode: free_form
  Reason: {why deviate}
  Hard constraints still binding: 5-item Pre-Promise Audit, Mandate 5 ([x] timing),
                                  Phase 5 Distill
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

State persistence (optional). The canonical schema is defined in SKILL.md
"## 工作流状态机 > 状态持久化" (v2.2). Mirror its fields verbatim:
// _planning/workflow_state.json
{
  "current_state": "execute",
  "iteration": 2,
  "retry_count": 0,
  "phase": "implementation",
  "task_index": 3,
  "task_marked_done": false,
  "compliance_verdict": null,
  "mode": "advisory",       // "advisory" | "free_form"
  "confidence_scores": { "understanding": 5, "certainty": 4, "dependencies": 4, "risk": 4 },
  "timestamp": "2026-05-23T15:30:00Z"
}

Interrupt recovery:
1. Read workflow_state.json
2. Continue from current_state
3. No need to re-initialize
```
