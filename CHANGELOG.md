# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Step 3.6 Compliance Check (Build Pass Path)** — prompt-level self-check inserted between Step 3 Validate (pass) and Step 4 Checkpoint. After build/lint/test passes, the agent collects 3 signals (current `[ ]` task description + `git diff HEAD` + most recent `Decisions Made` entry) and self-asks 2 questions in the main conversation (no subagent needed):
  - Q1: Does the diff fully implement the task? (functionality ≈ task description, not just "compiles")
  - Q2: Are there unplanned side changes? (goal drift signal — out-of-scope file edits, unrequested refactoring, "while I was at it" fixes)
- Structured Verdict written to `mission_notes.md > Compliance Checks`: `pass` / `needs-revision` / `escalate`.
- Verdict branching: `pass` → Step 4; `needs-revision` → don't mark task `[x]`, add correction subtask, next iteration; `escalate` → treat as medium error, route into Step 3.5 Self-Reflection with Q1/Q2 answers as input.
- **新增 `Compliance Checks` section in mission_notes.md template** (between Self-Reflections and Clarifications).
- **强制5 (Mandate 5)** in SKILL.md MUST section, requiring Compliance Check after every build pass and forbidding `[x]` marking when Verdict ≠ pass.
- **Pre-Promise Audit Checklist (4-item gate)** before outputting `<promise>Mission Accomplished</promise>`:
  1. All `- [ ]` tasks in mission_plan.md marked `[x]` (internal signal)
  2. All Success Criteria marked `[x]` (internal signal)
  3. `git diff --stat` shows non-empty changes (**external signal** — strongest anti-hallucination check, LLM cannot fabricate)
  4. Build/lint/test executed and passed, traceable in Progress Log (external signal)
- **"强制4" (Mandate 4)** in SKILL.md MUST section, explicitly requiring all 4 audit items to pass before promise.
- **`## Audit Trail`** section in mission_notes.md template, recording rejected promise attempts and the audit failures that triggered them.
- **Partial Report fallback**: when any audit item fails, output Partial Report listing the failed item + reason + next step instead of false promise.

### Changed
- SKILL.md `## 三大强制` heading renamed to `## 五大强制` (was `## 四大强制` after Pre-Promise Audit Checklist landed in this same `[Unreleased]` cycle, then bumped to 五大 with Compliance Check).
- SKILL.md Step 3 Validate ASCII frame: `如无错误 -> 跳过 Step 3.5` changed to `如无错误 -> 进入 Step 3.6 Compliance Check`.
- SKILL.md Step 4 Checkpoint ASCII diagram now branches through audit before issuing promise.
- `references/prompt-template.md` Completion Criteria section rewritten to require 4-item audit (replacing the looser "all [ ] marked + builds successfully" check).
- `references/prompt-template.md` Step 4 in iteration rules: added preamble `(Reaching here implies Step 3.6 Compliance Check verdict was pass)` and routes promise through Pre-Promise Audit Checklist.

### Removed
- **RiderMcp legacy purge**: removed Kotlin Plugin / Unity / PSI / TypeScript Bridge specific content inherited from a previous incarnation of this skill. Affected:
  - `SKILL.md` frontmatter description (removed the "RiderMcp projects" activation line)
  - `SKILL.md` "RiderMcp Project-Specific Error Patterns" section (9 Kotlin/Unity error categories)
  - `SKILL.md` "RiderMcp Project-Specific Validation" section (gradle build / Plugin Verifier / Rider 2025.3.1 notes)
  - `references/error-patterns.md` (entire file, 9 Kotlin/Unity error pattern templates)
  - `references/ridermcp-constraints.md` (entire file)
- **Rationale**: mission-runner is a general-purpose multi-file automation skill; the RiderMcp content was context noise in non-RiderMcp projects (every skill activation injected unrelated concepts like ReadAction, WriteCommandAction, Unity Play mode).

## [1.0.0] - 2024-01-15

### Added

- Initial public release
- **Core PIR Methodology**
  - Filesystem as Memory - persistent state using `_planning/` directory
  - Read-Before-Decide - goal anchoring before each iteration
  - Failures as Data - structured failure recording for learning

- **Confidence Check Protocol**
  - 4-dimension assessment (Understanding, Certainty, Clarity, Risk)
  - Automatic decision routing based on confidence level
  - User clarification flow for low-confidence scenarios

- **Self-Reflection Protocol (Reflexion)**
  - Based on NeurIPS 2023 Reflexion paper
  - Semantic gradient learning from failures
  - Error classification (Simple/Medium/Complex)
  - Max 3 reflection memory management

- **Advisory State Machine**
  - Guided workflow with clear state transitions
  - Escape hatch mechanism for flexibility
  - State persistence for interrupt recovery

- **Multi-Platform Support**
  - Claude Code: `SKILL.md` + `references/`
  - Cursor: `.cursorrules` + `.cursor/rules/*.mdc`

- **Documentation**
  - Comprehensive SKILL.md for Claude Code
  - Full and lite versions for Cursor
  - Prompt templates with scenario examples
  - Example planning files

### Theoretical Foundations

- Manus AI Context Engineering
- Reflexion (NeurIPS 2023)
- CrewAI Flows
- LangGraph State Machine

---

## Future Roadmap

### Planned for v1.1.0

- [ ] Enhanced parallel execution support
- [ ] Tool registry integration
- [ ] More scenario templates

### Planned for v2.0.0

- [ ] Multi-agent composition
- [ ] Cross-session memory
- [ ] Analytics and metrics
