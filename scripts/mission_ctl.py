#!/usr/bin/env python3
"""Mechanical control plane for mission-runner v3."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
DEFAULT_ARCHIVE_DIR = Path.home() / ".claude" / "mission-archive"


@dataclass
class GitContext:
    worktree_root: Path
    main_root: Path
    git_dir: Path
    common_dir: Path
    origin_url: str


def now_local() -> datetime:
    return datetime.now()


def iso_now() -> str:
    return now_local().strftime("%Y-%m-%dT%H:%M:%S")


def human_now() -> str:
    return now_local().strftime("%Y-%m-%d %H:%M:%S")


def date_stamp() -> str:
    return now_local().strftime("%Y%m%d")


def normalize_slug(raw: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", raw.lower()).strip("-")
    return cleaned


def collapse_ws(text: str) -> str:
    return " ".join(text.split())


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".tmp_", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        os.replace(tmp_name, str(path))
    except Exception:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def run_git(
    cwd: Path,
    args: Sequence[str],
    env: Optional[Dict[str, str]] = None,
    check: bool = False,
) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc


def resolve_git_path(base: Path, raw_path: str) -> Path:
    candidate = Path(raw_path.strip())
    if not candidate.is_absolute():
        candidate = base / candidate
    return candidate.resolve()


def detect_git_context(cwd: Path) -> Optional[GitContext]:
    probe = run_git(cwd, ["rev-parse", "--show-toplevel"])
    if probe.returncode != 0:
        return None
    worktree_root = Path(probe.stdout.strip()).resolve()
    gd_proc = run_git(worktree_root, ["rev-parse", "--git-dir"], check=True)
    cd_proc = run_git(worktree_root, ["rev-parse", "--git-common-dir"], check=True)
    git_dir = resolve_git_path(worktree_root, gd_proc.stdout)
    common_dir = resolve_git_path(worktree_root, cd_proc.stdout)
    main_root = common_dir.parent if common_dir.name == ".git" else worktree_root
    origin_proc = run_git(worktree_root, ["remote", "get-url", "origin"])
    origin_url = origin_proc.stdout.strip() if origin_proc.returncode == 0 else ""
    return GitContext(
        worktree_root=worktree_root,
        main_root=main_root,
        git_dir=git_dir,
        common_dir=common_dir,
        origin_url=origin_url,
    )


def parse_origin_slug(origin_url: str) -> str:
    trimmed = origin_url.strip().rstrip("/")
    if not trimmed:
        return ""
    if trimmed.endswith(".git"):
        trimmed = trimmed[:-4]
    segment = re.split(r"[/:]", trimmed)[-1]
    return normalize_slug(segment)


def read_slug_override(paths: Sequence[Path]) -> str:
    for root in paths:
        marker = root / ".mission-slug"
        if marker.is_file():
            for line in marker.read_text(encoding="utf-8").splitlines():
                candidate = normalize_slug(line.strip())
                if candidate:
                    return candidate
    return ""


def resolve_slug(cwd: Path, archive_dir: Path) -> str:
    ctx = detect_git_context(cwd)
    if ctx is None:
        override = read_slug_override([cwd.resolve()])
        return override or normalize_slug(cwd.resolve().name) or "workspace"

    override = read_slug_override([ctx.worktree_root, ctx.main_root])
    if override:
        return override

    dir_slug = normalize_slug(ctx.main_root.name)
    origin_slug = parse_origin_slug(ctx.origin_url)

    if origin_slug and dir_slug and origin_slug != dir_slug:
        has_dir = (archive_dir / dir_slug / "lessons").is_dir()
        has_origin = (archive_dir / origin_slug / "lessons").is_dir()
        if has_dir and not has_origin:
            return dir_slug
        return origin_slug

    return origin_slug or dir_slug or "workspace"


def ensure_planning_excluded(ctx: GitContext) -> None:
    probe = run_git(ctx.worktree_root, ["check-ignore", "-q", "_planning/.probe"])
    if probe.returncode == 0:
        return
    exclude_path = ctx.common_dir / "info" / "exclude"
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    existing = exclude_path.read_text(encoding="utf-8") if exclude_path.is_file() else ""
    lines = [line.strip() for line in existing.splitlines()]
    if "_planning/" in lines or "_planning" in lines:
        return
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    exclude_path.write_text(existing + prefix + "_planning/\n", encoding="utf-8")


def non_git_tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if not rel.parts or rel.parts[0] in {"_planning", ".git"}:
            continue
        if path.is_file():
            digest.update(str(rel).encode("utf-8"))
            digest.update(b"\0")
            digest.update(path.read_bytes())
            digest.update(b"\0")
    return f"nongit:{digest.hexdigest()}"


def snapshot_tree(workspace_root: Path, ctx: Optional[GitContext]) -> Tuple[str, str, bool]:
    if ctx is None:
        return non_git_tree_digest(workspace_root), "NON_GIT", True

    head_proc = run_git(ctx.worktree_root, ["rev-parse", "--verify", "HEAD"])
    head_sha = head_proc.stdout.strip() if head_proc.returncode == 0 else "UNBORN"

    status_proc = run_git(ctx.worktree_root, ["status", "--porcelain"], check=True)
    clean_start = status_proc.stdout.strip() == ""

    with tempfile.TemporaryDirectory(prefix="mctl_idx_") as tmpdir:
        tmp_index = Path(tmpdir) / "index"
        env = dict(os.environ)
        env["GIT_INDEX_FILE"] = str(tmp_index)
        run_git(ctx.worktree_root, ["add", "-A"], env=env, check=True)
        if tmp_index.exists():
            wt_proc = run_git(ctx.worktree_root, ["write-tree"], env=env, check=True)
            tree_sha = wt_proc.stdout.strip()
        else:
            tree_sha = EMPTY_TREE_SHA
    return tree_sha, head_sha, clean_start


def git_diff_names(
    workspace_root: Path, ctx: Optional[GitContext], tree_a: str, tree_b: str
) -> List[str]:
    if ctx is None:
        return [] if tree_a == tree_b else ["<workspace>"]
    if tree_a == tree_b:
        return []
    proc = run_git(
        ctx.worktree_root, ["diff", "--name-only", tree_a, tree_b], check=True
    )
    return [line for line in proc.stdout.splitlines() if line.strip()]


def append_event(mission_dir: Path, payload: Dict[str, Any]) -> None:
    logs_dir = mission_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    events_path = logs_dir / ".events.jsonl"
    record = {"ts": iso_now(), **payload}
    with events_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=True) + "\n")


def read_events(mission_dir: Path) -> List[Dict[str, Any]]:
    events_path = mission_dir / "logs" / ".events.jsonl"
    if not events_path.is_file():
        return []
    events: List[Dict[str, Any]] = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            events.append(json.loads(stripped))
    return events


def resolve_mission_dir(mission_arg: Optional[str], cwd: Path) -> Path:
    if mission_arg:
        candidate = Path(mission_arg).expanduser().resolve()
        if candidate.is_file() and candidate.name == "plan.md":
            return candidate.parent
        if candidate.is_dir() and (candidate / "plan.md").is_file():
            return candidate
        raise SystemExit(f"Invalid mission directory: {candidate}")

    ctx = detect_git_context(cwd)
    base = ctx.worktree_root if ctx else cwd.resolve()
    planning = base / "_planning"
    if not planning.is_dir():
        raise SystemExit(f"No _planning directory found under {base}")
    active = [
        p
        for p in sorted(planning.iterdir())
        if p.is_dir() and (p / "plan.md").is_file() and (p / "logs" / ".events.jsonl").is_file()
    ]
    if len(active) == 1:
        return active[0]
    if not active:
        raise SystemExit("No active mission found; pass --mission DIR")
    raise SystemExit("Multiple active missions found; pass --mission DIR")


def read_plan_meta(plan_text: str) -> Dict[str, str]:
    meta: Dict[str, str] = {}
    for line in plan_text.splitlines():
        match = re.match(r"^- ([A-Za-z]+):\s*`([^`]*)`", line)
        if match:
            meta[match.group(1)] = match.group(2)
    return meta


def transform_section(
    plan_text: str, heading: str, fn: Callable[[List[str]], List[str]]
) -> str:
    lines = plan_text.splitlines()
    start_idx = None
    end_idx = len(lines)
    target = f"## {heading}"
    for idx, line in enumerate(lines):
        if line.strip() == target:
            start_idx = idx + 1
        elif start_idx is not None and line.startswith("## "):
            end_idx = idx
            break
    if start_idx is None:
        raise SystemExit(f"Missing section '## {heading}' in plan.md")
    updated = fn(lines[start_idx:end_idx])
    new_lines = lines[:start_idx] + updated + lines[end_idx:]
    trailing = "\n" if plan_text.endswith("\n") else ""
    return "\n".join(new_lines) + trailing


def extract_section_lines(plan_text: str, heading: str) -> List[str]:
    lines = plan_text.splitlines()
    start_idx = None
    target = f"## {heading}"
    out: List[str] = []
    for line in lines:
        if line.strip() == target:
            start_idx = 1
            continue
        if start_idx is not None:
            if line.startswith("## "):
                break
            out.append(line)
    if start_idx is None:
        raise SystemExit(f"Missing section '## {heading}' in plan.md")
    return out


def append_receipt_line(mission_dir: Path, bullet: str) -> None:
    plan_path = mission_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")

    def add_line(section: List[str]) -> List[str]:
        out = list(section)
        while out and out[-1].strip() == "":
            out.pop()
        out.append(bullet)
        out.append("")
        return out

    atomic_write(plan_path, transform_section(plan_text, "Rulings & Verification", add_line))


def find_matched_lessons(
    slug: str, query: str, terms: str, archive_dir: Path, limit: int = 3
) -> List[str]:
    # Implemented cleanly in Ticket 02; returns empty when archive has no indexable files
    return []


def cmd_slug(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    archive_dir = Path(args.archive_dir).expanduser().resolve()
    print(resolve_slug(cwd, archive_dir))
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    cwd = Path(args.cwd).resolve()
    archive_dir = Path(args.archive_dir).expanduser().resolve()
    ctx = detect_git_context(cwd)
    workspace_root = ctx.worktree_root if ctx else cwd

    if ctx is not None:
        ensure_planning_excluded(ctx)

    slug = normalize_slug(args.slug) if args.slug else resolve_slug(cwd, archive_dir)
    if not slug:
        slug = "workspace"

    base_tree, head_sha, clean_start = snapshot_tree(workspace_root, ctx)
    title_slug = normalize_slug(args.title)[:48].strip("-") or "mission"
    prefix = f"{date_stamp()}-{title_slug}"

    planning_root = workspace_root / "_planning"
    planning_root.mkdir(parents=True, exist_ok=True)
    mission_dir = planning_root / prefix
    suffix = 2
    while mission_dir.exists():
        mission_dir = planning_root / f"{prefix}-{suffix}"
        suffix += 1
    mission_dir.mkdir(parents=True, exist_ok=False)

    pointers = find_matched_lessons(
        slug=slug,
        query=f"{args.title} {args.objective}",
        terms=args.terms or "",
        archive_dir=archive_dir,
        limit=3,
    )

    tasks = args.task if args.task else ["Define and execute concrete tasks"]
    criteria = args.criteria if args.criteria else ["Verify all checks pass cleanly"]

    pointer_block = "\n".join(pointers) if pointers else "- None matched."
    task_block = "\n".join(
        f"- [ ] **T{idx}**: {collapse_ws(t)}" for idx, t in enumerate(tasks, start=1)
    )
    criteria_block = "\n".join(
        f"- [ ] C{idx}: {collapse_ws(c)}" for idx, c in enumerate(criteria, start=1)
    )

    plan_content = (
        f"# Mission: {collapse_ws(args.title)}\n\n"
        f"- Slug: `{slug}`\n"
        f"- Mode: `{args.mode}`\n"
        f"- Status: `active`\n"
        f"- RepoRoot: `{workspace_root}`\n"
        f"- BaselineTree: `{base_tree}`\n"
        f"- HeadAtStart: `{head_sha}`\n"
        f"- CleanStart: `{'true' if clean_start else 'false'}`\n\n"
        f"## Objective\n\n"
        f"{args.objective.strip()}\n\n"
        f"## Archive Pointers\n\n"
        f"{pointer_block}\n\n"
        f"## Tasks\n\n"
        f"{task_block}\n\n"
        f"## Success Criteria\n\n"
        f"{criteria_block}\n\n"
        f"## Rulings & Verification\n\n"
        f"- [Init] {human_now()} baseline `{base_tree[:8]}`\n"
    )
    atomic_write(mission_dir / "plan.md", plan_content)
    append_event(
        mission_dir,
        {
            "event": "init",
            "slug": slug,
            "mode": args.mode,
            "repo_root": str(workspace_root),
            "base_tree": base_tree,
            "head_sha": head_sha,
            "clean_start": clean_start,
        },
    )

    print(str(mission_dir))
    for item in pointers:
        print(item)
    return 0


def cmd_task_start(args: argparse.Namespace) -> int:
    mission_dir = resolve_mission_dir(args.mission, Path.cwd())
    plan_text = (mission_dir / "plan.md").read_text(encoding="utf-8")
    meta = read_plan_meta(plan_text)
    workspace_root = Path(meta["RepoRoot"])
    ctx = detect_git_context(workspace_root)
    tree_sha, head_sha, _ = snapshot_tree(workspace_root, ctx)
    append_event(
        mission_dir,
        {
            "event": "task_start",
            "task_id": args.task_id,
            "tree": tree_sha,
            "head_sha": head_sha,
        },
    )
    print(f"task_start {args.task_id} tree={tree_sha[:8]}")
    return 0


def task_line_pattern(task_id: str) -> re.Pattern:
    escaped = re.escape(task_id)
    return re.compile(rf"^(\s*-\s+\[)([ x])(\]\s+(?:\*\*)?{escaped}(?:\*\*)?\s*:.*)$")


def task_exists_in_plan(plan_text: str, task_id: str) -> bool:
    pat = task_line_pattern(task_id)
    return any(pat.match(line) for line in extract_section_lines(plan_text, "Tasks"))


def find_start_tree(events: List[Dict[str, Any]], task_id: str, fallback: str) -> str:
    for ev in reversed(events):
        if ev.get("event") == "task_start" and ev.get("task_id") == task_id:
            return str(ev["tree"])
    for ev in reversed(events):
        if ev.get("event") == "task_done" and ev.get("end_tree"):
            return str(ev["end_tree"])
    return fallback


def cmd_task_done(args: argparse.Namespace, cmd_tokens: List[str]) -> int:
    if not cmd_tokens:
        raise SystemExit("task-done requires a verification command after --")
    mission_dir = resolve_mission_dir(args.mission, Path.cwd())
    plan_path = mission_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    if not task_exists_in_plan(plan_text, args.task_id):
        raise SystemExit(f"Task ID '{args.task_id}' not found in ## Tasks")

    meta = read_plan_meta(plan_text)
    workspace_root = Path(meta["RepoRoot"])
    ctx = detect_git_context(workspace_root)

    if len(cmd_tokens) == 1:
        proc = subprocess.run(
            cmd_tokens[0],
            cwd=str(workspace_root),
            shell=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        cmd_display = cmd_tokens[0]
    else:
        proc = subprocess.run(
            cmd_tokens,
            cwd=str(workspace_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        cmd_display = " ".join(cmd_tokens)

    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "_", args.task_id)
    log_path = mission_dir / "logs" / f"task-{safe_id}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_entry = (
        f"=== {human_now()} | task={args.task_id} | exit={proc.returncode} ===\n"
        f"$ {cmd_display}\n"
        f"{proc.stdout or ''}\n"
    )
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(log_entry)

    out_lines = (proc.stdout or "").splitlines()
    print(f"exit_code={proc.returncode} log={log_path}")
    for line in out_lines[-15:]:
        print(line)

    append_event(
        mission_dir,
        {
            "event": "task_attempt",
            "task_id": args.task_id,
            "cmd": cmd_display,
            "exit_code": proc.returncode,
            "verify_only": bool(args.verify_only),
        },
    )

    if proc.returncode != 0:
        return proc.returncode

    events = read_events(mission_dir)
    start_tree = find_start_tree(events, args.task_id, meta["BaselineTree"])
    end_tree, _, _ = snapshot_tree(workspace_root, ctx)
    changed_files = git_diff_names(workspace_root, ctx, start_tree, end_tree)

    if not changed_files and not args.verify_only:
        print(
            f"Refusing to mark {args.task_id} complete: empty diff since {start_tree[:8]}. "
            f"Pass --verify-only if intentionally no-diff.",
            file=sys.stderr,
        )
        return 2

    pat = task_line_pattern(args.task_id)

    def mark_task(section: List[str]) -> List[str]:
        out: List[str] = []
        for line in section:
            m = pat.match(line)
            if m:
                out.append(f"{m.group(1)}x{m.group(3)}")
            else:
                out.append(line)
        return out

    updated_plan = transform_section(plan_text, "Tasks", mark_task)
    atomic_write(plan_path, updated_plan)

    mode_tag = "verify-only" if args.verify_only else f"{len(changed_files)} files"
    append_receipt_line(
        mission_dir,
        f"- [Task {args.task_id}] {human_now()} passed `{collapse_ws(cmd_display)}` ({mode_tag})",
    )
    append_event(
        mission_dir,
        {
            "event": "task_done",
            "task_id": args.task_id,
            "start_tree": start_tree,
            "end_tree": end_tree,
            "changed_files": changed_files,
            "verify_only": bool(args.verify_only),
        },
    )
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    mission_dir = resolve_mission_dir(args.mission, Path.cwd())
    plan_text = (mission_dir / "plan.md").read_text(encoding="utf-8")
    meta = read_plan_meta(plan_text)
    workspace_root = Path(meta["RepoRoot"])
    ctx = detect_git_context(workspace_root)
    events = read_events(mission_dir)

    if args.task:
        start_tree = find_start_tree(events, args.task, meta["BaselineTree"])
        end_tree = None
        for ev in reversed(events):
            if ev.get("event") == "task_done" and ev.get("task_id") == args.task:
                end_tree = str(ev["end_tree"])
                break
        if end_tree is None:
            end_tree, _, _ = snapshot_tree(workspace_root, ctx)
    else:
        start_tree = meta["BaselineTree"]
        end_tree, _, _ = snapshot_tree(workspace_root, ctx)

    if ctx is None:
        if start_tree == end_tree:
            print("(no workspace changes)")
        else:
            print(f"Non-git workspace changed ({start_tree[:15]} -> {end_tree[:15]})")
        return 0

    diff_args = ["diff"]
    if args.stat:
        diff_args.append("--stat")
    diff_args.extend([start_tree, end_tree])
    proc = run_git(ctx.worktree_root, diff_args, check=True)
    sys.stdout.write(proc.stdout)
    return 0


def cmd_ruling(args: argparse.Namespace) -> int:
    mission_dir = resolve_mission_dir(args.mission, Path.cwd())
    decision = collapse_ws(args.decision)
    why = collapse_ws(args.why)
    cost = collapse_ws(args.cost)
    append_receipt_line(
        mission_dir,
        f"- [Ruling] {human_now()} decision=\"{decision}\" why=\"{why}\" cost=\"{cost}\"",
    )
    append_event(
        mission_dir,
        {"event": "ruling", "decision": decision, "why": why, "cost": cost},
    )
    return 0


def cmd_review_result(args: argparse.Namespace) -> int:
    mission_dir = resolve_mission_dir(args.mission, Path.cwd())
    summary = collapse_ws(args.summary)
    append_receipt_line(
        mission_dir,
        f"- [Review] {human_now()} verdict=`{args.verdict}` summary=\"{summary}\"",
    )
    append_event(
        mission_dir,
        {"event": "review", "verdict": args.verdict, "summary": summary},
    )
    return 0


def cmd_check_criteria(args: argparse.Namespace) -> int:
    mission_dir = resolve_mission_dir(args.mission, Path.cwd())
    if not args.all and not args.index:
        raise SystemExit("Pass --all or at least one --index N")
    plan_path = mission_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    wanted = set(args.index or [])
    matched_indices: set[int] = set()

    def mark_criteria(section: List[str]) -> List[str]:
        out: List[str] = []
        idx = 0
        for line in section:
            m = re.match(r"^(\s*-\s+\[)([ x])(\]\s+.*)$", line)
            if m:
                idx += 1
                if args.all or idx in wanted:
                    matched_indices.add(idx)
                    out.append(f"{m.group(1)}x{m.group(3)}")
                else:
                    out.append(line)
            else:
                out.append(line)
        return out

    updated = transform_section(plan_text, "Success Criteria", mark_criteria)
    missing = wanted - matched_indices
    if missing:
        raise SystemExit(f"Criteria index out of range: {sorted(missing)}")
    atomic_write(plan_path, updated)
    return 0


def cmd_audit(args: argparse.Namespace) -> int:
    mission_dir = resolve_mission_dir(args.mission, Path.cwd())
    plan_path = mission_dir / "plan.md"
    plan_text = plan_path.read_text(encoding="utf-8")
    meta = read_plan_meta(plan_text)
    events = read_events(mission_dir)
    errors: List[str] = []

    if not events:
        errors.append("Missing mechanical event log (logs/.events.jsonl)")

    task_lines = extract_section_lines(plan_text, "Tasks")
    checked_tasks: List[str] = []
    unchecked_tasks = 0
    total_tasks = 0
    for line in task_lines:
        m = re.match(r"^\s*-\s+\[([ x])\]\s+(?:\*\*)?([^:*\s]+)(?:\*\*)?\s*:", line)
        if m:
            total_tasks += 1
            if m.group(1) == " ":
                unchecked_tasks += 1
            else:
                checked_tasks.append(m.group(2))
        elif re.match(r"^\s*-\s+\[ \]", line):
            unchecked_tasks += 1
            total_tasks += 1
    if total_tasks == 0:
        errors.append("No tasks found in ## Tasks")
    if unchecked_tasks > 0:
        errors.append(f"{unchecked_tasks} unchecked task(s) remain in ## Tasks")

    done_ids = {ev.get("task_id") for ev in events if ev.get("event") == "task_done"}
    unbacked = [tid for tid in checked_tasks if tid not in done_ids]
    if unbacked:
        errors.append(f"Checked task(s) missing task_done receipt: {', '.join(unbacked)}")

    criteria_lines = extract_section_lines(plan_text, "Success Criteria")
    unchecked_criteria = sum(
        1 for line in criteria_lines if re.match(r"^\s*-\s+\[ \]", line)
    )
    if unchecked_criteria > 0:
        errors.append(f"{unchecked_criteria} unchecked item(s) remain in ## Success Criteria")

    workspace_root = Path(meta["RepoRoot"])
    ctx = detect_git_context(workspace_root)
    curr_tree, _, _ = snapshot_tree(workspace_root, ctx)
    net_files = git_diff_names(workspace_root, ctx, meta["BaselineTree"], curr_tree)
    if not net_files and not args.verify_only:
        errors.append("Net diff from mission BaselineTree is empty (pass --verify-only if intentional)")

    reviews = [ev for ev in events if ev.get("event") == "review"]
    if not reviews:
        errors.append("Missing fresh reviewer receipt (review-result)")
    elif reviews[-1].get("verdict") != "pass":
        errors.append(f"Latest review verdict is '{reviews[-1].get('verdict')}', expected 'pass'")

    has_distill = any(
        ev.get("event") in {"distill", "skip_distill"} for ev in events
    )
    if not has_distill:
        errors.append("Missing distillation decision (distill or skip-distill)")

    if errors:
        for err in errors:
            print(f"AUDIT FAIL: {err}", file=sys.stderr)
        return 1

    updated = re.sub(
        r"^- Status:\s*`[^`]*`",
        "- Status: `completed`",
        plan_text,
        count=1,
        flags=re.MULTILINE,
    )
    atomic_write(plan_path, updated)
    diff_desc = "verify-only" if args.verify_only else f"diff={len(net_files)} files"
    append_receipt_line(
        mission_dir,
        f"- [Audit] pass ({human_now()}, tasks={len(checked_tasks)}, {diff_desc})",
    )
    if not args.keep_logs and (mission_dir / "logs").is_dir():
        shutil.rmtree(mission_dir / "logs")
    print(f"AUDIT PASS: {mission_dir} (tasks={len(checked_tasks)}, {diff_desc})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Mission Runner v3 control plane")
    sub = parser.add_subparsers(dest="command", required=True)

    p_slug = sub.add_parser("slug", help="Resolve canonical project archive slug")
    p_slug.add_argument("--cwd", default=".")
    p_slug.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR))

    p_init = sub.add_parser("init", help="Initialize an isolated mission plan workspace")
    p_init.add_argument("--title", required=True)
    p_init.add_argument("--objective", required=True)
    p_init.add_argument("--cwd", default=".")
    p_init.add_argument("--terms", default="")
    p_init.add_argument("--mode", choices=["inline", "subagent", "worktree"], default="inline")
    p_init.add_argument("--slug", default="")
    p_init.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR))
    p_init.add_argument("--task", action="append", default=[])
    p_init.add_argument("--criteria", action="append", default=[])

    p_tstart = sub.add_parser("task-start", help="Snapshot tree before executing a task")
    p_tstart.add_argument("task_id")
    p_tstart.add_argument("--mission", default="")

    p_tdone = sub.add_parser("task-done", help="Verify and mark a task complete")
    p_tdone.add_argument("task_id")
    p_tdone.add_argument("--mission", default="")
    p_tdone.add_argument("--verify-only", action="store_true")

    p_diff = sub.add_parser("diff", help="Show git diff since baseline or task start")
    p_diff.add_argument("--mission", default="")
    p_diff.add_argument("--task", default="")
    p_diff.add_argument("--stat", action="store_true")

    p_ruling = sub.add_parser("ruling", help="Record an autonomous ruling in plan.md")
    p_ruling.add_argument("--mission", default="")
    p_ruling.add_argument("--decision", required=True)
    p_ruling.add_argument("--why", required=True)
    p_ruling.add_argument("--cost", default="none")

    p_review = sub.add_parser("review-result", help="Record reviewer verdict")
    p_review.add_argument("--mission", default="")
    p_review.add_argument("--verdict", choices=["pass", "revise"], required=True)
    p_review.add_argument("--summary", required=True)

    p_crit = sub.add_parser("check-criteria", help="Mark success criteria complete")
    p_crit.add_argument("--mission", default="")
    p_crit.add_argument("--all", action="store_true")
    p_crit.add_argument("--index", type=int, action="append", default=[])

    p_audit = sub.add_parser("audit", help="Run final mechanical mission audit")
    p_audit.add_argument("--mission", default="")
    p_audit.add_argument("--verify-only", action="store_true")
    p_audit.add_argument("--keep-logs", action="store_true")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    cmd_tail: List[str] = []
    if "--" in raw_argv:
        sep = raw_argv.index("--")
        cmd_tail = raw_argv[sep + 1 :]
        raw_argv = raw_argv[:sep]

    parser = build_parser()
    args = parser.parse_args(raw_argv)

    dispatch = {
        "slug": lambda: cmd_slug(args),
        "init": lambda: cmd_init(args),
        "task-start": lambda: cmd_task_start(args),
        "task-done": lambda: cmd_task_done(args, cmd_tail),
        "diff": lambda: cmd_diff(args),
        "ruling": lambda: cmd_ruling(args),
        "review-result": lambda: cmd_review_result(args),
        "check-criteria": lambda: cmd_check_criteria(args),
        "audit": lambda: cmd_audit(args),
    }
    return dispatch[args.command]()


if __name__ == "__main__":
    sys.exit(main())
