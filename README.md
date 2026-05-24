# Mission Runner

> **Automated Multi-File Development with PIR (Plan-Iterate-Resolve) Methodology**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Compatible-blueviolet)](https://claude.ai/code)
[![GitHub stars](https://img.shields.io/github/stars/sputnicyoji/Claude-Skill-MissionRunner?style=social)](https://github.com/sputnicyoji/Claude-Skill-MissionRunner)


**English** | [简体中文](README_zh-CN.md) | [日本語](README_ja.md)

Mission Runner is an AI coding assistant skill that enables autonomous execution of complex, multi-file development tasks. It combines task planning, iterative execution, and self-reflection to deliver high-quality results.

## Key Features

| Feature | Description |
|---------|-------------|
| **Filesystem as Memory** | Persistent state using local `_planning/` files, not context window |
| **Read-Before-Decide** | Always re-read the plan before each decision to prevent goal drift |
| **Failures as Data** | All errors recorded for learning in subsequent iterations |
| **Confidence Check** | 4-dimension assessment before each task execution |
| **Self-Reflection (Reflexion)** | Semantic gradient learning from failures (NeurIPS 2023) |
| **Advisory State Machine** | Guided workflow with escape hatch for flexibility |
| **Compliance Check (Step 3.6)** | Build-pass diff-vs-plan verifier; catches "code runs but does the wrong thing" goal drift |
| **Pre-Promise Audit (5-item gate)** | Hard gate before `<promise>` with 3 external signals (git diff, build output, lesson file) the LLM cannot fabricate |
| **Phase 5 Distill + cross-mission archive** | Every mission writes 1-3 ≤150-char lessons to `~/.claude/mission-archive/{slug}/lessons/`; future missions glob them in Phase 0 as Prior Lessons |

## When to Use

| Scenario | Example |
|----------|---------|
| New module development | Create complete feature with Data/Service/UI layers |
| Multi-file implementation | Add feature requiring 3+ files |
| Cross-module features | Implement functionality spanning multiple systems |
| Large refactoring | Rename/reorganize module structure |

## When NOT to Use

- Single file edits
- Simple bug fixes
- Research/Q&A tasks
- Configuration changes

## Installation

Mission Runner targets Claude Code. Earlier releases shipped Cursor rule files
(`.cursorrules` / `.cursor/rules/*.mdc`) but those were never updated to the
v1.1 protocol (Compliance Check, Pre-Promise Audit, Phase 5 Distill, Prior
Lessons glob) and have been removed.

```bash
# Clone the repository
git clone https://github.com/sputnicyoji/Claude-Skill-MissionRunner.git

# Copy to your project
mkdir -p .claude/skills/mission-runner
cp Claude-Skill-MissionRunner/SKILL.md .claude/skills/mission-runner/
cp -r Claude-Skill-MissionRunner/references .claude/skills/mission-runner/
```

## Quick Start

### Basic Usage

```
[MISSION RUNNER - PIR MODE]

## Task
Add user authentication feature to the application

## Phase 0: Initialization
1. mkdir -p _planning
2. Create mission_plan.md and mission_notes.md
3. Break down tasks into Phases

## Iteration Rules
1. Read-Before-Decide: Read _planning/mission_plan.md
2. Execute: Execute next [ ] task, mark [x]
3. Validate: Build/lint/test check
4. Checkpoint: Update Progress Log

## Completion Criteria
<promise>Mission Accomplished</promise>
```

### File Structure Created

```
_planning/                                   # Per-mission (transient)
├── mission_plan.md       # Tasks + success criteria + Prior Lessons + progress
├── mission_notes.md      # Findings + decisions + failures + Compliance Checks +
│                         #   Distilled Lessons + Audit Trail
└── workflow_state.json   # State machine position (optional)

~/.claude/mission-archive/                   # Cross-mission (persistent)
└── {project-slug}/
    └── lessons/
        └── {YYYY-MM-DD}-{topic-kebab}.md   # ≤150-char reusable insights
```

## Core Workflow

```
Phase 0: Initialize
├── Parse task
├── Determine {project-slug}                       (NEW: cross-mission ns)
├── Glob ~/.claude/mission-archive/{slug}/lessons/ (NEW: historical lesson hits)
├── Create _planning/ directory
├── Create mission_plan.md (incl. ## Prior Lessons injected from glob)
└── Create mission_notes.md (all standard sections)

Each Iteration:
├── Step 1: Read-Before-Decide (reads Prior Lessons + notes; feeds Confidence Check)
├── Step 1.5: Confidence Check (4 dimensions)
├── Step 2: Execute (one task only; does NOT mark [x] yet)
├── Step 3: Validate (compile/lint/test)
│      ├── fail -> Step 3.5
│      └── pass -> Step 3.6
├── Step 3.5: Self-Reflection (on validation fail OR Step 3.6 escalate)
├── Step 3.6: Compliance Check (NEW: diff-vs-plan goal-drift verifier)
│      ├── pass -> mark [x] + Step 4
│      ├── needs-revision -> don't mark; next iteration continues
│      └── escalate -> Step 3.5
└── Step 4: Checkpoint
       ├── No -> next iteration
       └── Yes (all done) -> Phase 4 Debrief -> Phase 5 Distill -> 5-item Audit

Phase 4: Debrief        (confirm Success Criteria all [x])
Phase 5: Distill        (NEW: extract 1-3 ≤150-char lessons to archive)
Pre-Promise Audit       (NEW: 5-item gate with 3 external signals)
├── all 5 pass -> <promise>Mission Accomplished</promise>
└── any fail   -> Partial Report + append to ## Audit Trail
```

## Confidence Check Protocol

Before executing each task, evaluate on 4 dimensions (1-5 scale):

| Dimension | Question |
|-----------|----------|
| Task Understanding | Are requirements fully clear? |
| Solution Certainty | Is approach unique and clear? |
| Dependency Clarity | Are APIs/modules identified? |
| Risk Assessment | Are side effects controllable? |

Decision based on average:
- **>= 4 (Green)**: Execute directly
- **3-4 (Yellow)**: Record concerns, then execute
- **< 3 (Red)**: Ask user for clarification

## Self-Reflection (Reflexion)

When validation fails, generate reflection before retrying:

1. **Why did it fail?** (root cause)
2. **How to fix?** (specific solution)
3. **Similar pitfalls?** (learn by analogy)

Error classification:
- **Simple** (typo/import): Fix immediately (max 2 retries)
- **Medium** (logic): Record, handle next iteration
- **Complex** (architecture): Ask user

## State Machine (Advisory Mode)

```
init -> read_before_decide -> confidence_check -> execute -> validate -> checkpoint
                                    |                           |
                                    v (low)                     v (fail)
                                ask_user              self_reflection
```

The state machine is **advisory, not mandatory**. Agent may deviate when needed - just record the reason.

## Theoretical Foundations

Mission Runner incorporates cutting-edge concepts from AI agent research:

| Source | Concept |
|--------|---------|
| [Manus AI](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus) | Filesystem memory, attention manipulation |
| [Reflexion (NeurIPS 2023)](https://arxiv.org/abs/2303.11366) | Semantic gradient self-reflection |
| [CrewAI Flows](https://docs.crewai.com/concepts/flows) | Deterministic skeleton + autonomous pockets |
| [LangGraph](https://www.langchain.com/langgraph) | Explicit state machine definition |

## Repository Structure

```
Claude-Skill-MissionRunner/
├── SKILL.md                          # Claude Code skill (main)
├── references/
│   └── prompt-template.md            # Detailed prompt templates
├── examples/
│   └── _planning/                    # Example planning files
├── README.md
├── LICENSE
└── CHANGELOG.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Anthropic](https://anthropic.com) for Claude Code
- The AI agent research community
- All contributors and users

---

<p align="center">
  <sub>Built with PIR methodology for autonomous AI development</sub>
</p>
