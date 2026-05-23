# Mission Runner 自我强化改进计划

> **执行须知（给后续工程师 / 后续会话）：** 本计划修改的仓库是 `C:\Users\Administrator\.claude\skills\mission-runner\`（独立 git 仓库），与 Prism-OS 无关。所有 `Edit`/`Write` 操作的 file_path 必须指向该仓库内的文件。本计划三个 Task 互相独立，每个 Task 完成后必须独立 commit。Markdown skill 没有传统单元测试，所以 "验证" 用"手动跑一个仿真 mission"替代。

**Goal：** 给 mission-runner 加 3 道真正能落地的强化：完成审计 checklist（防 false positive）、Compliance Check（防 goal drift）、跨任务学习层（解决单 mission 边界问题）。

**Architecture：** 三个 Task 按风险/收益从低到高排序，每个独立可发布、可回退。Task 1+2 只改 SKILL.md 与 prompt-template.md 两个文件；Task 3 引入新的跨项目目录 `~/.claude/mission-archive/`，但目录由 LLM 首次 mission 时按需创建，不需要预先 bootstrap。

**Tech Stack：** Markdown skill 文件（无 runtime、无依赖）；改造点全部在 prompt 层；验证靠手动 mission；归档靠文件系统。

---

## 总览：4 个 Task 的依赖与时间

```
Task 0 (Purge RiderMcp Legacy)     独立  ~30 分钟
   ↓
Task 1 (Pre-Promise Audit)         独立  ~1 晚
   ↓ (Task 3A 将复用 Task 1 的 checklist 结构)
Task 2 (Compliance Check)          独立  ~1 晚
   ↓
Task 3A (Distill 机制)              依赖 Task 1 的 checklist 扩展  ~半天 + 1 个观察 mission
   ↓
Task 3B (Phase 0 glob + 观察期)     依赖 Task 3A  ~半天 + 3-5 个真实 mission 的执行率观测
```

Task 0 → 1 → 2 → 3A → 3B 是推荐顺序。Task 0 应当最先做——它清理掉 mission-runner skill 里继承自其他项目的 RiderMcp 残留（Kotlin/Unity/PSI/ReadAction 等概念），避免后续 Task 在已经污染的基础上叠加。Task 1 和 Task 2 之间可以互换；Task 3 必须先做 3A 再做 3B（3B 要 glob 的就是 3A 产出的文件）。

---

## 总体涉及文件清单

```
mission-runner/
├── SKILL.md                                                 修改：六处
│   ├── [Task 0] frontmatter description 删除 RiderMcp 激活条件行
│   ├── [Task 0] "RiderMcp Project-Specific Error Patterns" 整段删除（约 217-241 行）
│   ├── [Task 0] "RiderMcp Project-Specific Validation" 整段删除（约 690-708 行）
│   ├── [Task 1] 三大强制（第 70-83 行附近） + 第 4 项强制（Pre-Promise Audit）
│   ├── [Task 2] 工作流 Step 3 Validate 之后 + 新增 Step 3.6 Compliance Check
│   ├── [Task 3A] 工作流 Phase 4 Debrief 之后 + 新增 Phase 5 Distill
│   └── [Task 3B] Phase 0 Initialization 段 + 新增 "glob 历史 lessons" 步骤
├── references/
│   ├── error-patterns.md                                    [Task 0] **删除整个文件**
│   ├── ridermcp-constraints.md                              [Task 0] **删除整个文件**
│   └── prompt-template.md                                   修改：三处
│       ├── [Task 2] 迭代规则段（Step 3.6 同步）
│       ├── [Task 2/3A] mission_notes.md 模板 + 新增 Compliance Checks / Distilled Lessons 段
│       └── [Task 3B] mission_plan.md 模板 + 新增 Prior Lessons 段
├── docs/plans/
│   └── 2026-05-23-self-improvement.md                       本计划（已创建）
└── CHANGELOG.md                                             修改：追加 [Unreleased] 段（每个 Task 各加一节）
```

不涉及：README.md、README_ja.md、README_zh-CN.md（这些是用户文档，等所有 Task 都落地、CHANGELOG cut 出版本号时再统一更新一次）。

---

## Task 0：Purge RiderMcp Legacy（清理项目特异性残留）

**Files：**
- Modify：`C:\Users\Administrator\.claude\skills\mission-runner\SKILL.md`（frontmatter + 两段 RiderMcp）
- Delete：`C:\Users\Administrator\.claude\skills\mission-runner\references\error-patterns.md`（整个文件，9 个 Kotlin/Unity/PSI 错误模式）
- Delete：`C:\Users\Administrator\.claude\skills\mission-runner\references\ridermcp-constraints.md`（整个文件）
- Modify：`C:\Users\Administrator\.claude\skills\mission-runner\CHANGELOG.md`

**Why：** mission-runner 是从某个 RiderMcp 模板演化出来的（或在最初草稿时绑定了那个项目），SKILL.md 顶部 frontmatter 把 "RiderMcp projects: Kotlin Plugin + TypeScript Bridge dual-language development" 列为激活场景之一，body 里还有两整段 RiderMcp 专属内容（PSI/ReadAction/Unity Play mode/Kotlin gradle 等）。这些内容在 Prism-OS（纯 TypeScript Node.js）或其他任何非 RiderMcp 项目里是上下文噪音——每次 skill 激活都会把这些异源概念灌进 LLM。先清掉再做后续 Task，避免在污染基础上叠加。

**验收：** Task 0 完成后：
1. `grep -ri -E "rider[ -]?mcp|kotlin|ReadAction|WriteCommandAction|XDebugger|Unity|gradle" C:/Users/Administrator/.claude/skills/mission-runner/` 应只在 CHANGELOG.md 历史段（[1.0.0]）和 docs/plans/ 命中（本计划文档本身提到过这些词），SKILL.md 与 references/ 下应 0 命中。
2. `ls C:/Users/Administrator/.claude/skills/mission-runner/references/` 应只剩 `prompt-template.md` 一个文件。
3. SKILL.md frontmatter description 不再包含 "RiderMcp" 字样。

### Step 0.1：修改 SKILL.md frontmatter description

打开 `C:\Users\Administrator\.claude\skills\mission-runner\SKILL.md`，定位 frontmatter（第 1-13 行）。把原文：

```yaml
---

name: mission-runner
description: |
  Large-scale module automation expert. Integrates task-planner + ralph-loop + PIR capabilities.
  Activates for these scenarios:
  - Large module development: Creating/modifying multiple files (3+)
  - Multi-layer architecture: Simultaneous Data/Service/UI implementation
  - Cross-module refactoring: Affecting multiple subsystems
  - Complex feature implementation: Multi-file coordination required
  - RiderMcp projects: Kotlin Plugin + TypeScript Bridge dual-language development
  Provides: (1) Auto-iterative execution (2) Read-Before-Decide safeguard (3) Local file memory (4) Validation checks
---
```

替换为：

```yaml
---

