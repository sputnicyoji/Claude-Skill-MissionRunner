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


# Mission Runner

> **task-planner + ralph-loop + PIR 的终极融合**
>
> 核心理念：**文件系统作为记忆 × 每次决策前读取计划 × 失败是学习数据**

## 核心哲学 (PIR - Plan-Iterate-Resolve)

```
Filesystem as Memory    - 本地文件，而非 context window
Plan-First-Always       - 先创建计划，防止目标漂移
Read-Before-Decide      - 每次决策前重读计划文件
Failures are Data       - 失败记录供下次迭代学习
Uncertainty is Signal   - 不确定时主动询问，不要猜测
Reflect-Before-Retry    - 失败后先反思，再重试 (Reflexion)
```

## 激活条件

当用户提到以下关键词时，本 Skill 应被激活：
- 大任务、复杂任务、大型模块
- 自动完成、自动迭代、mission
- 多层架构、跨模块、重构
- "帮我实现..."（涉及 3+ 文件）

## 默认配置

```yaml
max_iterations: 3              # 默认迭代次数
completion_promise: "Mission Accomplished"  # 完成标志
planning_dir: "_planning"      # 计划文件目录
```

## 四大禁令 (CRITICAL)

```
禁令1: 禁止迭代开始时不读取计划文件
  -> 必须先 Read _planning/mission_plan.md
  -> 必须确认当前阶段和下一个未完成任务

禁令2: 禁止静默跳过验证错误
  -> 每次迭代必须验证（编译/lint/测试）
  -> 验证失败必须记录到 mission_notes.md

禁令3: 禁止迭代结束时不更新进展
  -> 必须更新 mission_plan.md 的 checkbox 和 Progress Log
  -> 必须追加发现/错误到 mission_notes.md

禁令4: 禁止低置信度时猜测执行
  -> 置信度 < 3 分时必须 AskUserQuestion
  -> 禁止在不确定需求/方案/依赖时盲目实现
```

## 五大强制 (MUST)

```
强制1: 必须在迭代开始时执行 Read-Before-Decide
  -> Read _planning/mission_plan.md
  -> 确认目标、当前阶段、下一个任务

强制2: 必须在 Step 3.6 verdict=pass 之后才标记任务 [x]
  -> Step 2 Execute 完成时仅更新 Progress Log，**不勾 [x]**
  -> 标记 [x] 的唯一时机: Step 3 build pass + Step 3.6 verdict=pass
  -> 这样 [x] 是"代码运行 + 实现正确"两道闸门的合成信号
     而非"我做了什么"的口头汇报

强制3: 必须在任务完成时输出 Mission Accomplished
  -> 格式: <promise>Mission Accomplished</promise>
  -> 只有所有任务完成且 5 项 audit 全过才能输出

强制4: 必须在发 Mission Accomplished 之前通过 Pre-Promise Audit Checklist
  -> 见下方 "Pre-Promise Audit Checklist (CRITICAL)" 段
  -> 5 项中任一未通过 -> 禁止发 promise，输出 Partial Report

强制5: 必须在每次 build pass 之后执行 Step 3.6 Compliance Check
  -> 见工作流段的 Step 3.6 框
  -> 跳过 Compliance Check 等同于跳过 Step 3 Validate
  -> Verdict 必须写入 mission_notes.md > Compliance Checks
  -> Verdict ≠ pass 时禁止勾本任务 [x]，禁止进入 Step 4 "all done" 分支

注: 强制 2 / 强制 4 / 强制 5 在 Escape Hatch (mode=free_form) 下仍然生效
    —— 它们是协议层硬约束, 与状态机的"建议路径"无关。详见 Escape Hatch 段
    "escape hatch 不豁免的硬约束 (CRITICAL)"。
```

## Pre-Promise Audit Checklist (CRITICAL)

**在输出 `<promise>Mission Accomplished</promise>` 之前必须逐项核对，5 项全部通过才允许发 promise。本 checklist 在 Escape Hatch (mode=free_form) 下仍然生效——见 Escape Hatch 段。**

| # | 检查项 | 信号来源 | 通过条件 |
|---|--------|----------|----------|
| 1 | mission_plan.md 所有 Phase 任务标记 [x] | 内部（plan 文件） | 全文搜 `^- \[ \]` 应为 0 行 |
| 2 | mission_plan.md 所有 Success Criteria 标记 [x] | 内部（plan 文件） | Success Criteria 段无 `[ ]` |
| 3 | `git diff --stat` / `git status` 显示有实质改动 | **外部信号**（git） | 至少 1 个文件 modified/added |
| 4 | Build/lint/test 命令真实执行并通过 | 外部信号（命令输出） | Progress Log 最近一项含 `verified: pass` 或同等记录 |
| 5 | Phase 5 Distill 已完成 (archive 目录有本次 mission 的 lesson 文件) | **外部信号**（文件系统） | 设 `TODAY` = ISO 当日 (`date +%Y-%m-%d` / `Get-Date -Format yyyy-MM-dd`); Bash: `ls ~/.claude/mission-archive/{slug}/lessons/${TODAY}-*.md`; PowerShell: `Get-ChildItem "$env:USERPROFILE\.claude\mission-archive\{slug}\lessons\$TODAY-*.md"`; 任一 shell 至少返回 1 条 |

**任一项未通过：**
- 不输出 `<promise>Mission Accomplished</promise>`
- 改为输出 Partial Report，列出：哪一项未通过、原因、下一步建议
- 把审计结果追加到 mission_notes.md 新增的 `## Audit Trail` 段

**为什么必须有"外部信号"（项 3、项 4、项 5）：**
LLM 自报"已完成"是不可信的——存在 hallucinate 完成度的常见失败模式（checkboxes 全勾但 git diff 是空的；或宣称 distill 完成但 archive 目录是空的）。`git diff`、命令执行输出、文件系统状态都是 LLM 不能伪造的外部状态，是最强的反 hallucination 信号。

**为什么项 5 是硬前置：**
Phase 5 Distill 是最容易被 LLM 跳过的步骤（典型"收尾清理"心理），而 distill 失败 → 跨任务学习层（Task 3B 即将引入的 Phase 0 glob）永远是空——闭环断在生产端。项 5 用文件系统作为外部信号，确保 distill 真的发生。

