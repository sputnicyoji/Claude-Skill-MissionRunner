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

强制2: 必须实时更新计划文件
  -> 完成任务立即标记 [x]
  -> 更新 Progress Log 表格

强制3: 必须在任务完成时输出 Mission Accomplished
  -> 格式: <promise>Mission Accomplished</promise>
  -> 只有所有任务完成且验证通过才能输出

强制4: 必须在发 Mission Accomplished 之前通过 Pre-Promise Audit Checklist
  -> 见下方 "Pre-Promise Audit Checklist (CRITICAL)" 段
  -> 4 项中任一未通过 -> 禁止发 promise，输出 Partial Report

强制5: 必须在每次 build pass 之后执行 Step 3.6 Compliance Check
  -> 见工作流段的 Step 3.6 框
  -> 跳过 Compliance Check 等同于跳过 Step 3 Validate
  -> Verdict 必须写入 mission_notes.md > Compliance Checks
  -> Verdict ≠ pass 时禁止勾本任务 [x]，禁止进入 Step 4
```

## Pre-Promise Audit Checklist (CRITICAL)

**在输出 `<promise>Mission Accomplished</promise>` 之前必须逐项核对，4 项全部通过才允许发 promise。**

| # | 检查项 | 信号来源 | 通过条件 |
|---|--------|----------|----------|
| 1 | mission_plan.md 所有 Phase 任务标记 [x] | 内部（plan 文件） | 全文搜 `^- \[ \]` 应为 0 行 |
| 2 | mission_plan.md 所有 Success Criteria 标记 [x] | 内部（plan 文件） | Success Criteria 段无 `[ ]` |
| 3 | `git diff --stat` / `git status` 显示有实质改动 | **外部信号**（git） | 至少 1 个文件 modified/added |
| 4 | Build/lint/test 命令真实执行并通过 | 外部信号（命令输出） | Progress Log 最近一项含 `verified: pass` 或同等记录 |

**任一项未通过：**
- 不输出 `<promise>Mission Accomplished</promise>`
- 改为输出 Partial Report，列出：哪一项未通过、原因、下一步建议
- 把审计结果追加到 mission_notes.md 新增的 `## Audit Trail` 段

**为什么必须有"外部信号"（项 3、项 4）：**
LLM 自报"已完成"是不可信的——存在 hallucinate 完成度的常见失败模式（checkboxes 全勾但 git diff 是空的）。`git diff` 和命令执行输出是 LLM 不能伪造的外部状态，是最强的反 hallucination 信号。

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

### Task subagent 调用模板 (Claude Code)

```python
# 探索代码库
Task(subagent_type="Explore",
     prompt="探索 {目标模块} 的数据流和核心类")

# 架构设计
Task(subagent_type="Plan",
     prompt="基于探索结果，设计 {新功能} 的实现蓝图")
```

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
version: "2.0"

states:
  init:
    description: "初始化规划文件"
    next: read_before_decide

  read_before_decide:
    description: "读取计划文件，锚定目标"
    next: confidence_check

  confidence_check:
    description: "评估当前任务置信度"
    transitions:
      high: execute           # >= 4 分
      medium: execute         # 3-4 分 (带记录)
      low: ask_user           # < 3 分

  ask_user:
    description: "等待用户澄清"
    next: confidence_check    # 澄清后重新评估

  execute:
    description: "执行当前任务"
    next: validate

  validate:
    description: "验证执行结果"
    transitions:
      pass: checkpoint
      fail: self_reflection

  self_reflection:
    description: "分析失败原因"
    transitions:
      simple_error: execute   # 立即重试 (同一迭代)
      medium_error: checkpoint # 记录，下次迭代
      complex_error: ask_user  # 需要用户澄清

  checkpoint:
    description: "更新进度，检查完成状态"
    transitions:
      complete: done
      continue: read_before_decide  # 下一迭代
      max_iterations: report        # 达到最大迭代

  done:
    description: "任务完成"
    output: "<promise>Mission Accomplished</promise>"

  report:
    description: "报告部分完成"
    output: "剩余任务列表 + 建议"
```

### 状态机可视化

```
                    ┌──────────────────────────────────────────────────────┐
                    │                                                      │
                    v                                                      │
              ┌──────────┐                                                │
              │   init   │                                                │
              └────┬─────┘                                                │
                   │                                                      │
                   v                                                      │
         ┌─────────────────────┐                                         │
         │  read_before_decide │◄────────────────────────────────────────┤
         └─────────┬───────────┘                                         │
                   │                                                      │
                   v                                                      │
          ┌────────────────────┐     low      ┌───────────┐              │
          │  confidence_check  │─────────────►│  ask_user │              │
          └────────┬───────────┘              └─────┬─────┘              │
                   │ high/medium                    │                    │
                   v                                │ (澄清后)            │
              ┌─────────┐◄──────────────────────────┘                    │
              │ execute │                                                 │
              └────┬────┘                                                 │
                   │              ┌─────────────────┐                    │
                   v              │ self_reflection │                    │
              ┌──────────┐  fail  └────────┬────────┘                    │
              │ validate │────────────────►│                             │
              └────┬─────┘                 │ simple_error                │
                   │ pass                  └──────────►│                 │
                   v                                   │                 │
             ┌────────────┐◄────────────────(medium)───┘                 │
             │ checkpoint │                                              │
             └──────┬─────┘                                              │
                    │                                                    │
           ┌────────┼────────┐                                          │
           │        │        │                                          │
           v        v        v                                          │
       ┌──────┐ ┌────────┐ ┌────────┐                                   │
       │ done │ │ report │ │continue│───────────────────────────────────┘
       └──────┘ └────────┘ └────────┘