name: mission-runner
description: |
  Large-scale module automation expert. Integrates task-planner + ralph-loop + PIR capabilities.
  Activates for these scenarios:
  - Large module development: Creating/modifying multiple files (3+)
  - Multi-layer architecture: Simultaneous Data/Service/UI implementation
  - Cross-module refactoring: Affecting multiple subsystems
  - Complex feature implementation: Multi-file coordination required
  Provides: (1) Auto-iterative execution (2) Read-Before-Decide safeguard (3) Local file memory (4) Validation checks
---
```

仅删除一行（RiderMcp projects 那行），其他保持不变。

### Step 0.2：删除 SKILL.md 中 "RiderMcp Project-Specific Error Patterns" 整段

定位约第 217-241 行的整段（含 `### RiderMcp Project-Specific Error Patterns` 标题 + 后续描述 + 9 个 error categories 列表 + "Use the error patterns to:" 列表）。完整删除该段，包括段前段后的 markdown 分隔线（`---`）如果有。

删除范围（从最初 Read 看到的内容）：

```markdown
### RiderMcp Project-Specific Error Patterns

For faster error classification and Self-Reflection in RiderMcp projects, **consult references/error-patterns.md** for:

- **9 pre-classified error types** with root causes and typical fixes
- **Error decision tree** for quick classification
- **Self-reflection templates** for common failures

Error categories:
1. PSI Access Violation (ReadAction required)
2. Write Action Violation (WriteCommandAction required)
3. Service Not Found (ServiceRegistry issue)
4. XDebugger Async Timing (callback not awaited)
5. Zod Validation Failed (type mismatch across languages)
6. MCP Tool Definition Mismatch (tool name inconsistent)
7. Unity Object Destroyed (lifetime issue)
8. Expression Not in Play Mode (Unity prerequisites)
9. handleId Format Inconsistent (cross-language identifier)

Use the error patterns to:
- Quickly identify error type (simple/medium/complex)
- Generate accurate Self-Reflections
- Choose correct retry strategy
- Avoid similar errors in future iterations
```

这整段都是引用 references/error-patterns.md 的，文件即将删除，所以整段也作废。删除后留一行空白即可（保持上下文段落间距）。

### Step 0.3：删除 SKILL.md 中 "RiderMcp Project-Specific Validation" 整段

定位约第 690-708 行：

```markdown
### RiderMcp Project-Specific Validation

For RiderMcp development, validation has special requirements:

**Consult references/ridermcp-constraints.md for:**
- Kotlin Plugin constraints (ReadAction/WriteAction, Service lifecycle)
- TypeScript Bridge constraints (JSON-RPC 2.0, Zod validation)
- Cross-language type alignment checks
- Unity debugging prerequisites
- TDD workflow and test commands

**Validation Commands:**
- Kotlin build: `cd rider-mcp-plugin && ./gradlew build`
- Kotlin tests: `cd rider-mcp-plugin && ./gradlew test`
- TypeScript types: `cd mcp-bridge && npm run type-check`
- TypeScript tests: `cd mcp-bridge && npm test`

**Note:** Currently tests are temporarily disabled for Rider 2025.3.1 upgrade. Use manual verification + Plugin Verifier instead.
```

完整删除。删除后该段所在的位置（在 Step 3 Validate ASCII 框之后、Step 3.5 Self-Reflection 框之前）会接续——这正好是 Task 2 的 Step 3.6 Compliance Check 插入位置，所以 Task 0 删完留出的空隙正好被 Task 2 填上，节奏完美。

### Step 0.4：删除 references/ 下两个 RiderMcp 文件

```bash
rm "C:/Users/Administrator/.claude/skills/mission-runner/references/error-patterns.md"
rm "C:/Users/Administrator/.claude/skills/mission-runner/references/ridermcp-constraints.md"
```

或用 PowerShell：

```powershell
Remove-Item "C:\Users\Administrator\.claude\skills\mission-runner\references\error-patterns.md"
Remove-Item "C:\Users\Administrator\.claude\skills\mission-runner\references\ridermcp-constraints.md"
```

删除后 `references/` 目录应只剩 `prompt-template.md`。

### Step 0.5：CHANGELOG + commit

在 `C:\Users\Administrator\.claude\skills\mission-runner\CHANGELOG.md` 顶部、`## [1.0.0] - 2024-01-15` 之前追加（如 Task 1 已加 `[Unreleased]` 段则补充该段；如未加则新建）：

```markdown
## [Unreleased]

### Removed
- **RiderMcp legacy purge**: removed Kotlin Plugin / Unity / PSI / TypeScript Bridge specific content from a previous incarnation of this skill. Affected: SKILL.md frontmatter description (one activation line), SKILL.md "RiderMcp Project-Specific Error Patterns" section, SKILL.md "RiderMcp Project-Specific Validation" section, references/error-patterns.md (entire file, 9 Kotlin/Unity error patterns), references/ridermcp-constraints.md (entire file).
- Rationale: mission-runner is a general-purpose multi-file automation skill; the RiderMcp content was noise in non-RiderMcp projects.
```

提交：

```bash
git -C "C:/Users/Administrator/.claude/skills/mission-runner" add -A
git -C "C:/Users/Administrator/.claude/skills/mission-runner" status   # 确认只有上述 4 个文件被改/删
git -C "C:/Users/Administrator/.claude/skills/mission-runner" commit -m "chore: purge RiderMcp legacy content (skill is now project-agnostic)"
```

**用 `git add -A` 因为涉及删除文件。** 提交前用 `git status` 二次确认：被改的应只有 SKILL.md + CHANGELOG.md，被删的应只有 references/error-patterns.md + references/ridermcp-constraints.md。

### Step 0.6：验收

跑验收脚本：

```powershell
# 1. 没有任何 RiderMcp 相关词残留
Select-String -Path "C:\Users\Administrator\.claude\skills\mission-runner\SKILL.md","C:\Users\Administrator\.claude\skills\mission-runner\references\*.md" -Pattern "rider[ -]?mcp|kotlin|ReadAction|WriteCommandAction|XDebugger|Unity|gradle" -CaseSensitive:$false
# 期望：无输出（除了 CHANGELOG 的 Removed 描述可能命中，那是合理的）

# 2. references/ 只剩 prompt-template.md
Get-ChildItem "C:\Users\Administrator\.claude\skills\mission-runner\references\"
# 期望：只列出 prompt-template.md

# 3. SKILL.md frontmatter 干净
Get-Content "C:\Users\Administrator\.claude\skills\mission-runner\SKILL.md" -TotalCount 15
# 期望：description 段不含 "RiderMcp"
```

三项全过 -> Task 0 完成，可以继续 Task 1。

---

## Task 1：Pre-Promise Audit Checklist（改造 #6）

**Files：**
- Modify：`C:\Users\Administrator\.claude\skills\mission-runner\SKILL.md`（强制3 段附近 + Step 4 Checkpoint 段）
- Modify：`C:\Users\Administrator\.claude\skills\mission-runner\references\prompt-template.md`（完成条件段）
- Modify：`C:\Users\Administrator\.claude\skills\mission-runner\CHANGELOG.md`（追加 [Unreleased]）