## 置信度检查协议 (Confidence Check Protocol)

**每次迭代的 Execute 阶段前，必须进行置信度自评估。**

### 评估维度 (V1 - 结构化检查)

| 维度 | 评估问题 | 低分信号 (1-2分) |
|------|----------|------------------|
| **任务理解** | 当前任务是否完全理解？ | 需求有歧义、边界不清 |
| **方案确定性** | 实现方案是否唯一明确？ | 有多个等价方案、不知道选哪个 |
| **依赖清晰度** | 依赖的模块/接口是否明确？ | 不知道用哪个 API、调用顺序不确定 |
| **风险预估** | 潜在问题是否可控？ | 可能影响其他功能、不确定副作用 |

### 置信度等级 (V2 - 自动决策)

```
平均分计算: (任务理解 + 方案确定性 + 依赖清晰度 + 风险预估) / 4

🟢 高置信度 (平均 >= 4分): 直接执行
   -> 无需用户干预，继续工作流

🟡 中置信度 (平均 3-4分): 记录疑点，继续执行
   -> 将疑点记录到 mission_notes.md
   -> 执行时优先选择保守方案

🔴 低置信度 (平均 < 3分): 暂停并询问用户
   -> 使用 AskUserQuestion 列出具体疑问
   -> 等待用户澄清后继续
   -> 将澄清记录到 mission_notes.md 的 Clarifications 章节
```

### 典型低置信度场景

```
场景1: 需求歧义
  "添加退款功能" - 部分退款还是全额？需要审批流程吗？
  -> 必须询问

场景2: 多方案等价
  存储用 Map 还是 Object？状态管理用 Redux 还是 Zustand？
  -> 必须询问用户偏好

场景3: 依赖不明
  应该放在 services/ 还是 utils/？
  -> 必须探索后确认，或询问

场景4: 风险不可控
  修改可能影响其他正在使用的功能
  -> 必须告知用户风险
```

---

## 自我反思协议 (Self-Reflection Protocol)

