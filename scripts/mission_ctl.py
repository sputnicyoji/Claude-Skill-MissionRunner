#!/usr/bin/env python3
"""Mechanical control plane for mission-runner v3."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import locale
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

EN_STOPWORDS = frozenset(
    {
        "a", "an", "and", "any", "are", "as", "at", "be", "been", "being",
        "both", "but", "by", "can", "could", "did", "do", "does", "done",
        "during", "each", "else", "every", "few", "for", "from", "get",
        "got", "had", "has", "have", "he", "her", "here", "hers", "him",
        "his", "how", "i", "if", "in", "into", "is", "it", "its", "just",
        "like", "look", "made", "make", "makes", "many", "may", "me",
        "might", "mine", "more", "most", "much", "must", "my", "need",
        "needed", "needs", "new", "no", "not", "now", "of", "off", "ok",
        "old", "on", "only", "onto", "or", "other", "our", "out", "over",
        "put", "read", "run", "same", "see", "set", "shall", "she",
        "should", "so", "some", "such", "than", "that", "the", "their",
        "them", "then", "there", "these", "they", "this", "those", "to",
        "too", "under", "up", "upon", "us", "use", "used", "using", "very",
        "want", "was", "way", "we", "well", "were", "what", "when",
        "where", "which", "while", "who", "why", "will", "with", "would",
        "yes", "yet", "you", "your",
        # Generic coding task verbs/nouns that create false cross-lesson noise
        "add", "bug", "bugs", "build", "change", "changes", "check",
        "checks", "code", "create", "delete", "edit", "error", "errors",
        "file", "files", "fix", "fixed", "fixes", "implement", "issue",
        "issues", "modify", "note", "notes", "plan", "remove", "task",
        "tasks", "test", "tests", "update", "updated", "work", "works",
        "write",
    }
)

CJK_STOP_BIGRAMS = frozenset(
    {
        "\u4fee\u590d",  # xiu fu
        "\u6dfb\u52a0",  # tian jia
        "\u66f4\u65b0",  # geng xin
        "\u5b9e\u73b0",  # shi xian
        "\u68c0\u67e5",  # jian cha
        "\u95ee\u9898",  # wen ti
        "\u9700\u8981",  # xu yao
        "\u4f7f\u7528",  # shi yong
        "\u8fdb\u884c",  # jin xing
        "\u65b9\u6cd5",  # fang fa
        "\u5904\u7406",  # chu li
        "\u4ee3\u7801",  # dai ma
        "\u6587\u4ef6",  # wen jian
        "\u6d4b\u8bd5",  # ce shi
    }
)

CJK_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")
CJK_SPAN_RE = re.compile(r"[\u4e00-\u9fff]+")
KEBAB_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


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
        # newline="\n": text mode would otherwise write CRLF on Windows.
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
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
    # Git prints UTF-8; the default text mode would decode it with the
    # Windows ANSI code page and crash on CJK diffs. Diff lines from files
    # stored in another encoding (e.g. GBK sources) show as U+FFFD.
    proc = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        env=env,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc


def decode_output(data: bytes) -> str:
    """Decode a verification command's output without ever raising.

    Most toolchains print UTF-8; native Windows tools print the ANSI code
    page (e.g. cp936), so fall back to the locale encoding.
    """
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        text = data.decode(locale.getpreferredencoding(False), errors="replace")
    return text.replace("\r\n", "\n").replace("\r", "\n")


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
    # Rewrite in place: keeps the user's file mode, which a temp-file swap would reset.
    with exclude_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(existing + prefix + "_planning/\n")


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
    with events_path.open("a", encoding="utf-8", newline="\n") as fh:
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
    if not archive_dir.is_dir():
        return []
    lessons_dir = archive_dir / slug / "lessons"
    if not lessons_dir.is_dir():
        return []

    q_en, q_cjk, q_norm = tokenize_bilingual(f"{query} {terms}".strip())
    if not q_en and not q_cjk:
        return []

    scored: List[Tuple[float, str, str, str]] = []
    for path in sorted(lessons_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8", errors="replace")
        parsed = parse_lesson_document(raw, path.name)
        meta = parsed["meta"]
        name = str(meta.get("name") or infer_lesson_name(path.name))
        desc = str(meta.get("description") or "").strip()
        mdate = str(meta.get("mission_date") or infer_lesson_date(path.name) or "unknown")
        kw_list = [str(k).strip() for k in meta.get("keywords", []) if str(k).strip()]

        kw_en: set[str] = set()
        kw_cjk: set[str] = set()
        phrase_bonus = 0.0
        for kw in kw_list:
            k_en, k_cjk, k_norm = tokenize_bilingual(kw)
            kw_en |= k_en
            kw_cjk |= k_cjk
            if len(k_norm) >= 2 and (k_en or k_cjk):
                if re.search(rf"(?<![a-z0-9]){re.escape(k_norm)}(?![a-z0-9])", q_norm):
                    phrase_bonus += 4.0

        meta_en, meta_cjk, _ = tokenize_bilingual(f"{name} {desc}")
        body_en, body_cjk, _ = tokenize_bilingual(parsed["body"])

        kw_hits = len(q_en & kw_en) + len(q_cjk & kw_cjk)
        meta_hits = len(q_en & meta_en) + len(q_cjk & meta_cjk)
        body_hits = len(q_en & body_en) + len(q_cjk & body_cjk)

        # Require either a strong metadata/keyword signal or >=2 distinct body hits
        if kw_hits == 0 and meta_hits == 0 and body_hits < 2 and phrase_bonus == 0.0:
            continue

        score = kw_hits * 5.0 + meta_hits * 2.5 + min(body_hits, 6) * 0.8 + phrase_bonus
        if score < 2.5:
            continue

        one_line_desc = collapse_ws(desc) or "No description"
        pointer = f"- `{name}` ({mdate}) -- {one_line_desc} (`{path}`)"
        scored.append((score, mdate, name, pointer))

    scored.sort(key=lambda item: (-item[0], -date_sort_key(item[1]), item[2]))
    return [item[3] for item in scored[: max(limit, 0)]]


def date_sort_key(date_str: str) -> int:
    digits = re.sub(r"[^0-9]", "", date_str)
    if len(digits) == 8:
        return int(digits)
    return 0


def stem_en_variants(token: str) -> set[str]:
    forms = {token}
    if len(token) >= 5 and token.endswith("ies"):
        forms.add(token[:-3] + "y")
    elif len(token) >= 5 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        forms.add(token[:-1])
    return forms


def tokenize_bilingual(text: str) -> Tuple[set[str], set[str], str]:
    split_camel = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    norm = re.sub(r"[-_./:]+", " ", split_camel.lower())
    raw_words = re.findall(r"[a-z0-9]+", norm)
    en_tokens: set[str] = set()
    for word in raw_words:
        if len(word) < 2 or not re.search(r"[a-z]", word):
            continue
        if word in EN_STOPWORDS:
            continue
        for variant in stem_en_variants(word):
            if variant not in EN_STOPWORDS:
                en_tokens.add(variant)

    cjk_bigrams: set[str] = set()
    for span in CJK_SPAN_RE.findall(text):
        if len(span) >= 2:
            for idx in range(len(span) - 1):
                bg = span[idx : idx + 2]
                if bg not in CJK_STOP_BIGRAMS:
                    cjk_bigrams.add(bg)
    return en_tokens, cjk_bigrams, norm


def infer_lesson_date(filename: str) -> str:
    m = re.match(r"^(\d{4}-\d{2}-\d{2})(?:-|$)", filename)
    return m.group(1) if m else ""


def infer_lesson_name(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", stem)
    stem = re.sub(r"-r\d+$", "", stem)
    return normalize_slug(stem) or "lesson"


def unquote_yaml_scalar(val: str) -> Tuple[str, bool]:
    s = val.strip()
    if not s:
        return "", False
    if (s.startswith('"') and s.endswith('"') and len(s) >= 2):
        try:
            loaded = json.loads(s)
            if isinstance(loaded, str):
                return loaded, False
        except Exception:
            return s[1:-1], True
    if s.startswith("'") and s.endswith("'") and len(s) >= 2:
        return s[1:-1].replace("''", "'"), False
    if s.startswith('"') or s.startswith("'") or s.endswith('"') or s.endswith("'"):
        return s.strip("\"'"), True
    needs_quote = (
        ": " in s
        or s.startswith(("`", "*", "&", "{", "[", "#", "!", "|", ">"))
    )
    return s, needs_quote


def parse_keywords_value(raw_val: str) -> Tuple[List[str], bool]:
    s = raw_val.strip()
    if not s:
        return [], False
    if s.startswith("["):
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x).strip() for x in parsed if str(x).strip()], False
        except Exception:
            pass
        inner = s[1:-1] if s.endswith("]") else s[1:]
        items = [unquote_yaml_scalar(p)[0].strip() for p in re.split(r"[,\uff0c]", inner)]
        return [it for it in items if it], True
    # Comma-separated scalar keywords
    items = [unquote_yaml_scalar(p)[0].strip() for p in re.split(r"[,\uff0c]", s)]
    cleaned = [it for it in items if it]
    return cleaned, True


def split_frontmatter(raw_text: str) -> Tuple[Optional[str], str, bool]:
    text = raw_text.lstrip("\ufeff").replace("\r\n", "\n")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None, text, False
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            fm = "".join(lines[1:idx])
            body = "".join(lines[idx + 1 :])
            return fm, body, False
    return None, text, True


def parse_lesson_document(raw_text: str, filename: str = "") -> Dict[str, Any]:
    fm_text, body, broken_fence = split_frontmatter(raw_text)
    issues: List[str] = []
    meta: Dict[str, Any] = {}
    nested_meta: Dict[str, Any] = {}

    if broken_fence:
        issues.append("unclosed_frontmatter")
    if fm_text is None and not broken_fence:
        issues.append("missing_frontmatter")

    if fm_text is not None:
        fm_lines = fm_text.splitlines()
        i = 0
        in_metadata_block = False
        active_list_key: Optional[str] = None
        while i < len(fm_lines):
            line = fm_lines[i]
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                i += 1
                continue
            indent = len(line) - len(line.lstrip(" "))

            if indent == 0:
                in_metadata_block = False
                active_list_key = None
                m = re.match(r"^([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
                if not m:
                    issues.append("invalid_yaml_line")
                    i += 1
                    continue
                key, rest = m.group(1), m.group(2)
                if key == "metadata" and not rest.strip():
                    in_metadata_block = True
                    issues.append("nested_metadata")
                    i += 1
                    continue
                if not rest.strip():
                    # Look ahead for YAML list or nested keys
                    meta[key] = []
                    active_list_key = key
                    i += 1
                    continue
                if rest.strip() in {"|", ">", "|-", ">-"}:
                    block_lines: List[str] = []
                    j = i + 1
                    while j < len(fm_lines):
                        nxt = fm_lines[j]
                        if nxt.strip() and (len(nxt) - len(nxt.lstrip(" ")) == 0):
                            break
                        block_lines.append(nxt.strip())
                        j += 1
                    meta[key] = collapse_ws(" ".join(block_lines))
                    i = j
                    continue
                if key == "keywords":
                    kws, was_scalar = parse_keywords_value(rest)
                    meta["keywords"] = kws
                    if was_scalar:
                        issues.append("scalar_keywords")
                else:
                    val, unsafe = unquote_yaml_scalar(rest)
                    meta[key] = val
                    if unsafe:
                        issues.append(f"unsafe_scalar:{key}")
                i += 1
                continue

            # Indented line
            if active_list_key is not None and re.match(r"^\s+-\s+(.*)$", line):
                item_raw = re.match(r"^\s+-\s+(.*)$", line).group(1)
                val, _ = unquote_yaml_scalar(item_raw)
                if not isinstance(meta.get(active_list_key), list):
                    meta[active_list_key] = []
                if val:
                    meta[active_list_key].append(val)
                i += 1
                continue

            if in_metadata_block:
                nm = re.match(r"^\s+([A-Za-z0-9_-]+)\s*:\s*(.*)$", line)
                if nm:
                    nkey, nrest = nm.group(1), nm.group(2)
                    if nrest.strip():
                        nval, _ = unquote_yaml_scalar(nrest)
                        nested_meta[nkey] = nval
                i += 1
                continue

            issues.append("unexpected_indent")
            i += 1

    # Promote nested metadata keys carefully
    if "mission_date" in nested_meta and not meta.get("mission_date"):
        meta["mission_date"] = nested_meta["mission_date"]
        issues.append("nested_mission_date")
    if "keywords" not in meta or not meta["keywords"]:
        if isinstance(meta.get("tags"), list) and meta["tags"]:
            meta["keywords"] = list(meta["tags"])
        elif "tags" in nested_meta and nested_meta["tags"]:
            kws, _ = parse_keywords_value(str(nested_meta["tags"]))
            meta["keywords"] = kws
        else:
            meta.setdefault("keywords", [])

    if isinstance(meta.get("keywords"), str):
        kws, _ = parse_keywords_value(str(meta["keywords"]))
        meta["keywords"] = kws
        issues.append("scalar_keywords")

    if not meta.get("name") and filename:
        meta["name"] = infer_lesson_name(filename)
        issues.append("missing_name")
    else:
        raw_name = str(meta.get("name", "")).strip()
        if raw_name and normalize_slug(raw_name) != raw_name and " " in raw_name:
            meta["name"] = normalize_slug(raw_name)

    if not meta.get("mission_date"):
        inferred = infer_lesson_date(filename)
        if inferred:
            meta["mission_date"] = inferred
            issues.append("missing_mission_date")

    if not meta.get("description"):
        fallback_desc = extract_fallback_description(body)
        if fallback_desc:
            meta["description"] = fallback_desc
            issues.append("missing_description")

    return {"meta": meta, "body": body, "issues": issues}


def extract_fallback_description(body: str) -> str:
    for line in body.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        s = re.sub(r"^\*\*[^*]+\*\*:?\s*", "", s)
        s = collapse_ws(s)
        if s:
            return s[:160]
    return ""


def serialize_lesson_frontmatter(meta: Dict[str, Any]) -> str:
    ordered = ["name", "description", "keywords", "mission_date"]
    lines = ["---"]
    for key in ordered:
        if key == "keywords":
            kws = [str(k).strip() for k in meta.get("keywords", []) if str(k).strip()]
            lines.append(f"keywords: {json.dumps(kws, ensure_ascii=False)}")
        elif key in meta and str(meta[key]).strip():
            lines.append(f"{key}: {json.dumps(str(meta[key]).strip(), ensure_ascii=False)}")
    for key, val in meta.items():
        if key in ordered or key == "metadata":
            continue
        if isinstance(val, list):
            cleaned = [str(x).strip() for x in val if str(x).strip()]
            lines.append(f"{key}: {json.dumps(cleaned, ensure_ascii=False)}")
        elif str(val).strip():
            lines.append(f"{key}: {json.dumps(str(val).strip(), ensure_ascii=False)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def validate_strict_frontmatter(raw_text: str) -> List[str]:
    errs: List[str] = []
    fm, _, broken = split_frontmatter(raw_text)
    if broken or fm is None:
        return ["missing or unclosed frontmatter"]
    seen_keys: set[str] = set()
    for lineno, line in enumerate(fm.splitlines(), start=1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            errs.append(f"line {lineno}: unexpected indentation")
            continue
        m = re.match(r"^([A-Za-z0-9_-]+):\s*(.+)$", line)
        if not m:
            errs.append(f"line {lineno}: invalid key-value syntax")
            continue
        key, raw_val = m.group(1), m.group(2).strip()
        seen_keys.add(key)
        if key == "keywords":
            try:
                parsed = json.loads(raw_val)
                if not isinstance(parsed, list):
                    errs.append(f"line {lineno}: keywords is not a JSON/YAML array")
            except Exception as exc:
                errs.append(f"line {lineno}: invalid keywords array ({exc})")
        else:
            if raw_val.startswith('"'):
                try:
                    parsed = json.loads(raw_val)
                    if not isinstance(parsed, str):
                        errs.append(f"line {lineno}: expected string value")
                except Exception as exc:
                    errs.append(f"line {lineno}: invalid quoted string ({exc})")
            elif raw_val.startswith(("`", "*", "&", "{", "[", "'")) or ": " in raw_val:
                errs.append(f"line {lineno}: unsafe unquoted scalar for {key}")
    for req in ("name", "description", "keywords", "mission_date"):
        if req not in seen_keys:
            errs.append(f"missing required key: {req}")
    return errs


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
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        cmd_display = cmd_tokens[0]
    else:
        proc = subprocess.run(
            cmd_tokens,
            cwd=str(workspace_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        cmd_display = " ".join(cmd_tokens)
    output = decode_output(proc.stdout or b"")

    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "_", args.task_id)
    log_path = mission_dir / "logs" / f"task-{safe_id}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_entry = (
        f"=== {human_now()} | task={args.task_id} | exit={proc.returncode} ===\n"
        f"$ {cmd_display}\n"
        f"{output}\n"
    )
    with log_path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(log_entry)

    out_lines = output.splitlines()
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


def cmd_match_lessons(args: argparse.Namespace) -> int:
    archive_dir = Path(args.archive_dir).expanduser().resolve()
    if args.slug:
        slug = normalize_slug(args.slug)
    else:
        cwd = Path(args.cwd).resolve()
        slug = resolve_slug(cwd, archive_dir)
    pointers = find_matched_lessons(
        slug=slug,
        query=args.query,
        terms=args.terms or "",
        archive_dir=archive_dir,
        limit=args.limit,
    )
    for item in pointers:
        print(item)
    return 0


def effective_bilingual_length(text: str) -> int:
    cjk_count = len(CJK_CHAR_RE.findall(text))
    ascii_only_text = CJK_CHAR_RE.sub(" ", text)
    ascii_words = re.findall(r"[A-Za-z0-9_]+", ascii_only_text)
    return len(ascii_words) + cjk_count


def parse_cli_keywords(raw: str) -> List[str]:
    s = raw.strip()
    items: List[str] = []
    if s.startswith("["):
        try:
            loaded = json.loads(s)
            if isinstance(loaded, list):
                items = [collapse_ws(str(x)) for x in loaded]
        except Exception:
            items = [collapse_ws(p) for p in re.split(r"[,\uff0c]", s.strip("[]"))]
    else:
        items = [collapse_ws(p) for p in re.split(r"[,\uff0c]", s)]
    deduped: List[str] = []
    seen: set[str] = set()
    for item in items:
        key = item.lower()
        if item and key not in seen:
            seen.add(key)
            deduped.append(item)
    return deduped


def cmd_distill(args: argparse.Namespace) -> int:
    mission_dir = resolve_mission_dir(args.mission, Path.cwd())
    plan_text = (mission_dir / "plan.md").read_text(encoding="utf-8")
    meta = read_plan_meta(plan_text)
    slug = normalize_slug(meta.get("Slug", "")) or "workspace"

    name = args.name.strip()
    if not KEBAB_RE.match(name) or not (2 <= len(name) <= 80):
        print("DISTILL REJECTED: --name must be lowercase kebab-case (2..80 chars)", file=sys.stderr)
        return 2

    description = collapse_ws(args.description)
    if not description:
        print("DISTILL REJECTED: --description cannot be empty", file=sys.stderr)
        return 2

    evidence = collapse_ws(args.evidence)
    if not evidence:
        print("DISTILL REJECTED: --evidence is required", file=sys.stderr)
        return 2

    keywords = parse_cli_keywords(args.keywords)
    if len(keywords) < 2:
        print("DISTILL REJECTED: at least 2 distinct keywords required", file=sys.stderr)
        return 2

    if not args.ascii_only:
        has_ascii = any(re.search(r"[A-Za-z0-9]", kw) for kw in keywords)
        has_cjk = any(CJK_CHAR_RE.search(kw) for kw in keywords)
        if not (has_ascii and has_cjk):
            print(
                "DISTILL REJECTED: bilingual keywords required (>=1 ASCII and >=1 CJK, or pass --ascii-only)",
                file=sys.stderr,
            )
            return 2

    if args.body_file:
        body = Path(args.body_file).expanduser().read_text(encoding="utf-8").strip()
    elif args.body is not None:
        body = args.body.strip()
    else:
        print("DISTILL REJECTED: pass --body or --body-file", file=sys.stderr)
        return 2

    eff_len = effective_bilingual_length(body)
    if not (10 <= eff_len <= 150):
        print(
            f"DISTILL REJECTED: effective lesson length {eff_len} outside 10..150 units",
            file=sys.stderr,
        )
        return 2

    archive_dir = Path(args.archive_dir).expanduser().resolve()
    lessons_dir = archive_dir / slug / "lessons"
    lessons_dir.mkdir(parents=True, exist_ok=True)
    mdate = now_local().strftime("%Y-%m-%d")

    target = lessons_dir / f"{mdate}-{name}.md"
    rev = 2
    while target.exists():
        target = lessons_dir / f"{mdate}-{name}-r{rev}.md"
        rev += 1

    fm = serialize_lesson_frontmatter(
        {
            "name": name,
            "description": description,
            "keywords": keywords,
            "mission_date": mdate,
        }
    )
    lesson_doc = (
        f"{fm}\n"
        f"# Lesson: {name}\n\n"
        f"**Lesson:** {body}\n\n"
        f"**Evidence:** {evidence}\n"
    )
    atomic_write(target, lesson_doc)
    append_receipt_line(mission_dir, f"- [Distill] saved `{target}`")
    append_event(
        mission_dir,
        {
            "event": "distill",
            "lesson_path": str(target),
            "name": name,
            "keywords": keywords,
        },
    )
    print(str(target))
    return 0


def count_distill_triggers(events: List[Dict[str, Any]]) -> Dict[str, int]:
    failed = sum(
        1
        for ev in events
        if ev.get("event") == "task_attempt" and int(ev.get("exit_code", 0)) != 0
    )
    revises = sum(
        1
        for ev in events
        if ev.get("event") == "review" and ev.get("verdict") == "revise"
    )
    rulings = sum(1 for ev in events if ev.get("event") == "ruling")
    return {"failed_attempts": failed, "revise_reviews": revises, "rulings": rulings}


def cmd_skip_distill(args: argparse.Namespace) -> int:
    mission_dir = resolve_mission_dir(args.mission, Path.cwd())
    reason = collapse_ws(args.reason)
    if not reason:
        print("SKIP REJECTED: --reason cannot be empty", file=sys.stderr)
        return 2
    events = read_events(mission_dir)
    triggers = count_distill_triggers(events)
    total = sum(triggers.values())
    if total > 0 and not args.local_only:
        print(
            f"SKIP REJECTED: {total} learning trigger(s) recorded ({triggers}). "
            f"Distill 1-2 lessons or pass --local-only if strictly machine/one-off.",
            file=sys.stderr,
        )
        return 2
    append_receipt_line(mission_dir, f"- [Distill] skipped (reason=\"{reason}\")")
    append_event(
        mission_dir,
        {
            "event": "skip_distill",
            "reason": reason,
            "local_only": bool(args.local_only),
            "triggers": triggers,
        },
    )
    print(f"skip_distill recorded ({reason})")
    return 0


def discover_scan_repo_merges(
    scan_root: Path, existing_dirs: Dict[str, Path]
) -> List[Tuple[str, str, str]]:
    if not scan_root.is_dir():
        return []
    candidates: List[Path] = []
    if (scan_root / ".git").exists():
        candidates.append(scan_root)
    else:
        for child in sorted(scan_root.iterdir()):
            if child.is_dir() and (child / ".git").exists():
                candidates.append(child)

    norm_map = {normalize_slug(k): k for k in existing_dirs}
    merges: List[Tuple[str, str, str]] = []
    for repo in candidates:
        ctx = detect_git_context(repo)
        if ctx is None:
            continue
        dir_slug = normalize_slug(ctx.main_root.name)
        origin_slug = parse_origin_slug(ctx.origin_url)
        if not origin_slug or not dir_slug or origin_slug == dir_slug:
            continue
        if dir_slug in norm_map and origin_slug in norm_map:
            src_actual = norm_map[dir_slug]
            dst_actual = norm_map[origin_slug]
            if src_actual != dst_actual:
                merges.append((src_actual, dst_actual, f"repo {repo.name} duplicate slug"))
    return merges


def cmd_doctor_archive(args: argparse.Namespace) -> int:
    archive_dir = Path(args.archive_dir).expanduser().resolve()
    if not archive_dir.is_dir():
        print(f"Archive directory not found: {archive_dir}", file=sys.stderr)
        return 1

    existing_dirs = {
        d.name: d
        for d in sorted(archive_dir.iterdir())
        if d.is_dir() and not d.name.startswith(".")
    }

    merge_map: Dict[str, str] = {}
    merge_reasons: Dict[str, str] = {}

    for ns in existing_dirs:
        norm = normalize_slug(ns)
        if norm and norm != ns:
            merge_map[ns] = norm
            merge_reasons[ns] = "non-kebab directory name"

    if args.scan_repos:
        for src, dst, reason in discover_scan_repo_merges(
            Path(args.scan_repos).expanduser().resolve(), existing_dirs
        ):
            target = merge_map.get(dst, dst)
            merge_map[src] = target
            merge_reasons[src] = reason

    for spec in args.merge or []:
        if ":" not in spec:
            raise SystemExit(f"Invalid --merge spec '{spec}', expected SRC:DST")
        src, dst = spec.split(":", 1)
        src_clean = src.strip()
        dst_clean = normalize_slug(dst.strip()) or dst.strip()
        if src_clean and dst_clean and src_clean != dst_clean:
            merge_map[src_clean] = dst_clean
            merge_reasons[src_clean] = "explicit --merge"

    def resolve_target_ns(ns: str) -> str:
        cur = ns
        seen: set[str] = set()
        while cur in merge_map and cur not in seen:
            seen.add(cur)
            cur = merge_map[cur]
        return cur

    final_merges: List[Tuple[str, str, str]] = []
    for src in sorted(existing_dirs):
        dst = resolve_target_ns(src)
        if dst != src:
            final_merges.append((src, dst, merge_reasons.get(src, "normalized")))

    # Collect all lesson files per source namespace and simulate / prepare outputs
    # Track target_ns -> {filename -> (normalized_content, body_hash, keywords)}
    planned_targets: Dict[str, Dict[str, Tuple[str, str]]] = {}
    stats = {
        "scanned": 0,
        "repaired": 0,
        "deduplicated": 0,
        "collisions_renamed": 0,
        "written": 0,
        "removed_files": 0,
    }

    # Pre-load destination namespaces first so existing target filenames stay canonical
    ordered_namespaces = sorted(
        existing_dirs.keys(),
        key=lambda ns: (1 if resolve_target_ns(ns) != ns else 0, ns),
    )

    body_hashes_by_target: Dict[str, set[str]] = {}
    file_writes: List[Tuple[Path, str]] = []
    files_to_remove: List[Path] = []

    for src_ns in ordered_namespaces:
        target_ns = resolve_target_ns(src_ns)
        lessons_dir = existing_dirs[src_ns] / "lessons"
        if not lessons_dir.is_dir():
            continue
        target_lessons_dir = archive_dir / target_ns / "lessons"
        if target_ns not in planned_targets:
            planned_targets[target_ns] = {}
            body_hashes_by_target[target_ns] = set()

        for path in sorted(lessons_dir.glob("*.md")):
            stats["scanned"] += 1
            raw = path.read_text(encoding="utf-8", errors="replace")
            parsed = parse_lesson_document(raw, path.name)
            strict_errs = validate_strict_frontmatter(raw)
            needs_repair = bool(parsed["issues"] or strict_errs)

            fm = serialize_lesson_frontmatter(parsed["meta"])
            repaired_text = fm + "\n" + parsed["body"].lstrip("\n")
            if needs_repair and repaired_text != raw:
                stats["repaired"] += 1

            body_norm = parsed["body"].strip()
            body_hash = hashlib.sha256(body_norm.encode("utf-8")).hexdigest()

            same_inode_dir = (
                target_lessons_dir.parent.exists()
                and os.path.samefile(existing_dirs[src_ns], target_lessons_dir.parent)
            )
            is_moving = (src_ns != target_ns) and not same_inode_dir
            if is_moving and body_hash in body_hashes_by_target[target_ns]:
                stats["deduplicated"] += 1
                files_to_remove.append(path)
                continue

            body_hashes_by_target[target_ns].add(body_hash)
            dest_name = path.name
            if dest_name in planned_targets[target_ns]:
                stats["collisions_renamed"] += 1
                stem = Path(dest_name).stem
                rev = 2
                while f"{stem}-r{rev}.md" in planned_targets[target_ns]:
                    rev += 1
                dest_name = f"{stem}-r{rev}.md"

            planned_targets[target_ns][dest_name] = (repaired_text, body_hash)
            dest_path = target_lessons_dir / dest_name
            if is_moving or repaired_text != raw or dest_name != path.name:
                file_writes.append((dest_path, repaired_text))
                stats["written"] += 1
            if is_moving:
                files_to_remove.append(path)
                stats["removed_files"] += 1

    print(f"Archive: {archive_dir}")
    print(f"Scanned lessons: {stats['scanned']}")
    print(f"Planned namespace merges ({len(final_merges)}):")
    if final_merges:
        for src, dst, reason in final_merges:
            print(f"  {src} -> {dst} ({reason})")
    else:
        print("  (none)")
    print(
        f"Frontmatter repairs: {stats['repaired']} | "
        f"Deduplicated: {stats['deduplicated']} | "
        f"Collisions renamed: {stats['collisions_renamed']}"
    )

    if args.dry_run:
        return 0

    if args.backup_dir:
        backup_path = Path(args.backup_dir).expanduser().resolve()
        if backup_path.exists():
            print(f"Backup directory already exists: {backup_path}", file=sys.stderr)
            return 2
        shutil.copytree(archive_dir, backup_path)
        print(f"Backup written: {backup_path}")

    for dest_path, content in file_writes:
        atomic_write(dest_path, content)

    written_set = {str(p.resolve()) for p, _ in file_writes}
    for old_path in files_to_remove:
        if str(old_path.resolve()) not in written_set and old_path.exists():
            old_path.unlink()

    for src_ns, dst_ns, _ in final_merges:
        src_dir = existing_dirs[src_ns]
        dst_dir = archive_dir / dst_ns
        if src_dir.is_dir():
            if dst_dir.exists() and os.path.samefile(src_dir, dst_dir):
                tmp_rename = archive_dir / f".tmp_case_{dst_ns}"
                os.rename(src_dir, tmp_rename)
                os.rename(tmp_rename, dst_dir)
            else:
                remaining = [
                    p for p in src_dir.rglob("*") if p.is_file() and p.name != ".DS_Store"
                ]
                if not remaining:
                    shutil.rmtree(src_dir)

    # Strict validation sweep over entire resulting archive
    remaining_errors: List[str] = []
    final_dirs = sorted(
        d.name for d in archive_dir.iterdir() if d.is_dir() and not d.name.startswith(".")
    )
    for ns in final_dirs:
        ldir = archive_dir / ns / "lessons"
        if not ldir.is_dir():
            continue
        for md in sorted(ldir.glob("*.md")):
            errs = validate_strict_frontmatter(md.read_text(encoding="utf-8", errors="replace"))
            if errs:
                remaining_errors.append(f"{md}: {', '.join(errs)}")

    print(f"Final namespaces ({len(final_dirs)}): {', '.join(final_dirs)}")
    print(f"Post-apply strict YAML errors: {len(remaining_errors)}")
    for err in remaining_errors:
        print(f"  ERROR: {err}", file=sys.stderr)
    return 0 if not remaining_errors else 1


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

    p_match = sub.add_parser("match-lessons", help="Match bilingual archive lessons")
    p_match_target = p_match.add_mutually_exclusive_group(required=False)
    p_match_target.add_argument("--slug", default="")
    p_match_target.add_argument("--cwd", default=".")
    p_match.add_argument("--query", required=True)
    p_match.add_argument("--terms", default="")
    p_match.add_argument("--limit", type=int, default=3)
    p_match.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR))

    p_distill = sub.add_parser("distill", help="Save a validated lesson to the archive")
    p_distill.add_argument("--mission", default="")
    p_distill.add_argument("--name", required=True)
    p_distill.add_argument("--description", required=True)
    p_distill.add_argument("--keywords", required=True)
    p_distill.add_argument("--evidence", required=True)
    p_distill_body = p_distill.add_mutually_exclusive_group(required=True)
    p_distill_body.add_argument("--body")
    p_distill_body.add_argument("--body-file")
    p_distill.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR))
    p_distill.add_argument("--ascii-only", action="store_true")

    p_skip = sub.add_parser("skip-distill", help="Record skip decision if no trigger fired")
    p_skip.add_argument("--mission", default="")
    p_skip.add_argument("--reason", required=True)
    p_skip.add_argument("--local-only", action="store_true")

    p_doc = sub.add_parser("doctor-archive", help="Reconcile slugs and repair archive YAML")
    p_doc.add_argument("--archive-dir", default=str(DEFAULT_ARCHIVE_DIR))
    p_doc.add_argument("--scan-repos", default="")
    p_doc.add_argument("--merge", action="append", default=[])
    p_doc.add_argument("--backup-dir", default="")
    p_doc_mode = p_doc.add_mutually_exclusive_group(required=True)
    p_doc_mode.add_argument("--dry-run", action="store_true")
    p_doc_mode.add_argument("--apply", action="store_true")

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
        "match-lessons": lambda: cmd_match_lessons(args),
        "distill": lambda: cmd_distill(args),
        "skip-distill": lambda: cmd_skip_distill(args),
        "doctor-archive": lambda: cmd_doctor_archive(args),
    }
    return dispatch[args.command]()


if __name__ == "__main__":
    # Agents read this CLI through pipes, which a stock Windows Python would
    # encode in the ANSI code page (e.g. cp936) instead of UTF-8.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")
    sys.exit(main())