**Why：** 现状是 LLM 自己判断"所有任务完成 + 验证通过"才发 `<promise>Mission Accomplished</promise>`，没有客观外部信号校验。真实失败模式：checkboxes 全打勾但 `git diff` 是空的（LLM 以为做了但其实只在脑内做了）。审计要包含至少一项**外部信号**，不能全靠 LLM 自报。

**验收（手动验证 mission）：** Task 1 完成后，跑一个故意制造矛盾的小 mission：让 mission-runner 处理一个简单任务，但在迭代中**只口头说"已完成"**而不执行 Edit。新 checklist 必须拦住，拒绝发 promise。

### Step 1.1：在 SKILL.md "三大强制" 段加第 4 项

打开 `C:\Users\Administrator\.claude\skills\mission-runner\SKILL.md`，定位现有"## 三大强制 (MUST)" 段（约第 70 行）。在 `强制3` 结束、`## 置信度检查协议` 之前插入：

```markdown
强制4: 必须在发 Mission Accomplished 之前通过 Pre-Promise Audit Checklist
  -> 见下方"Pre-Promise Audit Checklist (CRITICAL)"段
  -> 4 项中任一未通过 -> 禁止发 promise，输出 Partial Report
```

然后在该段之后、`## 置信度检查协议` 之前，新增一节：

```markdown
## Pre-Promise Audit Checklist (CRITICAL)

**在输出 `<promise>Mission Accomplished</promise>` 之前必须逐项核对，4 项全部通过才允许发 promise。**

| # | 检查项 | 信号来源 | 通过条件 |
|---|--------|----------|----------|
| 1 | mission_plan.md 所有 Phase 任务标记 [x] | 内部（plan 文件） | grep `^- \[ \]` 应为 0 行 |
| 2 | mission_plan.md 所有 Success Criteria 标记 [x] | 内部（plan 文件） | Success Criteria 段无 `[ ]` |
| 3 | `git diff --stat` / `git status` 显示有实质改动 | **外部信号**（git） | 至少 1 个文件 modified/added |
| 4 | Build/lint/test 命令真实执行并通过 | 外部信号（命令输出） | Progress Log 最近一项含 "verified: pass" |

**任一项未通过：**
- 不输出 `<promise>Mission Accomplished</promise>`
- 改为输出 Partial Report，列出：哪一项未通过、原因、下一步建议
- 把审计结果追加到 mission_notes.md 新增的 `## Audit Trail` 段

**为什么必须有"外部信号"（项 3）：**
LLM 自报"已完成"是不可信的——存在 hallucinate 完成度的常见失败模式。`git diff` 是 LLM 不能伪造的外部状态，是最强的反 hallucination 信号。
```

### Step 1.2：在 SKILL.md Step 4 Checkpoint 段对齐完成判定逻辑

定位"## 工作流程"段中的 `Step 4: Checkpoint (检查点)`（约第 737 行附近）。把原有完成判定文本：

```
│  判断: 所有任务完成？                                         │
│  ├─ 是 + 验证通过 -> <promise>Mission Accomplished</promise>  │
│  └─ 否 -> 继续下一迭代                                        │
```

替换为：

```
│  判断: 所有任务完成？                                         │
│  ├─ 是 -> 执行 Pre-Promise Audit Checklist (4 项)             │
│  │       ├─ 4 项全通过 -> <promise>Mission Accomplished</promise>│
│  │       └─ 任一未通过 -> 输出 Partial Report + 追加 Audit Trail │
│  └─ 否 -> 继续下一迭代                                        │
```

### Step 1.3：在 prompt-template.md 完成条件段同步

打开 `C:\Users\Administrator\.claude\skills\mission-runner\references\prompt-template.md`，定位 `## Completion Criteria`（约第 152 行）。把原文：

```
Output completion flag ONLY when ALL conditions are met:
1. All [ ] in mission_plan.md marked as [x]
2. Code compiles/builds successfully
3. Related skill constraints followed

On completion, output: <promise>Mission Accomplished</promise>
```

替换为：

```
Output completion flag ONLY when ALL 4 Pre-Promise Audit items pass:

1. mission_plan.md: all `- [ ]` tasks marked `[x]`
2. mission_plan.md: all Success Criteria marked `[x]`
3. **External signal:** `git diff --stat` shows non-empty changes (LLM cannot fabricate this)
4. **External signal:** Build/lint/test commands actually executed and passed (traceable in Progress Log: must contain `verified: pass` for the latest entry)

If any of the 4 fails:
- Do NOT output `<promise>Mission Accomplished</promise>`
- Output Partial Report instead, including: which audit item failed, why, suggested next step
- Append the audit result to mission_notes.md `## Audit Trail` section

On full pass, output: <promise>Mission Accomplished</promise>
```

并在 `## mission_notes.md Complete Template`（约第 375 行）的 `## Open Questions` 之后追加：

```markdown
## Audit Trail
[Pre-Promise Audit results per Mission Accomplished attempt]
- [Iter N, Attempt M] Audit failed at item 3 (git diff empty)
  -> Suggested action: re-verify Iteration N actually wrote files, not just "claimed completion"
```

### Step 1.4：手动验证 mission

在任意 sandbox 项目（推荐：`E:\Yoji\test-sandbox\` 或新建临时目录），让 mission-runner 处理一个**有意制造的假完成场景**：

```
[MISSION RUNNER - PIR MODE]

## Task
创建一个 hello.txt 文件，内容为单词 "hello"。

## Success Criteria
- [ ] hello.txt 存在
- [ ] 文件内容为 "hello"
```

预期：mission-runner 在执行过程中（或调试时手动模拟），把 plan 全打勾**但故意不执行 Write**——此时检查 git diff 应为空，Pre-Promise Audit 项 3 必须失败，promise 必须被拒发，输出 Partial Report。

如果跑下来 promise 仍被发出 → Step 1.1 的强制4 文本不够强、或 Step 1.2 的判定逻辑没生效，需要回到 SKILL.md 加重语气（例如把"应"改"必须"、增加"违反此 checklist 即视为禁令1-4 中的禁令"等约束）。

### Step 1.5：CHANGELOG + commit

在 `C:\Users\Administrator\.claude\skills\mission-runner\CHANGELOG.md` 顶部、`## [1.0.0] - 2024-01-15` 之前追加：

```markdown
## [Unreleased]

### Added
- **Pre-Promise Audit Checklist** - 4-item gate before `<promise>Mission Accomplished</promise>`, includes external signal (git diff) to prevent hallucinated completion. See SKILL.md "Pre-Promise Audit Checklist (CRITICAL)" section.
- **Audit Trail** section in mission_notes.md template for recording rejected promise attempts.
```

提交：

```bash
git -C "C:/Users/Administrator/.claude/skills/mission-runner" add SKILL.md references/prompt-template.md CHANGELOG.md
git -C "C:/Users/Administrator/.claude/skills/mission-runner" commit -m "feat: add Pre-Promise Audit Checklist (4-item gate with git diff external signal)"
```