```

### 状态持久化

```json
// _planning/workflow_state.json
{
  "current_state": "execute",
  "iteration": 2,
  "retry_count": 0,
  "phase": "implementation",
  "task_index": 3,
  "confidence_scores": {
    "understanding": 5,
    "certainty": 4,
    "dependencies": 4,
    "risk": 4
  },
  "timestamp": "2024-01-15T15:30:00Z"
}
```

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
1. Agent 恢复完全自主权，不再受状态机约束
2. 仍保留 mission_plan.md 作为目标参考（但非强制）
3. 任务完成后，记录"自由模式"路径供后续学习

---


## 文件结构

```
_planning/                    # 任务规划目录 (迭代持久化)
├── mission_plan.md          # 任务计划 + 成功标准 + 进度日志
├── mission_notes.md         # 研究发现 + 决策 + 失败记录 (append-only)
└── workflow_state.json      # 状态机当前位置 (支持中断恢复)
```

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

## Clarifications
[用户澄清记录 - 置信度检查的结果]
- [Iter N] Q: [问的问题]
  A: [用户回答]
  -> 影响: [对实现的影响]

## Open Questions
[未解决的问题]
```

---


## 工作流程

```
===============================================================
                    MISSION RUNNER 工作流 (PIR Mode)
===============================================================

Phase 0: Initialization (初始化)
├── 1. 解析用户任务描述
├── 2. 创建 _planning/ 目录:
│      mkdir -p _planning
├── 3. 创建 mission_plan.md (任务计划)
├── 4. 创建 mission_notes.md (空笔记)
└── 5. 启动迭代循环 (默认 3 次迭代)

---------------------------------------------------------------

每次迭代执行 (Iteration 1-N):

┌─ Step 1: Read-Before-Decide (目标锚定) ──────────────────────┐
│  Read _planning/mission_plan.md                              │
│  - 确认: Objective 是什么？                                   │
│  - 确认: 当前在哪个 Phase？                                   │
│  - 确认: 下一个未完成 [ ] 任务是什么？                         │
│  Read _planning/mission_notes.md                             │
│  - 检查: 上次迭代有什么失败/学习？                             │
│  - 检查: 之前的 Clarifications 记录                           │
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
│  - 完成任务立即标记 [x]                                       │
│  - 更新 Progress Log 表格                                     │
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
│     - pass           -> 进入 Step 4 Checkpoint                │
│     - needs-revision -> 不勾本任务 [x]                        │
│                        在 plan 该任务下追加修正子任务         │
│                        下一迭代继续此任务                     │
│     - escalate       -> 视为"中等错误"                        │
│                        触发 Step 3.5 Self-Reflection          │
│                        Q1/Q2 答案作为 Reflection 输入         │
└──────────────────────────────────────────────────────────────┘

           |
           v (如果失败 / escalate)
┌─ Step 3.5: Self-Reflection (自我反思) ───────────────────────┐
│  **触发条件**: Step 3 验证失败                                │
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
│  更新 Progress Log:                                          │
│  | N | Phase X | 完成了 xxx, 遇到 yyy | Done/Blocked |        │
│                                                              │
│  判断: 所有任务完成？                                         │
│  ├─ 是 -> 执行 Pre-Promise Audit Checklist (4 项)             │
│  │       ├─ 4 项全通过 -> <promise>Mission Accomplished</promise>│
│  │       └─ 任一未通过 -> 输出 Partial Report                 │
│  │                       追加审计结果到 mission_notes.md      │
│  │                       > Audit Trail 段                     │
│  └─ 否 -> 继续下一迭代                                        │
└──────────────────────────────────────────────────────────────┘

---------------------------------------------------------------

Phase 4: Debrief (收尾)
├── 确认所有 Success Criteria 标记 [x]
├── mission_notes.md 保留为历史记录
└── 如未完全完成，报告剩余工作
```

---


## 使用方式

### 方式一：使用 /mission-runner 命令 (Claude Code)

```bash
/mission-runner "为电商系统添加订单退款功能"
```

### 方式二：手动调用

```
[MISSION RUNNER - PIR MODE]

## 任务
为电商系统添加订单退款功能

## Phase 0: Initialization
1. mkdir -p _planning
2. 创建 mission_plan.md 和 mission_notes.md
3. 分解任务到 Phases

## 迭代规则 (每次迭代必须执行)
1. Read-Before-Decide: 读取 _planning/mission_plan.md
2. Execute: 执行下一个 [ ] 任务，更新 [x]
3. Validate: 验证检查，错误追加到 mission_notes.md
4. Checkpoint: 更新 Progress Log

## 完成条件
所有 Success Criteria 标记 [x] 且验证通过后输出:
<promise>Mission Accomplished</promise>
```

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
