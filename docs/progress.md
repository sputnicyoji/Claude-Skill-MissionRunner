# Progress

## 2026-11-14 — v3 控制面重构与正式发布

完成 Mission Runner 从 v2 提示词状态机向 v3 机械控制面的重构并发布 `v3.0.0`：新增零依赖 Python 3.9+ 标准库脚本 `scripts/mission_ctl.py`（基于临时 `GIT_INDEX_FILE` + `git write-tree` 的无侵入快照、`task-done` 退出码与非空 diff 机械门控、中英双语词边界/bigram 教训检索、触发器门控蒸馏及 `doctor-archive` 归档修复），并将 `SKILL.md` 收敛至 115 行正向编排主干，以单一新鲜只读 Reviewer 替代同上下文自评。同步补齐 `references/{subagent-briefs,schemas,harness-adapters}.md`、真实生成的 `examples/_planning/20261114-order-refund/plan.md`、多代理（Claude Code / Codex / Gemini CLI / Antigravity / Cursor）安装说明及 GitHub Release 与仓库 About 元数据，并将仓库正式更名为 `mission-runner`（去掉原厂商前缀以体现跨代理通用技能定位）；后续可在真实跨模块任务中继续观察双语关键词召回表现与子代理拆分粒度。

锚点：`scripts/mission_ctl.py`、`tests/test_mission_ctl.py`（`8/8` 单测通过）、`SKILL.md`、commits `09be807`..`e752b94`、tag `v3.0.0`（https://github.com/sputnicyoji/mission-runner/releases/tag/v3.0.0）。