---

## Task 2：Step 3.6 Compliance Check（改造 #1 缩水版）

**Files：**
- Modify：`C:\Users\Administrator\.claude\skills\mission-runner\SKILL.md`（工作流 Step 3 之后新增 Step 3.6；Step 1 Read-Before-Decide 段同步）
- Modify：`C:\Users\Administrator\.claude\skills\mission-runner\references\prompt-template.md`（迭代规则段 + notes 模板）
- Modify：`C:\Users\Administrator\.claude\skills\mission-runner\CHANGELOG.md`

**Why：** 现 Step 3 Validate 只验证「代码能 build / lint / test pass」，不验证「实现的是 mission_plan 里说的那个任务」。Step 3.6 在 build pass 之后插入一道 prompt-level 自检：把"当前 [ ] 任务描述 + 本次 git diff + 最近 Decisions Made"拼起来问 LLM"diff 是否符合任务描述？有无意外改动？"。**先不派 subagent，先用主对话内自问自答的成本最低形态**，验证一周；如果不灵再升级到 Task subagent。

**验收（手动验证 mission）：** Task 2 完成后跑一个故意 goal drift 的 mission：让 mission-runner 完成"在 file_a.txt 写 hello"任务，但在执行中"顺便"也修改了 file_b.txt（计划外）。Compliance Check 必须把 verdict 标为 `needs-revision` 或 `escalate`，并把意外改动记入 notes。

### Step 2.1：在 SKILL.md 工作流 Step 3 之后插入 Step 3.6

打开 `SKILL.md`，定位"## 工作流程"段的 Step 3 Validate ASCII 框（约第 684 行）。在 Step 3 框的"如无错误 -> 跳过 Step 3.5，直接进入 Step 4" 后面、Step 3.5 Self-Reflection 框之前插入：

```markdown
           |
           v (如果 build 通过)
┌─ Step 3.6: Compliance Check (Build Pass 路径强制执行) ───────┐
│  **触发条件**: Step 3 build/lint/test 全部通过                │
│  **目标**: 验证 diff 不仅"能跑"，而且"实现的就是计划那个任务" │
│                                                              │
│  1. 收集三方信号:                                             │
│     a. 当前迭代正在做的 [ ] 任务（从 mission_plan.md 提取）   │
│     b. 本次 Execute 阶段产生的 git diff (`git diff HEAD`)     │
│     c. mission_notes.md > Decisions Made 最近一条（如有）     │
│                                                              │
│  2. 自问 2 个问题（在主对话中直接回答，不派 subagent）:        │
│     Q1: 这个 diff 是否完整实现了 a 描述的任务？               │
│        （不是"代码能编译"，是"功能 ≈ 任务描述"）              │
│     Q2: 是否含计划外的"意外改动"？（goal drift 信号）         │
│        - 文件改动是否都在任务影响范围内？                     │
│        - 是否引入了任务未要求的重构 / 改名 / "顺便修复"？     │
│                                                              │
│  3. 输出 Verdict（写入 mission_notes.md > Compliance Checks）:│
│     - [Iter N] Task: "{任务名}"                              │
│       Diff files: {列出 git diff 影响的文件}                  │
│       Q1 (实现完整度): {完整 / 部分 / 偏离}                   │
│       Q2 (意外改动): {无 / 有 - 列举}                         │
│       Verdict: {pass / needs-revision / escalate}             │
│                                                              │
│  4. 根据 Verdict 分支:                                        │
│     - pass         -> 进入 Step 4 Checkpoint                  │
│     - needs-revision -> 不勾本任务 [x]，下一迭代继续此任务    │
│                       （在 plan 该任务下追加修正子任务）       │
│     - escalate     -> 视为"中等错误"，触发 Step 3.5 Self-Reflection│
│                     （把 Q1/Q2 答案作为 Reflection 输入）     │
└──────────────────────────────────────────────────────────────┘
           |
           v (Verdict = pass)
```

把后续的 `Step 4: Checkpoint` 框接在 Step 3.6 后面（原本接在 Step 3 后面）。

### Step 2.2：在 SKILL.md "三大强制" 段加 Step 3.6 的强制语气

在 Step 1.1 已插入的"强制4"段之后追加（注意编号变化）：

```markdown
强制5: 必须在每次 build pass 之后执行 Compliance Check (Step 3.6)
  -> 跳过 Step 3.6 等同于跳过 Step 3 Validate
  -> Verdict 必须写入 mission_notes.md > Compliance Checks
  -> Verdict ≠ pass 时禁止勾 [x]，禁止进入 Step 4
```

并同步更新 SKILL.md "## 三大强制" 标题为 "## 五大强制 (MUST)"。

### Step 2.3：在 prompt-template.md 迭代规则段同步

打开 `references/prompt-template.md`，定位 `### Step 3: Validate`（约第 101 行）。在 Step 3 与 Step 3.5 之间插入：

```markdown
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
   - needs-revision -> do NOT mark task [x]; next iteration continues this task
                       (append correction subtask under the task in plan)
   - escalate       -> treat as "medium error"; trigger Step 3.5 Self-Reflection
                       (feed Q1/Q2 answers as Reflection input)
```

把原 Step 4 改为：

```markdown
### Step 4: Checkpoint
- Update Progress Log table
- (Compliance Check must have verdict=pass before reaching here)
- Decide: All Success Criteria complete?
  - Yes -> run Pre-Promise Audit Checklist (4 items, see SKILL.md)
    - All 4 pass -> Output completion flag
    - Any fail   -> Output Partial Report + append Audit Trail
  - No  -> Continue next iteration
```

### Step 2.4：在 prompt-template.md mission_notes.md 模板新增段

在 mission_notes.md Complete Template 的 `## Self-Reflections` 段和 `## Clarifications` 段之间，插入：

```markdown
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
```

### Step 2.5：手动验证 mission

在 sandbox 跑一个 goal-drift mission：

```
[MISSION RUNNER - PIR MODE]

## Task
在 sandbox/notes.txt 文件末尾追加一行 "TODO: review"。

## Success Criteria
- [ ] notes.txt 末尾有 "TODO: review" 一行
- [ ] 不修改其他文件
```

执行时**故意**让 mission-runner 同时"顺手"格式化整个文件（或改了无关的其他文件）。Step 3.6 必须把 Verdict 标为 `escalate`，notes 中必须出现"side changes: found"。

如果跑下来 Verdict 仍是 `pass` → Step 2.1 的 Q2 指令不够具体，需要在 Q2 下加更精细的判定条件（"diff 行数 > 任务预估的 3 倍即视为 drift"等）。

### Step 2.6：CHANGELOG + commit

在 `CHANGELOG.md` 的 `[Unreleased]` 段追加：

```markdown
### Added
- **Step 3.6 Compliance Check** - prompt-level self-check on build-pass path: validates that diff matches task description (not just "compiles"). Detects goal drift via 2 self-questions and writes structured verdict to mission_notes.md > Compliance Checks.
- New `Compliance Checks` section in mission_notes.md template.
```

