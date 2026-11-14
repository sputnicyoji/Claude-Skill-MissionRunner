# Subagent Briefs & Host Cap Policy

## Host Model & Reasoning Cap Policy

Always leave subagent model and reasoning-effort overrides unset unless the user explicitly asks to switch models. Let the host harness inherit its configured default cap (for example global `CLAUDE_CODE_SUBAGENT_MODEL` or `medium` reasoning effort limits configured in Codex/Antigravity). Never attempt to escalate subagent effort above the host workspace configuration.

---

## Implementer Task Brief (Fresh Context per Task)

Pass only the slice the Implementer needs so it starts clean without inheriting accumulated controller noise:

```text
Role: Task Implementer for <T_id>
Workspace: <repo_root or worktree path>

Objective Slice:
<Exact T_id description + 2-4 line context of why this task exists>

Target Files & Archive Pointers:
- Inspect/modify: <explicit paths or module scope>
- Archive rule(s) if any: <verbatim pointer(s) or "None">

Constraints:
- Keep changes minimal and scoped strictly to <T_id>.
- Record or surface minor design trade-offs concisely if encountered; stop and report clearly on destructive actions, schema/API ambiguity, missing secrets, or after 2 failed fix attempts.
- Follow repository coding conventions (pure ASCII where required, match existing tests/style).

Verification Target:
Run and ensure this check passes cleanly before reporting back:
  <exact verification command>

Return Format:
1. Changed files and brief summary of edits.
2. Exact command run and its observed exit code + summary output.
3. Any design ruling candidate or open blocker.
```

Controller follows up with `python3 <ctl> task-done <T_id> --mission <dir> -- <verify_cmd>` (never trusting prose alone).

---

## Fresh Read-Only Reviewer Brief (Final & High-Risk Gate)

Spawn ONE fresh read-only Reviewer after cumulative changes stabilize (plus an extra mid-mission review right after high-risk auth, schema migration, cleanup, or financial state-transition tasks). Never modify files from the Reviewer.

```text
Role: Fresh Read-Only Code & Verification Reviewer
Workspace: <repo_root>
Access: Read-only (no edits, no commits)

Inputs to Inspect:
1. Run: python3 <ctl> diff --mission <mission_dir> --stat
2. Run: python3 <ctl> diff --mission <mission_dir>
3. Read: <mission_dir>/plan.md (Objective, Rulings & Verification, Success Criteria)
4. Spot-check relevant modified files and tests directly on disk.

Severity Triage:
- Blocking Defect (requires verdict = "revise"):
  - Unhandled error path, race condition, state corruption, security hole, or broken edge case.
  - Missing or tautological/mock-only tests leaving claimed behavior unverified.
  - Diff modifies unrelated files or diverges from plan.md Objective / Rulings.
- Non-Blocking Nit (report briefly, verdict remains "pass"):
  - Pure style preference, minor naming suggestion, or speculative optimization with zero behavioral risk.

Return Format:
- Verdict: pass | revise
- Blocking Defects: concise list with file:line and exact failure scenario (or "None")
- Verification Check: confirm tests/checks actually cover the diff claims
- Nits (non-blocking): <= 3 bullets (or "None")
```

Controller records the verdict mechanically:

```bash
python3 <ctl> review-result --mission <mission_dir> --verdict <pass|revise> --summary "<reviewer verdict summary>"
```