> 基于 [Reflexion 论文 (NeurIPS 2023)](https://arxiv.org/abs/2303.11366) 的语义梯度学习

**核心理念**: 失败后不是简单重试，而是先生成文字反思，将反思作为"语义梯度"指导下次尝试。

### Self-Reflection Prompt 模板

```
你是软件开发助手。分析这次失败：

## 失败的代码
{code_snippet}

## 错误信息
{error_message}

## 反思要求
用 2-3 句话回答：
1. 为什么这个实现失败了？（根本原因）
2. 下次应该怎么修改？（具体方案）
3. 有没有类似的坑需要避免？（举一反三）

只写反思，不写代码。
```

### 错误类型分类与策略选择

| 错误类型 | 示例 | 策略 | 重试限制 |
|----------|------|------|----------|
| **简单错误** | TS2307 缺少 import, typo, 语法错误 | 立即修复，同一迭代 | 2 次 |
| **中等错误** | TypeError, 逻辑错误, 边界条件 | 记录反思，下次迭代 | 1 次 |
| **复杂错误** | 架构不匹配, 需求理解偏差 | AskUserQuestion | 0 次 |
| **连续失败** | 同类错误连续 3 次 | AskUserQuestion | 强制 |

### 策略执行逻辑

```
if 错误类型 == 简单:
    if 本迭代重试次数 < 2:
        生成反思 -> 立即修复 -> 返回 Step 2
    else:
        记录反思 -> 进入 Step 4 (下次迭代处理)

elif 错误类型 == 中等:
    生成反思 -> 记录到 notes -> 进入 Step 4

elif 错误类型 == 复杂 or 连续失败 3 次:
    生成反思 -> AskUserQuestion 确认方向 -> 等待用户
```

### 反思记录格式

```markdown
## Self-Reflections
- [Iter 2, Attempt 1] TS2307: Cannot find module '@/services/refund'
  反思: 文件创建了但路径别名配置错误，应该检查 tsconfig.json 的 paths 配置
  策略: 立即修复
  状态: 已修复

- [Iter 2, Attempt 2] TypeError: Cannot read property 'id' of undefined
  反思: order 对象在某些情况下可能为空，需要添加空值检查
  策略: 记录待处理
  状态: 待下迭代

- [Iter 3] 架构冲突: 退款逻辑应该放在 OrderService 还是单独的 RefundService？
  反思: 两种方案各有优劣，OrderService 简单但职责不单一，RefundService 更清晰但增加复杂度
  策略: 询问用户
  状态: 等待澄清
```

### 反思记忆管理

```
最大保留数量: 3 条 (参考 Reflexion 论文)
超出时: 移除最旧的反思
跨迭代: 每次 Read-Before-Decide 时检查历史反思
```

---

## 工具选择策略 (CRITICAL)

**Research 阶段推荐使用 Task subagent 进行探索，避免在主对话中大量使用搜索工具。**

### 何时使用 Task subagent (Claude Code)

| 阶段 | 任务类型 | 推荐工具 |
|------|----------|----------------|
| Research | 探索模块架构 | `Task(subagent_type="Explore")` |
| Research | 设计实现方案 | `Task(subagent_type="Plan")` |
| Verification | 代码审查 | `Task(subagent_type="code-reviewer")` |

### Task subagent 调用方式 (Claude Code)

不是 Python 代码; 是描述给主对话 LLM 如何发起 Task tool 调用的指引:

- 探索代码库: 调用 Task tool, 设置 `subagent_type` 为 `Explore`,
  `prompt` 字段填"探索 {目标模块} 的数据流和核心类"等等。
- 架构设计: 调用 Task tool, 设置 `subagent_type` 为 `Plan`,
  `prompt` 字段填"基于探索结果, 设计 {新功能} 的实现蓝图"。
- 代码审查: 调用 Task tool, 设置 `subagent_type` 为 `code-reviewer`,
  `prompt` 字段填具体审查目标。

不要把上面这些当作字符串去输出或写入文件——它们是工具调用的字段映射,
应该通过实际的 Task tool_use 发起。

### 禁止的 Research 模式

```
禁止: 在主对话中连续执行 10+ 次搜索/读取探索
原因: 消耗主对话上下文，降低后续执行质量
正确: 启动 Task subagent，让子进程处理探索，只接收结构化报告
```

---

## 迭代状态输出 (MUST) - 可见性协议

**每次迭代必须输出状态摘要，让用户能在控制台观察进度变化。**

### 迭代开始时输出

```
====================================================================
ITERATION N | Read-Before-Decide
====================================================================

## Objective
[从 mission_plan.md 提取]

## Current Progress
Phase 1: Research [2/3 done]
- [x] 理解需求
- [x] 探索代码
- [ ] 识别约束  <-- 当前任务

Phase 2: Implementation [0/3 done]
- [ ] 任务1
- [ ] 任务2

## Confidence Check (当前任务)
| 维度 | 分数 | 说明 |
|------|------|------|
| 任务理解 | 4 | 需求清晰 |
| 方案确定性 | 3 | 有两种方案待定 |
| 依赖清晰度 | 5 | API 明确 |
| 风险预估 | 4 | 影响范围可控 |
| **平均** | **4.0** | 🟢 继续执行 |

## Last Iteration Notes
- [Iter N-1] 发现 xxx，决定 yyy

====================================================================
```

### 迭代结束时输出

```
--------------------------------------------------------------------
ITERATION N | Checkpoint
--------------------------------------------------------------------

## This Iteration
- 完成: [具体做了什么]
- 遇到: [问题/发现]
- 下一步: [下个任务是什么]

## Updated Progress
Phase 1: Research [3/3 done] DONE
Phase 2: Implementation [1/3 done]

## Notes Changes (本轮新增)
### Failures & Learnings
- [Iter N] TS2307: Cannot find module xxx
  -> 原因: 缺少路径配置
  -> 方案: 更新 tsconfig.json paths
  -> 状态: 已修复

### Research Findings
- [Iter N] 发现 xxx 模块在 yyy 目录

### Decisions Made
- [Iter N] 决定使用 zzz 方案，因为...

### Self-Reflections (本轮 Step 3.5 产出)
- [Iter N, Attempt 1] {错误信息}
  反思: {根本原因 + 改进方案}
  策略: {立即修复 / 记录待处理 / 询问用户}

### Compliance Checks (本轮 Step 3.6 verdict)
- [Iter N] Task: "{任务名}"
  Verdict: {pass / needs-revision / escalate}

### Distilled Lessons (仅 Phase 5 完成时填)
- {YYYY-MM-DD}-{topic-kebab}.md
  "一句话摘要"

### Audit Trail (仅 promise 尝试时填)
- [Iter N, Attempt M] Audit item X failed (原因) / All 5 passed

### Deviations & Reasons (仅 escape hatch 触发时填)
- [Iter N] Trigger: ... → mode=free_form, 硬约束仍生效

--------------------------------------------------------------------
```

**关键**: Notes Changes 必须显示本轮实际新增的条目内容，不能只说"文件已更新"。

---

## 工作流状态机 (Workflow State Machine)

> 基于 [LangGraph State Machine](https://www.langchain.com/langgraph) 的显式状态定义

**核心理念**: 状态机是**指导建议**而非**强制约束**。提供审计、中断恢复、可视化能力，但 Agent 保留完全自主决策权。

### 设计哲学：建议模式 (Advisory Mode)

```
┌─────────────────────────────────────────────────────────────┐
│  状态机 = 导航地图，不是铁轨                                    │
│  - 提供推荐路径，但允许 Agent 根据情况绕行                       │
│  - 记录实际路径，用于审计和学习                                 │
│  - 异常情况可触发"逃逸舱"回到自由模式                           │
└─────────────────────────────────────────────────────────────┘
```

**何时可以偏离状态机：**
- Agent 置信度评估与预设路径冲突
- 发现更高效的执行路径
- 用户明确要求跳过某步骤
- 外部环境变化（如发现代码已被修改）

### 状态机定义

```yaml
# workflow_state_machine.yaml
name: mission-runner-pir
version: "2.1"

states:
  init:
    description: "Phase 0 初始化: slug 推导, 历史 lesson glob, 创建 _planning/"
    next: read_before_decide

  read_before_decide:
    description: "读取 plan + notes + Prior Lessons, 锚定目标"
    next: confidence_check

  confidence_check:
    description: "评估当前任务置信度 (含 Prior Lessons 信号)"
    transitions:
      high: execute           # >= 4 分
      medium: execute         # 3-4 分 (带记录)
      low: ask_user           # < 3 分

  ask_user:
    description: "等待用户澄清"
    next: confidence_check    # 澄清后重新评估

  execute:
    description: "Step 2: 执行任务 (不勾 [x])"
    next: validate

  validate:
    description: "Step 3: build / lint / test 验证"
    transitions:
      pass: compliance_check   # build pass 后必须进 Step 3.6
      fail: self_reflection

  compliance_check:
    description: "Step 3.6: diff vs 任务描述的 verifier"
    transitions:
      pass: checkpoint_mark    # 勾 [x] + 进 Step 4
      needs_revision: read_before_decide  # 不勾 [x], 追加修正子任务, 下迭代
      escalate: self_reflection           # 视为 medium error

  self_reflection:
    description: "Step 3.5: 失败/escalate 后的反思"
    transitions:
      simple_error: execute     # 立即重试 (同一迭代)
      medium_error: checkpoint  # 记录, 不勾 [x], 进 Step 4 (会因任务未完成转入 read_before_decide)
      complex_error: ask_user   # 需要用户澄清

  checkpoint_mark:
    description: "Step 3.6 pass 后勾 [x] + Progress Log"
    next: checkpoint

  checkpoint:
    description: "Step 4: 检查任务/Success Criteria 是否全完成"
    transitions:
      all_tasks_complete: debrief   # 进 Phase 4 Debrief
      continue: read_before_decide  # 下一迭代
      max_iterations: report        # 达到最大迭代

  debrief:
    description: "Phase 4: 确认 Success Criteria 全 [x]"
    next: distill

  distill:
    description: "Phase 5: 从 notes 蒸馏 1-3 条 lesson 写入 archive (含碰撞保护)"
    next: audit

  audit:
    description: "Pre-Promise Audit Checklist (5 项)"
    transitions:
      all_pass: done
      any_fail: report   # Partial Report, 追加 Audit Trail

  done:
    description: "任务完成"
    output: "<promise>Mission Accomplished</promise>"

  report:
    description: "报告部分完成 / Partial Report"
    output: "剩余任务列表 + Audit 失败项 + 建议"
```

### 状态机可视化

```
init
  ↓
read_before_decide ←──────────────────────────┐
  ↓                                            │
confidence_check ──(low)──→ ask_user           │
  ↓ (high/medium)              ↓ (澄清后)       │
execute ←────────────────────┘                 │
  ↓                                            │
validate ──(fail)──→ self_reflection ──┐       │
  ↓ (pass)                              │      │
compliance_check ←─────────(escalate)──┤       │
  ↓ (pass)                              │      │
  ↓     (needs_revision)─────────────────────→ │  (回 read_before_decide)
  ↓                                     │      │
checkpoint_mark (勾 [x])                 │      │
  ↓                              (medium │      │
checkpoint                       error)  ↓      │
  ↓                              ──→ checkpoint
  ↓                              (simple_error→execute)
  ↓ (all_tasks_complete)                        │
debrief                                         │ (continue: 任务未完)
  ↓                                             │
distill (写 lesson 到 archive)                   │
  ↓                                             │
audit (5 项) ──(any_fail)──→ report             │
  ↓ (all_pass)                                  │
done <promise>                                  │
                                                │
checkpoint (continue) ─────────────────────────┘
checkpoint (max_iterations) ───→ report
ask_user (complex_error from self_reflection) ─→ (等待用户)
```

简化阅读路径:
- **理想路径**: init → read → confidence → execute → validate(pass) → compliance(pass) → mark[x] → checkpoint → debrief → distill → audit(pass) → done
- **build 失败**: validate(fail) → self_reflection → execute(retry) 或 checkpoint(下迭代)
- **goal drift**: compliance(escalate) → self_reflection → 同上
- **小返工**: compliance(needs_revision) → 不勾 [x] → read (下迭代继续此任务)

### 状态持久化

```json
// _planning/workflow_state.json (v2.2 canonical, 含 Step 3.6 / Phase 5 / audit / escape-hatch 状态)
// 本 schema 是单一权威; references/prompt-template.md 与 examples/_planning/workflow_state.json
// 必须与本结构对齐 (字段同名、缺省值同语义).
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

字段说明:
- `current_state`: 见下方枚举.
- `iteration`: 当前迭代号 (Phase 0 init 为 0; 第一次进 Step 1 起递增).
- `retry_count`: 本迭代 Step 3.5 Self-Reflection 立即修复重试计数 (上限 2).
- `phase`: `initialization` / `research` / `implementation` / `verification` / `debrief` / `distill`.
- `task_index`: 当前 Phase 内的任务序号 (0-based).
- `task_marked_done`: 当前任务的 [x] 是否已勾 — 只有 Step 3.6 verdict=pass 后才可置 true.
- `compliance_verdict`: 最近一次 Step 3.6 结果 — `null` / `"pass"` / `"needs-revision"` / `"escalate"`.
- `mode`: `"advisory"` (默认) / `"free_form"` (escape hatch 触发后置位; 此时状态机暂停, 但协议层硬约束仍生效 — 见 Escape Hatch 段).
- `confidence_scores`: Step 1.5 当前任务的 4 维度评分.
- `timestamp`: ISO 8601, 每次状态转换时更新.

合法 `current_state` 值: init / read_before_decide / confidence_check / ask_user / execute / validate / compliance_check / self_reflection / checkpoint_mark / checkpoint / debrief / distill / audit / done / report

### 状态机使用规则 (建议性)

```
1. [建议] 状态转换时更新 workflow_state.json - 便于中断恢复
2. [建议] 中断恢复: 读取 workflow_state.json，从 current_state 继续
3. [建议] 审计日志: 状态变化记录到 mission_notes.md Progress Log
4. [可选] 可视化: 状态机图可嵌入到任务报告中
5. [允许] 偏离路径时，记录原因到 mission_notes.md Decisions Made
```

### 逃逸舱机制 (Escape Hatch)

当状态机"卡住"或不适用时，可触发逃逸舱：

```yaml
escape_hatch:
  triggers:
    - agent_confidence < 0.3          # Agent 信心过低
    - iteration_count > max_iterations # 迭代过多
    - user_command: "free_form"        # 用户主动干预
    - path_conflict: true              # 推荐路径与实际冲突

  actions:
    fallback_to_free_form:
      description: "切换到自由执行模式，保留 mission_plan.md 作为目标参考"
      preserve:
        - mission_plan.md              # 保留目标
        - mission_notes.md             # 保留记录
      suspend:
        - workflow_state.json          # 暂停状态机追踪

    record_deviation:
      description: "记录偏离原因，继续执行"
      append_to: mission_notes.md
      section: "Deviations & Reasons"
```

**触发逃逸舱后：**
1. 状态机暂停 — `mode` 切换到 `free_form`，`current_state` 不再更新；
   Agent 自主选择执行步骤、可跳过 Step 1.5 / Step 3.5 的具体模板
2. mission_plan.md 仍是目标参考（用于回答"我在做什么"）
3. 退出 free_form 时，向 mission_notes.md 的 `## Deviations & Reasons` 段
   追加一条记录（含触发原因、原状态、偏离结果）

**escape hatch 不豁免的硬约束（CRITICAL）：**

下列三项即使在 free_form 下也必须遵守 — 它们属于协议层硬约束，**不是**状态机里的"建议路径"：

| 硬约束 | 出处 | 为什么不能 bypass |
|--------|------|-------------------|
| **强制 5: [x] timing**       | 见 "五大强制" | `[x]` 是"build pass + Compliance pass"的复合外部信号；free_form 下若直接勾 [x]，等于让 LLM 重新拿回伪造完成度的权力，整个 v1.1 反 hallucination 设计崩溃 |
| **Phase 5 Distill**          | 见 "Phase 5" 段 | 跨 mission 学习层的生产端；跳过 = 后续 mission 拿不到 Prior Lessons |
| **5 项 Pre-Promise Audit**   | 见 "Pre-Promise Audit Checklist" | 含 3 个外部信号（git diff / build output / lesson 文件存在），Audit 项 5 又依赖 Phase 5 — 三者锁在一起，任一缺失则 promise 必拒 |

简言之：**escape hatch 让状态机沉默，不让 audit 沉默**。LLM 想发 `<promise>Mission Accomplished</promise>`，仍然必须先跑完 Phase 4 → Phase 5 → 5 项 Audit；任一外部信号缺失就只能输出 Partial Report。

如果 escape hatch 触发后 Agent 判断"任务确实无法完成"（如需求被推翻、依赖被废弃）— 正确做法是**主动退出而非发 promise**：
1. 在 mission_notes.md 的 `## Deviations & Reasons` 段记录 `Outcome: abandoned`，说明退出原因 (这是 abandon 的权威记录段)
2. 在 `## Audit Trail` 段追加一条索引行 `[Iter N] No promise issued — abandoned, see Deviations & Reasons` (便于将来扫 mission 状态时一站式查到)
3. 把 mission_plan.md 未勾任务保留为 `[ ]`，供后续 mission 接手
4. 输出 Partial Report (而不是 `<promise>Mission Accomplished</promise>`)，明确告知 caller 任务已 abandon

---


## 文件结构

```
_planning/                    # 任务规划目录 (迭代持久化, 单次 mission)
├── mission_plan.md          # 任务计划 + 成功标准 + 进度日志
├── mission_notes.md         # 研究发现 + 决策 + 失败记录 (append-only)
└── workflow_state.json      # 状态机当前位置 (支持中断恢复)

~/.claude/mission-archive/   # 跨 mission 知识沉淀 (跨项目持久化)
└── {project-slug}/
    └── lessons/
        └── {YYYY-MM-DD}-{topic-kebab}.md   # Phase 5 产出, 单条 ≤150 字
```

### Lesson 文件结构 (Phase 5 产出，跨项目持久化)

每个 lesson 文件采用统一 frontmatter，便于后续 (Task 3B) Phase 0 glob 时做关键词匹配：

```markdown
---
name: {topic-kebab-case}
description: 一句话描述，用于 Phase 0 glob 时模糊匹配
mission_date: YYYY-MM-DD
keywords: [关键词1, 关键词2, ...]
---

# Lesson: {一句话核心结论}

**Context:** {本次 mission 的简短背景}

**Lesson (≤150 字):**
{真正可复用的洞察，不是行动清单}
{强调"下次遇到 X 类情况要 Y"的可迁移性}

**Source:** Iter N, from {Decisions Made / Self-Reflections / Compliance Checks}
```

**严格 ≤150 字的理由：** Phase 0 glob 命中时会把 lesson 注入 mission_plan.md 的 Prior Lessons 段（Task 3B 落地后）。超长 lesson 污染上下文。如果一条心得真的需要超过 150 字，说明它是"多条 lesson 的混合"，应当拆开成多个文件而非合并。

**slug 推导规则：**
- 在 git 仓库内：`git rev-parse --show-toplevel` 末段目录名 → 小写 → kebab-case
- 不在 git 仓库内：`pwd` 末段目录名 → 小写 → kebab-case
- 示例：`E:\Yoji\Prism-OS` → `prism-os`；`/Users/foo/My App` → `my-app`

### mission_plan.md 模板

```markdown
# Mission Plan

## Objective
[任务目标 - 从用户请求中提取]

## Success Criteria
- [ ] [具体可验证的成功标准1]
- [ ] [具体可验证的成功标准2]
- [ ] [验证通过 (编译/lint/测试)]

## Context
- 模块路径: src/modules/xxx/
- 涉及架构层: Data/Service/UI
- 相关约束: [项目特定约束]

## Prior Lessons
[Phase 0 step 3 产出: 从 ~/.claude/mission-archive/{slug}/lessons/ glob 命中的历史 lesson]
[未命中时写: "(no historical lessons matched this task)"]

## Phases

### Phase 1: Research & Discovery
- [ ] 理解完整需求
- [ ] 探索现有代码/上下文
- [ ] 识别依赖和约束

### Phase 2: Implementation
- [ ] [具体任务1]
- [ ] [具体任务2]
- [ ] [具体任务3]

### Phase 3: Verification
- [ ] 编译/Lint 验证
- [ ] 约束检查

## Progress Log
| Iteration | Phase | Actions Taken | Status |
|-----------|-------|---------------|--------|
| 1 | Init | Created planning structure | In Progress |
```

### mission_notes.md 模板

```markdown
# Mission Notes

## Research Findings
[追加发现，带时间戳]

## Decisions Made
[记录选择和理由]

## Failures & Learnings
[关键! 记录所有失败 - 供下次迭代学习]
- [时间] [什么失败了] -> [学到了什么] -> [下次尝试什么]

## Self-Reflections
[Reflexion 自反思记录 - 验证失败后的结构化反思]
- [Iter N, Attempt M] {错误信息}
  反思: {根本原因 + 改进方案 + 类似陷阱}
  策略: {立即修复 / 记录待处理 / 询问用户}
  状态: {已修复 / 待下迭代 / 等待澄清}

最大保留: 3 条 (超出时移除最旧)

## Compliance Checks
[Step 3.6 verdicts per build-pass iteration - structured goal-drift detector]
- [Iter N] Task: "..."
  Diff files: [...]
  Q1 (实现完整度): complete / partial / drift
  Q2 (意外改动): none / found - [list]
  Verdict: pass / needs-revision / escalate

## Clarifications
[用户澄清记录 - 置信度检查的结果]
- [Iter N] Q: [问的问题]
  A: [用户回答]
  -> 影响: [对实现的影响]

## Open Questions
[未解决的问题]

## Distilled Lessons
[Phase 5 输出 - 写到 ~/.claude/mission-archive/{slug}/lessons/ 的 lesson 文件清单]
- {YYYY-MM-DD}-{topic-kebab}.md
  "一句话摘要"
  Source: Iter N (Decisions Made / Self-Reflections / Compliance Checks)

## Audit Trail
[Pre-Promise Audit 失败记录 - 每次被拒的 promise 尝试; 也容纳 escape-hatch abandon 的索引行
 (退出原因的权威记录在 Deviations & Reasons, 此处仅留一条交叉引用)]
- [Iter N, Attempt M] Audit failed at item X (原因)
  -> Suggested action: ...
- [Iter N+1, Attempt 1] All 5 items passed -> promise issued
- [Iter N+2] No promise issued — abandoned, see Deviations & Reasons

## Deviations & Reasons
[Escape Hatch / 状态机偏离记录 — mode 切换到 free_form 或临时绕过推荐路径时填]
[未触发时此段为空; 触发时按以下格式追加]
- [Iter N] 触发: {agent_confidence<0.3 / iteration>max / user:free_form / path_conflict}
  原 current_state: {state}
  新 mode: free_form
  理由: {为什么偏离}
  仍需遵守的硬约束: 5 项 Pre-Promise Audit / 强制 5 ([x] timing) / Phase 5 Distill
```

---


## 工作流程

```
===============================================================
                    MISSION RUNNER 工作流 (PIR Mode)
===============================================================

Phase 0: Initialization (初始化)
├── 1. 解析用户任务描述
│
├── 2. 确定 project-slug (跨任务学习层的命名空间):
│      在 git 仓库内: `git rev-parse --show-toplevel` 末段 -> 小写 + kebab-case
│      不在 git 仓库内: `pwd` 末段 -> 小写 + kebab-case
│      示例: E:\Yoji\Prism-OS -> prism-os
│
├── 3. Glob 历史 lessons (跨任务学习层消费端):
│      LessonsDir = ~/.claude/mission-archive/{slug}/lessons/
│      ├─ 目录不存在 -> 跳过此步（首次 mission 情形，无历史可读）
│      └─ 目录存在 -> 读取所有 *.md 的 frontmatter:
│           - 提取每个文件的 keywords[] 与 description
│           - 与当前任务描述做关键词匹配 (大小写不敏感、子串 OK)
│           - 命中阈值: 任务描述中出现 ≥1 个 keyword 或 description 关键词
│      把命中的 lesson (最多 5 条) 完整内容缓存待用
│
├── 4. 创建 _planning/ 目录 (与 Phase 5.2 同样的 shell 分支规则):
│      Unix-like (Bash/zsh): mkdir -p _planning
│      Windows PowerShell:   New-Item -ItemType Directory -Force -Path _planning
│      **不要混用**: Agent 根据当前 shell tool 类型选择对应命令; `mkdir -p`
│      在 PowerShell 中会报 "A positional parameter cannot be found" 错误
│
├── 5. 创建 mission_plan.md (任务计划):
│      包含新增 ## Prior Lessons 段:
│      ├─ Step 3 命中: 列出 lesson 文件名 + 完整 lesson 正文 + Source 引用
│      └─ Step 3 未命中: 写 "(no historical lessons matched this task)"
│
├── 6. 创建 mission_notes.md (空笔记，含所有标准段)
│
└── 7. 启动迭代循环 (默认 3 次迭代)

---------------------------------------------------------------

每次迭代执行 (Iteration 1-N):

┌─ Step 1: Read-Before-Decide (目标锚定) ──────────────────────┐
│  Read _planning/mission_plan.md                              │
│  - 确认: Objective 是什么？                                   │
│  - 确认: 当前在哪个 Phase？                                   │
│  - 确认: 下一个未完成 [ ] 任务是什么？                         │
│  - **检查 ## Prior Lessons 段** (Phase 0 step 3 命中产物):    │
│      ├─ 命中 ≥ 1 条 -> 评估每条 lesson 是否触发其适用条件     │
│      │                  触发的 lesson 内容作为 Step 1.5       │
│      │                  Confidence Check 的输入信号           │
│      │                  (如果 lesson 预警过此类陷阱,           │
│      │                   方案确定性 / 风险预估应相应下调)      │
│      └─ 未命中 / 无段 -> 当前任务无可借鉴的历史，正常评估      │
│  Read _planning/mission_notes.md                             │
│  - 检查: 上次迭代有什么失败/学习？                             │
│  - 检查: 之前的 Clarifications 记录                           │
│  - 检查: Compliance Checks (verdict ≠ pass) / Audit Trail     │
└──────────────────────────────────────────────────────────────┘
           |
           v
┌─ Step 1.5: Confidence Check (置信度检查) ────────────────────┐
│  对当前任务进行 4 维度评估 (1-5分):                            │
│  - 任务理解: 需求是否清晰？                                   │
│  - 方案确定性: 实现方案是否唯一？                              │
│  - 依赖清晰度: API/模块是否明确？                             │
│  - 风险预估: 副作用是否可控？                                 │
│                                                              │
│  计算平均分并决策:                                            │
│  ├─ >= 4 (🟢): 继续 Step 2                                    │
│  ├─ 3-4 (🟡): 记录疑点到 notes，继续 Step 2                   │
│  └─ < 3 (🔴): AskUserQuestion，记录到 Clarifications          │
└──────────────────────────────────────────────────────────────┘
           |
           v
┌─ Step 2: Execute (执行) ─────────────────────────────────────┐
│  执行当前任务 (一次只做一个!)                                  │
│  遵循项目约束                                                 │
│                                                              │
│  实时更新 mission_plan.md:                                    │
│  - **不立即勾 [x]** (强制2): [x] 的合法时机是 Step 3.6 pass 后  │
│  - 更新 Progress Log 表格 ("Iter N: 完成了 xxx, 待 verify")    │
└──────────────────────────────────────────────────────────────┘
           |
           v
┌─ Step 3: Validate (验证) ────────────────────────────────────┐
│  检查代码是否通过验证 (编译/lint/测试)                         │
│  如有错误 -> 进入 Step 3.5 Self-Reflection                    │
│  如无错误 -> 进入 Step 3.6 Compliance Check                   │
└──────────────────────────────────────────────────────────────┘
           |
           v (build pass 路径)
┌─ Step 3.6: Compliance Check (Build Pass 后强制执行) ─────────┐
│  **触发条件**: Step 3 build/lint/test 全部通过                │
│  **目标**: 验证 diff 不仅"能跑"，而且"实现的就是计划那个任务" │
│                                                              │
│  1. 收集三方信号:                                             │
│     a. 当前迭代正在做的 [ ] 任务（从 mission_plan.md 提取）   │
│     b. 本次 Execute 阶段产生的 git diff (`git diff HEAD`)     │
│     c. mission_notes.md > Decisions Made 最近一条（如有）     │
│                                                              │
│  2. 自问 2 个问题 (主对话中直接回答，不派 subagent):           │
│     Q1: 这个 diff 是否完整实现了 a 描述的任务？               │
│         (不是 "代码能编译"，是 "功能 ≈ 任务描述")             │
│     Q2: 是否含计划外的"意外改动"? (goal drift 信号)           │
│         - 文件改动是否都在任务影响范围内？                    │
│         - 是否引入了任务未要求的重构 / 改名 / "顺便修复"？    │
│                                                              │
│  3. 输出 Verdict (写入 mission_notes.md > Compliance Checks):│
│     - [Iter N] Task: "{任务名}"                              │
│       Diff files: {列出 git diff 影响的文件}                  │
│       Q1 (实现完整度): {完整 / 部分 / 偏离}                   │
│       Q2 (意外改动): {无 / 有 - 列举}                         │
│       Verdict: {pass / needs-revision / escalate}             │
│                                                              │
│  4. 根据 Verdict 分支:                                        │
│     - pass           -> **此时勾本任务 [x]** (强制2 满足)      │
│                        进入 Step 4 Checkpoint                 │
│     - needs-revision -> 不勾本任务 [x]                        │
│                        在 plan 该任务下追加修正子任务         │
│                        下一迭代继续此任务                     │
│     - escalate       -> 不勾本任务 [x]                        │
│                        触发 Step 3.5 Self-Reflection          │
│                        Q1/Q2 答案作为 Reflection 输入         │
└──────────────────────────────────────────────────────────────┘

           |
           v (如果失败 / escalate)
┌─ Step 3.5: Self-Reflection (自我反思) ───────────────────────┐
│  **触发条件**:                                                │
│    a. Step 3 验证失败 (build / lint / test 失败), 或          │
│    b. Step 3.6 Compliance Check verdict = escalate            │
│       (此时 build 已 pass, 但 diff 与任务描述偏离过远)        │
│                                                              │
│  1. 生成反思 (使用 Self-Reflection Prompt):                   │
│     - 为什么这个实现失败了？（根本原因）                        │
│     - 下次应该怎么修改？（具体方案）                           │
│     - 有没有类似的坑需要避免？（举一反三）                      │
│                                                              │
│  2. 根据错误类型选择策略:                                     │
│     ├─ 简单错误 (typo/missing import): 立即修复，同一迭代      │
│     ├─ 中等错误 (逻辑问题): 记录反思，下次迭代处理             │
│     └─ 复杂错误 (架构问题): AskUserQuestion 确认方向           │
│                                                              │
│  3. 更新 mission_notes.md:                                    │
│     ## Self-Reflections                                       │
│     - [Iter N, Attempt M] {错误信息}                          │
│       反思: {为什么失败 + 如何改进}                            │
│       策略: {立即修复 / 记录待处理 / 询问用户}                  │
│       状态: {已修复 / 待下迭代 / 等待澄清}                      │
│                                                              │
│  4. 如果选择"立即修复":                                       │
│     -> 返回 Step 2 重新执行 (同一迭代内)                       │
│     -> 最多重试 2 次，超过则记录并进入下一迭代                  │
└──────────────────────────────────────────────────────────────┘
           |
           v
┌─ Step 4: Checkpoint (检查点) ────────────────────────────────┐
│  (到达此处隐含: Step 3 build pass + Step 3.6 verdict=pass)   │
│  更新 Progress Log:                                          │
│  | N | Phase X | 完成了 xxx, verified: pass | Done |          │
│                                                              │
│  判断: 所有任务完成？(全部 [x] 已勾 + Success Criteria 全 [x])│
│  ├─ 是 -> 进入 Phase 4 Debrief (确认 Success Criteria)        │
│  │       -> 进入 Phase 5 Distill (产出 lesson 文件)           │
│  │       -> 跑 Pre-Promise Audit Checklist (5 项)             │
│  │       ├─ 5 项全通过 -> <promise>Mission Accomplished</promise>│
│  │       └─ 任一未通过 -> 输出 Partial Report                 │
│  │                       追加审计结果到 mission_notes.md      │
│  │                       > Audit Trail 段                     │
│  └─ 否 -> 继续下一迭代 (回 Step 1 Read-Before-Decide)         │
└──────────────────────────────────────────────────────────────┘

---------------------------------------------------------------

Phase 4: Debrief (收尾)
├── 确认所有 Success Criteria 标记 [x]
├── mission_notes.md 保留为历史记录
└── 如未完全完成，报告剩余工作

---------------------------------------------------------------

Phase 5: Distill (收尾蒸馏 - Mission Accomplished 的硬前置)

├── 5.1 确定 project-slug (与 Phase 0 step 2 一致, 不 cd):
│      在 git 仓库内: `git rev-parse --show-toplevel` 输出末段
│                    -> 小写 + kebab-case = {project-slug}
│      不在 git 仓库内: `pwd` 输出末段 -> 小写 + kebab-case
│      **不要 cd** —— 只读取命令输出，保持当前 cwd 不变
│      示例: E:\Yoji\Prism-OS -> prism-os
│
├── 5.2 确保 archive 目录存在:
│      Unix-like (Bash/zsh):
│        mkdir -p "$HOME/.claude/mission-archive/{slug}/lessons"
│      Windows PowerShell:
│        New-Item -ItemType Directory -Force -Path `
│          "$env:USERPROFILE\.claude\mission-archive\{slug}\lessons"
│      Agent 应根据 shell tool 类型选择对应命令; 不要混用
│
├── 5.3 从本次 mission_notes.md 提取 Lesson 候选:
│      扫描以下三段:
│        - Decisions Made: 哪个决定值得复用？
│        - Self-Reflections: 哪个失败的根因有跨场景价值？
│        - Compliance Checks **(Verdict = escalate 的)**: 哪类 drift│
│          应该提前防？(needs-revision 通常下迭代变 pass, 不算稳定教训)│
│      生成 1-3 条候选（不是越多越好，宁缺毋滥）
│
├── 5.4 每条候选写入 archive 目录:
│      基础文件名: {YYYY-MM-DD}-{topic-kebab-case}.md
│      内容格式: 见本文档 "## 文件结构 > Lesson 文件结构" 段
│      **碰撞保护** (强制):
│        写入前 ls 检查文件是否已存在
│        ├─ 不存在 -> 直接写入基础文件名
│        └─ 已存在 -> 改名 {YYYY-MM-DD}-{topic}-r2.md (依次递增 r3, r4...)
│                    直到找到不冲突的文件名
│        理由: 同日多迭代 mission 可能产出同主题 lesson, 静默覆盖会丢失深度
│      Lesson 正文 ≤150 字（强制：超出则压缩或拆条）
│
├── 5.5 在 mission_notes.md 追加 ## Distilled Lessons 段:
│      列出本次产出的 lesson 文件路径 + 一句话摘要
│
└── 5.6 Pre-Promise Audit Checklist 项 5 验证:
       项 5: archive 目录下存在至少 1 个本次 mission 的 lesson 文件
       项 5 失败 -> 禁止发 promise，回到 5.3 重新蒸馏
```

---


## 使用方式

### 方式一：使用 /mission-runner 命令 (Claude Code)

```bash
/mission-runner "为电商系统添加订单退款功能"
```

### 方式二：手动调用 (复制完整 Standard Template)

**不要直接抄下面的精简骨架** —— 它只列出顶层结构, 用于解释 prompt 长什么样。
真正贴进 ralph-loop / agent 上下文的 prompt 必须使用
[`references/prompt-template.md`](references/prompt-template.md) 的 Standard Template
(含 7 步 Phase 0 + 含 Step 1.5 / 3.5 / 3.6 的迭代规则 + 5 项 Pre-Promise Audit)。

骨架 (仅示意, 不要照抄):

```
[MISSION RUNNER - PIR MODE]

## 任务
{任务描述}

## Phase 0: Initialization (展开见 prompt-template Standard Template)
- 7 步: 任务解析 / slug 推导 / 历史 lesson glob / 创建 _planning /
  创建 mission_plan.md (含 Prior Lessons 段) / 创建 mission_notes.md /
  启动迭代

## Iteration Rules (展开见 prompt-template Standard Template)
- Step 1   Read-Before-Decide (含 Prior Lessons / Compliance Checks / Audit Trail)
- Step 1.5 Confidence Check (4 维度)
- Step 2   Execute (一次一个任务; **不立即勾 [x]**)
- Step 3   Validate (build / lint / test)
- Step 3.5 Self-Reflection (validate 失败 或 Step 3.6 escalate)
- Step 3.6 Compliance Check (diff vs plan; pass 后才勾 [x])
- Step 4   Checkpoint (全完成 → Phase 4 Debrief → Phase 5 Distill → 5 项 audit)

## Completion (展开见 prompt-template Standard Template)
- 5 项 Pre-Promise Audit 全过 -> <promise>Mission Accomplished</promise>
- 任一项失败 -> Partial Report, 追加 Audit Trail
```

强烈不建议自行精简协议。Step 1.5 / 3.5 / 3.6 + 5 项 audit 中任一缺失,
都会让任务退化回 v1.0 的 "声明完成" 模式 (LLM 自报 [x] 但 git diff 是空).

---


## 与项目自定义 Skills 的协作

Mission Runner 可以与项目中定义的其他 Skills 协作：

| 协作方式 | 说明 |
|----------|------|
| 约束引用 | 在 mission_plan.md Context 中指定相关 Skill |
| 模板复用 | 其他 Skill 可提供领域特定的模板和约束 |
| 验证委托 | 特定验证可委托给专业 Skill |

示例：
```markdown
## Context
- 模块路径: src/modules/order/
- 相关约束: my-project-conventions, api-guidelines
```

---


## 适用场景 vs 不适用场景

### 适用

| 场景 | 示例 |
|------|------|
| 新模块开发 | 创建完整的功能模块 |
| 多层架构实现 | 添加需要 Data/Service/UI 配合的功能 |
| 跨模块功能 | 实现影响多个系统的功能 |
| 大型重构 | 重命名/重组模块结构 |

### 不适用

| 场景 | 原因 | 替代方案 |
|------|------|----------|
| 单文件修改 | 过度复杂 | 直接编辑 |
| 简单 Bug 修复 | 不需要迭代 | 直接修复 |
| 研究/问答 | 无需执行 | 直接对话 |
| 配置修改 | 无需验证循环 | 直接修改 |

---


## 错误处理

### 验证失败时

追加到 `_planning/mission_notes.md`:

```markdown
## Failures & Learnings
- [Iter 2] TS2307: Cannot find module '@/services/refund'
  -> 原因: 路径别名未配置
  -> 方案: 更新 tsconfig.json paths
  -> 状态: 已修复
```

### 达到最大迭代但未完成

```
输出:
- 已完成的任务列表 (从 mission_plan.md)
- 未完成的任务列表
- 建议的后续步骤
- 不输出 Mission Accomplished (诚实原则)
```

---


## 设计哲学

```
+-------------------------------------------------------------+
|                                                             |
|   "Make a dent in the universe."                           |
|                                                             |
|   Mission Runner + PIR 不是让 AI 机械重复，                  |
|   而是让 AI 像工匠一样：                                     |
|                                                             |
|   - 每次迭代都有记忆 (本地文件持久化)                         |
|   - 每次决策都有锚点 (Read-Before-Decide)                    |
|   - 每次失败都是学习 (Failures & Learnings)                  |
|   - 最终交付的是作品，不是代码 (Mission Accomplished)         |
|                                                             |
+-------------------------------------------------------------+
```

---

## 理论基础与致谢

Mission Runner 的设计融合了以下先进理念：

- **[Manus AI Context Engineering](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus)** - 文件系统记忆、注意力操纵
- **[Reflexion (NeurIPS 2023)](https://arxiv.org/abs/2303.11366)** - 语义梯度自反思学习
- **[CrewAI Flows](https://docs.crewai.com/concepts/flows)** - 确定性骨架 + 自治口袋
- **[LangGraph State Machine](https://www.langchain.com/langgraph)** - 显式状态机定义