提交：

```bash
git -C "C:/Users/Administrator/.claude/skills/mission-runner" add SKILL.md references/prompt-template.md CHANGELOG.md
git -C "C:/Users/Administrator/.claude/skills/mission-runner" commit -m "feat: add Step 3.6 Compliance Check (prompt-level diff-vs-plan verification)"
```

### Step 2.7：一周观察节点（不是即时步骤，但要排进日历）

Task 2 落地后第 7 天，回看这一周用 mission-runner 跑过的所有 mission 的 `mission_notes.md > Compliance Checks` 段，统计：

- 总 build-pass 迭代数 N
- 其中 Verdict = pass 的数 N_pass
- 其中 Verdict = needs-revision / escalate 的数 N_caught
- 其中"我事后发现 drift 但 Verdict 仍是 pass"的数 N_missed（这是 false negative）

决策规则：
- 若 N_caught ≥ 1 且 N_missed = 0 → Compliance Check 有效，保留
- 若 N_caught = 0 且 N_missed = 0 → 数据不足或本周没有 drift 案例，再观察一周
- 若 N_missed ≥ 1 → 自问形式不够，**升级到 Task subagent**（派 `code-reviewer` agent 做 compliance review，给它 git diff + 任务描述）

升级方案先不写进 plan，等观察期数据决定。

---

## Task 3A：Distill 机制 + 把 distill 设为硬前置（改造 #2 第一步）

**Files：**
- Modify：`C:\Users\Administrator\.claude\skills\mission-runner\SKILL.md`（新增 Phase 5 段；Pre-Promise Audit Checklist 加第 5 项）
- Modify：`C:\Users\Administrator\.claude\skills\mission-runner\references\prompt-template.md`（迭代规则段之后追加 Phase 5；notes 模板新增 Distilled Lessons 段）
- Modify：`C:\Users\Administrator\.claude\skills\mission-runner\CHANGELOG.md`

**Why：** mission-runner 当前最大的结构性弱点是单 mission 边界——每次都是从零开始，过去 mission 的教训丢失。Distill 把本次 mission 的关键 Decisions / Reflections 蒸馏成 1-3 条 ≤150 字的 lesson 写到跨项目目录。**关键设计：distill 失败 → 禁止发 Mission Accomplished**，避免 LLM 跳过收尾步骤（这是 LLM 最常省略的环节）。

**Archive 路径结构：**

```
%USERPROFILE%\.claude\mission-archive\
└── {project-slug}\
    └── lessons\
        ├── 2026-05-23-refund-flow-architecture.md
        ├── 2026-05-23-search-rebuild-mock-shape.md
        └── ...
```

`{project-slug}` = mission 启动时 `git rev-parse --show-toplevel` 末段目录名的 kebab-case（例如 `Prism-OS` → `prism-os`）。没有 git 时退化为 cwd basename。

**单个 lesson 文件结构：**

```markdown
---
name: refund-flow-architecture
description: 一句话描述，用于 Phase 0 glob 时模糊匹配
mission_date: 2026-05-23
keywords: [refund, payment, service-layer]
---

# Lesson: 退款服务应单独成 Service 而非塞进 OrderService

**Context:** 2026-05-23 实现订单退款功能时遇到的架构决策。

**Lesson (≤150 字):**
退款的状态机和 Order 状态机正交（退款审批/部分退款/退款失败重试 vs 订单创建/支付/发货）；
强行塞进 OrderService 会让单一职责崩溃。下次遇到"X 是 Y 的子流程？"问题时，
先画状态机：状态机正交 → 独立 Service；状态机嵌套 → 子方法即可。

**Source iteration:** Iter 3, Compliance Check verdict=escalate
```

**验收（手动验证 mission）：** Task 3A 落地后跑一个简单 mission。Mission Accomplished 之前必须：(1) Phase 5 被执行；(2) `%USERPROFILE%\.claude\mission-archive\{slug}\lessons\` 下出现至少 1 个 .md 文件；(3) 该文件出现在 mission_notes.md `## Distilled Lessons` 段的引用列表中。任一缺失 → 第 5 项 Audit 失败，promise 被拒。

### Step 3A.1：在 SKILL.md 工作流加 Phase 5 段

打开 `SKILL.md`，定位"## 工作流程" 段末尾的 `Phase 4: Debrief` 段（约第 748 行）。在 `Phase 4: Debrief` 段之后追加：

````markdown
---------------------------------------------------------------

Phase 5: Distill (收尾蒸馏 - Mission Accomplished 的硬前置)

├── 5.1 确定 project-slug:
│      cd 到 git 根目录: `git rev-parse --show-toplevel`
│      取末段目录名 -> 小写 + kebab-case = {project-slug}
│      无 git 仓库时: 用 cwd 末段目录名
│
├── 5.2 确保 archive 目录存在:
│      mkdir -p "$HOME/.claude/mission-archive/{slug}/lessons"
│      (Windows: %USERPROFILE%\.claude\mission-archive\{slug}\lessons)
│
├── 5.3 从本次 mission_notes.md 提取 Lesson 候选:
│      扫描以下三段:
│        - Decisions Made: 哪个决定值得复用？
│        - Self-Reflections: 哪个失败的根因有跨场景价值？
│        - Compliance Checks (Verdict ≠ pass 的): 哪类 drift 应该提前防？
│      生成 1-3 条候选（不是越多越好，宁缺毋滥）
│
├── 5.4 每条候选写入 archive 目录:
│      文件名: {YYYY-MM-DD}-{topic-kebab-case}.md
│      内容: 见 SKILL.md "Lesson 文件结构" 模板
│      Lesson 正文 ≤150 字（强制：超出则压缩）
│
├── 5.5 在 mission_notes.md 追加 ## Distilled Lessons 段:
│      列出本次产出的 lesson 文件路径与一句话摘要
│
└── 5.6 Pre-Promise Audit Checklist 项 5 验证:
       项 5: archive 目录下存在至少 1 个本次 mission 的 lesson 文件
       项 5 失败 -> 禁止发 promise，回到 5.3 重新蒸馏

```

并在 SKILL.md 的 `## 文件结构` 段（约第 544 行）追加：

````markdown
### Lesson 文件结构 (Phase 5 产出，跨项目持久化)

```
~/.claude/mission-archive/{project-slug}/lessons/
└── {YYYY-MM-DD}-{topic-kebab}.md
```

每个 lesson 文件：

```markdown
---
name: {topic-kebab-case}
description: 一句话描述，用于 Phase 0 glob 时模糊匹配
mission_date: YYYY-MM-DD
keywords: [关键词1, 关键词2, ...]   # 用于 Phase 0 的命中判断
---

# Lesson: {一句话核心结论}

**Context:** {本次 mission 的简短背景}

**Lesson (≤150 字):**
{真正可复用的洞察，不是行动清单。强调"下次遇到 X 类情况要 Y"}

**Source iteration:** {Iter N, 来源是 Decisions Made / Self-Reflections / Compliance Checks}
```

