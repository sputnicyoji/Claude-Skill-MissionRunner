# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
