# Mission Runner

> **基于 PIR (Plan-Iterate-Resolve) 方法论的自动化多文件开发工具**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-blueviolet)](https://claude.ai/code)
[![Cursor](https://img.shields.io/badge/Cursor-Compatible-blue)](https://cursor.sh)
[![GitHub stars](https://img.shields.io/github/stars/sputnicyoji/Claude-Skill-MissionRunner?style=social)](https://github.com/sputnicyoji/Claude-Skill-MissionRunner)

[English](README.md) | **简体中文** | [日本語](README_ja.md)

Mission Runner 是一个 AI 编码助手技能，能够自主执行复杂的多文件开发任务。它结合了任务规划、迭代执行和自我反思，以交付高质量的结果。

## 核心特性

| 特性 | 描述 |
|------|------|
| **文件系统即记忆** | 使用本地 `_planning/` 文件持久化状态，而非上下文窗口 |
| **决策前先读取** | 每次决策前重新读取计划，防止目标漂移 |
| **失败即数据** | 所有错误都被记录，供后续迭代学习 |
| **置信度检查** | 每次任务执行前进行 4 维度评估 |
| **自我反思 (Reflexion)** | 基于失败的语义梯度学习 (NeurIPS 2023) |
| **建议式状态机** | 带逃逸舱的引导式工作流，保持灵活性 |

## 适用场景

| 场景 | 示例 |
|------|------|
| 新模块开发 | 创建包含 Data/Service/UI 层的完整功能 |
| 多文件实现 | 添加需要 3+ 文件的功能 |
| 跨模块功能 | 实现跨越多个系统的功能 |
| 大型重构 | 重命名/重组模块结构 |

## 不适用场景

- 单文件编辑
- 简单 Bug 修复
- 研究/问答任务
- 配置更改

## 安装

### Claude Code 用户

```bash
# 克隆仓库
git clone https://github.com/sputnicyoji/Claude-Skill-MissionRunner.git

# 复制到你的项目
mkdir -p .claude/skills/mission-runner
cp Claude-Skill-MissionRunner/SKILL.md .claude/skills/mission-runner/
cp -r Claude-Skill-MissionRunner/references .claude/skills/mission-runner/
```

### Cursor 用户

```bash
# 方式 1: 使用 .cursorrules (根目录级别，推荐)
cp Claude-Skill-MissionRunner/.cursorrules /path/to/your/project/

# 方式 2: 使用 .cursor/rules/ (模块化)
mkdir -p /path/to/your/project/.cursor/rules
cp Claude-Skill-MissionRunner/.cursor/rules/mission-runner.mdc /path/to/your/project/.cursor/rules/

# 或使用精简版快速参考:
cp Claude-Skill-MissionRunner/.cursor/rules/mission-runner-lite.mdc /path/to/your/project/.cursor/rules/
```

## 快速开始

### 基本用法

```
[MISSION RUNNER - PIR MODE]

## 任务
为应用程序添加用户认证功能

## Phase 0: 初始化
1. mkdir -p _planning
2. 创建 mission_plan.md 和 mission_notes.md
3. 将任务分解为阶段

## 迭代规则
1. 决策前读取: 读取 _planning/mission_plan.md
2. 执行: 执行下一个 [ ] 任务，标记 [x]
3. 验证: 构建/lint/测试检查
4. 检查点: 更新进度日志

## 完成条件
<promise>Mission Accomplished</promise>
```

### 创建的文件结构

```
_planning/
├── mission_plan.md       # 任务 + 成功标准 + 进度
├── mission_notes.md      # 发现 + 决策 + 失败记录
└── workflow_state.json   # 状态机位置 (可选)
```

## 核心工作流

```
Phase 0: 初始化
├── 创建 _planning/ 目录
├── 创建 mission_plan.md (任务 + 成功标准)
└── 创建 mission_notes.md (空笔记)

每次迭代:
├── Step 1: 决策前读取 (锚定目标)
├── Step 1.5: 置信度检查 (4 维度)
├── Step 2: 执行 (仅一个任务)
├── Step 3: 验证 (编译/lint/测试)
├── Step 3.5: 自我反思 (如果验证失败)
└── Step 4: 检查点 (更新进度)

完成:
└── 输出: <promise>Mission Accomplished</promise>
```

## 置信度检查协议

在执行每个任务前，从 4 个维度评估 (1-5 分):

| 维度 | 问题 |
|------|------|
| 任务理解 | 需求是否完全清晰？ |
| 方案确定性 | 实现方案是否唯一明确？ |
| 依赖清晰度 | API/模块是否已识别？ |
| 风险评估 | 副作用是否可控？ |

基于平均分决策:
- **>= 4 (绿色)**: 直接执行
- **3-4 (黄色)**: 记录疑虑，然后执行
- **< 3 (红色)**: 向用户询问澄清

## 自我反思 (Reflexion)

当验证失败时，在重试前生成反思:

1. **为什么失败？** (根本原因)
2. **如何修复？** (具体方案)
3. **类似陷阱？** (举一反三)

错误分类:
- **简单** (typo/import): 立即修复 (最多 2 次重试)
- **中等** (逻辑): 记录，下次迭代处理
- **复杂** (架构): 询问用户

## 状态机 (建议模式)

```
init -> read_before_decide -> confidence_check -> execute -> validate -> checkpoint
                                    |                           |
                                    v (低)                      v (失败)
                                ask_user              self_reflection
```

状态机是**建议性的，非强制性的**。Agent 可以在需要时偏离——只需记录原因。

## 理论基础

Mission Runner 融合了 AI Agent 研究的前沿概念:

| 来源 | 概念 |
|------|------|
| [Manus AI](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) | 文件系统记忆，注意力操纵 |
| [Reflexion (NeurIPS 2023)](https://arxiv.org/abs/2303.11366) | 语义梯度自我反思 |
| [CrewAI Flows](https://docs.crewai.com/concepts/flows) | 确定性骨架 + 自治口袋 |
| [LangGraph](https://www.langchain.com/langgraph) | 显式状态机定义 |

## 仓库结构

```
Claude-Skill-MissionRunner/
├── SKILL.md                          # Claude Code 技能 (主文件)
├── references/
│   └── prompt-template.md            # 详细 Prompt 模板
├── .cursorrules                      # Cursor 根级规则
├── .cursor/rules/
│   ├── mission-runner.mdc            # Cursor 完整版
│   └── mission-runner-lite.mdc       # Cursor 精简版
├── examples/
│   └── _planning/                    # 示例规划文件
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## 贡献

欢迎贡献！请随时提交 Pull Request。

1. Fork 仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 致谢

- [Anthropic](https://anthropic.com) 的 Claude Code
- [Cursor](https://cursor.sh) AI 驱动的编辑器
- AI Agent 研究社区
- 所有贡献者和用户

---

<p align="center">
  <sub>基于 PIR 方法论构建，用于自主 AI 开发</sub>
</p>