**严格 ≤150 字的理由：** Phase 0 glob 命中时会注入 Prior Lessons 段到 mission_plan.md，超长 lesson 会污染上下文。如果一条心得真的需要超过 150 字，说明它是"多条 lesson 的混合"，拆开写。
````

### Step 3A.2：把 Phase 5 完成作为 Mission Accomplished 硬前置

在 SKILL.md 的 "## Pre-Promise Audit Checklist (CRITICAL)" 表格中追加第 5 行（Task 1 已建好 4 行）：

```markdown
| 5 | Phase 5 Distill 已完成（archive 目录有本次 mission 的 lesson 文件） | **外部信号**（文件系统） | `ls ~/.claude/mission-archive/{slug}/lessons/{today}-*.md` 至少返回 1 条 |
```

并把段首文本"**4 项全部通过才允许发 promise**"改为"**5 项全部通过才允许发 promise**"。

### Step 3A.3：在 prompt-template.md notes 模板新增 Distilled Lessons 段

在 `references/prompt-template.md` 的 mission_notes.md Complete Template 末尾（`## Open Questions` 段之后、`## Audit Trail` 段之前）插入：

```markdown
## Distilled Lessons
[Phase 5 output - lesson files written to ~/.claude/mission-archive/{slug}/lessons/]
- 2026-05-23-refund-flow-architecture.md
  "退款状态机与订单状态机正交时应独立 Service"
  Source: Iter 3 Decisions Made
- 2026-05-23-search-rebuild-mock-shape.md
  "rebuildSearchIndex 测试的 mock 要返回 vectors.ids() iterable，不能只 mock add/remove"
  Source: Iter 2 Self-Reflections, Compliance Check escalate
```

### Step 3A.4：手动验证 mission

在 Prism-OS 或其他真实项目跑一个小 mission（不要在 sandbox 跑——因为我们要观察 distill 在真实场景下能否产出有价值的 lesson）。Mission 结束时检查：

```bash
ls "$HOME/.claude/mission-archive/prism-os/lessons/"
# 应有今天日期开头的 .md 文件
```

并检查文件内容是否 ≤150 字、是否含 frontmatter、是否真的可复用（不是"这次做了 X" 这种废话）。

如果 LLM 跑完 mission **直接发了 Mission Accomplished 而跳过 Phase 5**（即 archive 目录是空的）→ Step 3A.2 的 Audit 项 5 没生效，需要在 SKILL.md 强制段加更强语气：

```markdown
强制6: Phase 5 Distill 缺失等同于 Mission Failed
  -> 即使所有 Success Criteria 都 [x] 且 build pass，没有 Phase 5 lesson 也禁止发 promise
  -> 看不见 archive 目录文件 = mission 不算完
```

### Step 3A.5：CHANGELOG + commit

`CHANGELOG.md` 的 `[Unreleased]` 段追加：

```markdown
### Added
- **Phase 5: Distill** - mission 结束前必须蒸馏 1-3 条 ≤150 字 lesson 到 `~/.claude/mission-archive/{project-slug}/lessons/`. 跨项目持久化、跨任务学习的起点。
- **Pre-Promise Audit Checklist** 扩展至 5 项，新增"Phase 5 lesson 文件存在"作为外部信号。
- mission_notes.md 新增 `## Distilled Lessons` 段。
- Lesson 文件结构规范（frontmatter + ≤150 字正文 + Source iteration 引用）。
```

提交：

```bash
git -C "C:/Users/Administrator/.claude/skills/mission-runner" add SKILL.md references/prompt-template.md CHANGELOG.md
git -C "C:/Users/Administrator/.claude/skills/mission-runner" commit -m "feat: add Phase 5 Distill + cross-mission lesson archive (hard prereq for Mission Accomplished)"
```

---

## Task 3B：Phase 0 glob 历史 + 3-5 mission 观察期（改造 #2 第二步）

**Files：**
- Modify：`C:\Users\Administrator\.claude\skills\mission-runner\SKILL.md`（Phase 0 段；Step 1 Read-Before-Decide 段）
- Modify：`C:\Users\Administrator\.claude\skills\mission-runner\references\prompt-template.md`（Phase 0 段；mission_plan.md 模板）
- Modify：`C:\Users\Administrator\.claude\skills\mission-runner\CHANGELOG.md`

**Why：** Task 3A 让每次 mission **生产** lesson，但没让任何 mission **消费** lesson——闭环没合上。Task 3B 在 Phase 0 启动时 glob 当前项目的 archive 目录，把命中的 lesson 注入到 mission_plan.md `## Prior Lessons` 段，并强制 Step 1 Read-Before-Decide 读它。

**关键设计：模糊匹配用文件名 keyword 命中，不用 embedding。**理由：mission-runner 是纯 markdown skill，不能跑 embedding；keyword 命中虽然粗糙但零依赖、可调试、可解释。

### Step 3B.1：在 SKILL.md Phase 0 段加 glob 步骤

打开 `SKILL.md`，定位"## 工作流程"段的 `Phase 0: Initialization`（约第 637 行）。把原 Phase 0 的 5 步扩展为 7 步：

```markdown
Phase 0: Initialization (初始化)
├── 1. 解析用户任务描述
├── 2. 确定 project-slug:
│      git rev-parse --show-toplevel -> 末段目录名 kebab-case
│      (无 git 时用 cwd basename)
├── 3. Glob 历史 lessons (新增):
│      LessonsDir = ~/.claude/mission-archive/{slug}/lessons/
│      如果目录不存在 -> 跳过此步（首次 mission 情形）
│      否则读取所有 *.md 的 frontmatter:
│        - 提取每个文件的 keywords[] 和 description
│        - 与当前 task 描述做关键词匹配 (大小写不敏感、子串 OK)
│        - 命中阈值: 任务描述中出现 ≥1 个 keyword 或 description 关键词
│      把命中的 lesson (最多 5 条) 完整内容缓存
├── 4. 创建 _planning/ 目录: mkdir -p _planning
├── 5. 创建 mission_plan.md (任务计划):
│      包含新增 ## Prior Lessons 段:
│        - 列出 Step 3 命中的 lesson 文件名 + ≤150 字正文 + Source iteration
│        - 如果 Step 3 没命中 -> 写 "（无历史 lesson 命中此任务）"
├── 6. 创建 mission_notes.md (空笔记，含所有标准段)
└── 7. 启动迭代循环
```

### Step 3B.2：在 SKILL.md Step 1 Read-Before-Decide 段补 Prior Lessons 读取

定位"工作流程"段中 Step 1 Read-Before-Decide 框（约第 649 行）。把原文：

```
│  Read _planning/mission_plan.md                              │
│  - 确认: Objective 是什么？                                   │
│  - 确认: 当前在哪个 Phase？                                   │
│  - 确认: 下一个未完成 [ ] 任务是什么？                         │
```

替换为：

```
│  Read _planning/mission_plan.md                              │
│  - 确认: Objective 是什么？                                   │
│  - 确认: 当前在哪个 Phase？                                   │
│  - 确认: 下一个未完成 [ ] 任务是什么？                         │
│  - **检查: ## Prior Lessons 段有命中 lesson 吗？**            │
│    如果有 -> 当前任务是否触发某条 lesson 的适用条件？          │
│    触发 -> 把 lesson 内容作为 Confidence Check 的输入信号     │
```

### Step 3B.3：在 prompt-template.md Phase 0 段同步

打开 `references/prompt-template.md`，定位 `Phase 0: Initialization`（约第 38 行）。把原 4-5 步扩展为 7 步（结构与 Step 3B.1 一致）：

```markdown
1. Determine project-slug:
   `git rev-parse --show-toplevel` -> last segment, kebab-case (lowercase)
   (Fall back to cwd basename if not in git repo)

2. Glob historical lessons:
   LessonsDir = ~/.claude/mission-archive/{slug}/lessons/
   - If dir doesn't exist: skip (first mission for this project)
   - Otherwise read all *.md frontmatter:
     * Extract keywords[] and description
     * Match against current task description (case-insensitive substring)
     * Hit threshold: task contains ≥1 keyword OR description token
   - Cache up to 5 hits with full content

3. Create planning directory: mkdir -p _planning

4. Create _planning/mission_plan.md:
   - Objective: extract from task
   - Success Criteria
   - Phases
   - Progress Log (empty)
   - **## Prior Lessons (new):**
     * If step 2 had hits: paste full lesson body + filename + Source iteration
     * If no hits: write "(no historical lessons matched this task)"

5. Create _planning/mission_notes.md with all standard sections

6. Create _planning/workflow_state.json (optional)

7. Start iteration loop
```

### Step 3B.4：在 prompt-template.md mission_plan.md 模板加 Prior Lessons 段

在 `references/prompt-template.md` 的 `## mission_plan.md Complete Template` 中，把现有模板的 `## Context` 段和 `## Phases` 段之间插入：

```markdown
## Prior Lessons
[Phase 0 step 2 output - lessons globbed from ~/.claude/mission-archive/{slug}/lessons/]
[If no hits: "(no historical lessons matched this task)"]

### lesson: refund-flow-architecture (2026-05-23)
> Mission-archive 来源，已在 Phase 0 命中。Step 1 Read-Before-Decide 时必须读这段。

**Lesson (≤150 字):**
退款的状态机和 Order 状态机正交（退款审批/部分退款/退款失败重试 vs 订单创建/支付/发货）；
强行塞进 OrderService 会让单一职责崩溃。下次遇到"X 是 Y 的子流程？"问题时，
先画状态机：状态机正交 → 独立 Service；状态机嵌套 → 子方法即可。

**Source:** 2026-05-23 mission Iter 3 Decisions Made
**File:** ~/.claude/mission-archive/prism-os/lessons/2026-05-23-refund-flow-architecture.md
```

### Step 3B.5：3-5 mission 观察期 + 执行率统计

Task 3B 代码改完后**不立即合并**，先在 Prism-OS（或任意真实项目）跑 3-5 个真实 mission。每个 mission 完成后记录：

| 指标 | 含义 | 收集方式 |
|------|------|----------|
| `phase5_attempted` | mission 是否走到 Phase 5 | 看 mission_notes.md > Distilled Lessons 段是否非空 |
| `phase5_completed` | Phase 5 是否产出至少 1 个 lesson 文件 | `ls ~/.claude/mission-archive/{slug}/lessons/{today}-*.md` |
| `phase0_glob_run` | Phase 0 是否真的尝试 glob 历史 | 看 mission_plan.md > Prior Lessons 段是否存在（即使是"no hits"） |
| `phase0_glob_hit` | 历史 lesson 是否命中当前任务 | mission_plan.md > Prior Lessons 段是否含真实 lesson 内容（而非"no hits"） |
| `lesson_consumed` | 命中的 lesson 是否真的影响了执行 | 在 mission_notes.md 搜"Prior Lesson"、"Lesson"等关键词作为引用证据 |

每个 mission 完成后追加到 `docs/plans/2026-05-23-self-improvement.md` 末尾新增的 `## Task 3B Observation Log` 段：

```markdown
## Task 3B Observation Log

| Date | Mission | phase5_attempted | phase5_completed | phase0_glob_run | phase0_glob_hit | lesson_consumed | Notes |
|------|---------|------------------|------------------|-----------------|-----------------|-----------------|-------|
| 2026-05-24 | Add geo tagging to memory | y | y | y | n | n/a | 首次 mission，archive 空 |
| 2026-05-25 | Refactor recall path | y | n | y | n | n/a | Phase 5 被跳过！|
| ...
```

### Step 3B.6：决策门槛

跑完 5 个 mission 后统计：

- **Distill 执行率** = `phase5_completed / phase5_attempted`
- **Glob 命中率** = `phase0_glob_hit / (phase0_glob_run - 首次空 archive 次数)`
- **Lesson 消费率** = `lesson_consumed / phase0_glob_hit`

决策规则：

| 场景 | Distill 执行率 | Glob 命中率 | Lesson 消费率 | 行动 |
|------|----------------|-------------|---------------|------|
| 理想 | ≥ 70% | 任意 | 任意 | 合并 Task 3B，结束计划 |
| Distill 经常被跳 | < 70% | 任意 | 任意 | **加禁令6**：Phase 5 缺失即 Mission Failed（见 Step 3A.4 备选）|
| Distill 稳但没命中 | ≥ 70% | < 20%（数据量 ≥ 5 次非首次时） | 任意 | 跑更多 mission 累积；如果 1 个月后仍 < 20%，关键词匹配太严，加同义词扩展或换 fuzzy |
| 命中但不消费 | ≥ 70% | ≥ 20% | < 50% | Step 3B.2 的 Prior Lessons 读取没生效，加重 Step 1 Read-Before-Decide 的语气 |

### Step 3B.7：CHANGELOG + commit

观察期通过后，`CHANGELOG.md` 的 `[Unreleased]` 段追加：

```markdown
### Added
- **Phase 0 historical lesson glob** - Phase 0 启动时按 project-slug 查询 `~/.claude/mission-archive/{slug}/lessons/`, 关键词匹配命中的 lesson 注入到 mission_plan.md `## Prior Lessons` 段。
- Step 1 Read-Before-Decide 强制读 `## Prior Lessons` 并作为 Confidence Check 输入。
- mission_plan.md 模板新增 `## Prior Lessons` 段。
- Observation Log（仅本计划文档内）记录 distill / glob / consumption 三项指标。
```

观察期通过后把 `[Unreleased]` 改为 `[1.1.0] - YYYY-MM-DD`（实际日期取决于观察期长度），并更新 SKILL.md 顶部 frontmatter 的 description（如果增加了关键能力描述）。

提交：

```bash
git -C "C:/Users/Administrator/.claude/skills/mission-runner" add SKILL.md references/prompt-template.md CHANGELOG.md docs/plans/2026-05-23-self-improvement.md
git -C "C:/Users/Administrator/.claude/skills/mission-runner" commit -m "feat: close cross-mission learning loop with Phase 0 lesson glob + Prior Lessons injection"
```

---

## Self-Review

按 writing-plans 要求做 spec coverage / placeholder / type consistency 三项自检：

### 1. Spec coverage（spec = 上一条回复确认的 3 项强化 + 用户追加的 RiderMcp 清理）

| Spec 要求 | 对应 Task / Step | 状态 |
|-----------|------------------|------|
| 用户追加: 清理 mission-runner 里的 RiderMcp 残留 | Task 0（5 个 step，删 2 文件 + 改 SKILL.md 三处） | ✓ |
| #6: Pre-Promise Audit Checklist（4 项外部信号） | Task 1（含 git diff 外部信号、命令输出可追溯） | ✓ |
| #1 缩水版: Step 3 后加 ~10 行 diff-vs-plan 自检 prompt | Task 2（Step 2.1 插入 Step 3.6，含 Q1/Q2 + Verdict） | ✓ |
| #1 后续: 一周验证后决定升级 subagent 与否 | Task 2 Step 2.7（观察节点 + 升级规则） | ✓ |
| #2 第一步: distill + 强制为 Mission Accomplished 前置 | Task 3A（Phase 5 + Audit 项 5） | ✓ |
| #2 第二步: Phase 0 glob 历史 | Task 3B Step 3B.1-3B.4 | ✓ |
| 跑 3-5 mission 看执行率 | Task 3B Step 3B.5 (Observation Log) | ✓ |
| distill 执行率 ≥ 70% 才继续；否则把"distill 失败强制 retry"写进禁令 | Task 3B Step 3B.6 决策表（Distill < 70% → 加禁令6） | ✓ |

无 spec 缺口。

### 2. Placeholder scan

扫描"TBD / TODO / fill in later / implement later / similar to / add appropriate":
- 全文搜过，没有未实现的 placeholder。
- Task 2 Step 2.7 升级方案"先不写进 plan，等观察期数据决定"是有意的——这不是 placeholder，是显式的"先观察再设计"决策。
- Task 3B Step 3B.6 决策表覆盖了所有可能的观察结果分支，没有遗漏情形。

### 3. Type consistency（路径 / 命名一致性）

- `project-slug` 在 Task 3A 和 Task 3B 中定义一致（`git rev-parse --show-toplevel` 末段 kebab-case，无 git 时退化）✓
- archive 路径在所有 Task 中统一为 `~/.claude/mission-archive/{slug}/lessons/`（Unix 风格）；Windows 用户实际是 `%USERPROFILE%\.claude\mission-archive\{slug}\lessons\`，在 SKILL.md Step 3A.1 已注明 ✓
- Audit Checklist 行数从 4 → 5（Task 1 建 4 行，Task 3A 加第 5 行），文本"5 项全部通过"在 Task 3A Step 3A.2 显式更新 ✓
- 强制段从"三大强制"→"五大强制"（Task 2 Step 2.2 显式更新标题）；Task 3A Step 3A.4 备选的"强制6"如果触发，再升级为"六大强制" ✓
- Lesson 文件结构（frontmatter + ≤150 字正文）在 Task 3A 定义、在 Task 3B mission_plan.md 模板和 Phase 0 glob 引用中一致 ✓

无不一致。

---

## 风险与回退策略

| 风险 | 触发信号 | 回退动作 |
|------|----------|----------|
| Task 0 删除后发现某段 RiderMcp 内容其实有通用价值 | 后续做 Prism-OS mission 时发现某条 Self-Reflection 模式确实想复用 | 不回滚 Task 0（删的对）；改为在 Task 3A 的 Phase 5 Distill 重新蒸馏出通用版（去 Kotlin/Unity 上下文），写入 archive 目录 |
| Task 1 的 Pre-Promise Audit 仍被 LLM 绕过 | 跑验证 mission 时 promise 仍被发 | 把"强制4"语气加重为"违反此 checklist = 任务失败，禁止继续操作"，并把 Audit Trail 段写入 SKILL.md 模板的强制部分 |
| Task 2 的 Compliance Check 没接住 drift | 一周后 N_missed ≥ 1 | 不立即派 subagent，先把 Q2 的判定标准量化（"diff 行数 / 任务影响范围比 > 3 即视为 drift"）；再不灵才升级 subagent |
| Task 3A 的 Distill 被跳过 | archive 目录空 | 启用 Task 3A Step 3A.4 备选的"强制6"+ Audit 项 5 必须含文件存在校验 |
| Task 3B 的 glob 误命中 / 漏命中 | Lesson 消费率 < 50% 但命中率 > 50% | 在 lesson frontmatter 加 `applicability_check` 字段（一句话条件），Step 1 Read-Before-Decide 时先评估条件再决定是否纳入 Confidence Check |

每个 Task 都是独立 commit，任一步 revert 不影响其他 Task。最坏情况：3 个 commit 全 revert，回到当前 v1.0.0 状态。

---

## Execution Handoff

计划完整保存在 `C:\Users\Administrator\.claude\skills\mission-runner\docs\plans\2026-05-23-self-improvement.md`。

执行方式建议：

**选项 1（推荐）：手动顺序执行，每个 Task 一个会话**
- Task 0：1 个会话，~30 分钟（纯删除/改 frontmatter，无新逻辑）
- Task 1：1 个会话，~1 晚
- Task 2：1 个会话，~1 晚
- Task 3A：1 个会话，~半天
- Task 3B 改造部分：1 个会话，~半天
- Task 3B 观察期：3-5 个真实 mission 跨度（不阻塞其他工作）

理由：每个 Task 修改文件少，改动可在一次会话内 review-and-commit。无需派 subagent。**强烈建议 Task 0 优先**——把 RiderMcp 噪音清掉后，后续 Task 在干净的 skill 上做改造，验证 mission 也不会被无关概念污染。

**选项 2：mission-runner 自举执行**
- 用 mission-runner 自己（当前 v1.0.0）来执行本计划——把本计划文档作为 mission_plan.md 的 input。
- 元-趣味性高，但有循环依赖风险（如果当前 v1.0.0 有 bug，执行计划时可能放大）。
- **Task 0 绝对不要用自举**——当前 v1.0.0 的 SKILL.md 里 RiderMcp 内容会污染自举出来的 mission 计划。Task 0 必须手动做。
- 建议至少 Task 0 + Task 1 完成后再考虑自举执行 Task 2 / Task 3。

无论哪种执行方式，**Task 之间必须独立 commit**，避免一次提交多个 Task 导致回退颗粒度过大。

---

## Task 3B Observation Log

（Task 3B Step 3B.5 落地后开始填写。当前为空。）

| Date | Mission | phase5_attempted | phase5_completed | phase0_glob_run | phase0_glob_hit | lesson_consumed | Notes |
|------|---------|------------------|------------------|-----------------|-----------------|-----------------|-------|
| - | - | - | - | - | - | - | - |
