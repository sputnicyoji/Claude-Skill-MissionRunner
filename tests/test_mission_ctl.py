import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "scripts" / "mission_ctl.py"
TEST_PATH = Path(__file__).resolve()


def run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=True,
    )


def init_git_repo(
    path: Path,
    with_commit: bool = True,
    origin_url: str = "",
) -> None:
    path.mkdir(parents=True, exist_ok=True)
    run_git(path, "init")
    run_git(path, "config", "user.email", "test@example.com")
    run_git(path, "config", "user.name", "Test User")
    if origin_url:
        run_git(path, "remote", "add", "origin", origin_url)
    if with_commit:
        (path / "README.md").write_text("hello\n", encoding="utf-8")
        run_git(path, "add", "README.md")
        run_git(path, "commit", "-m", "init")


def run_ctl(*args: str, cwd: Path = None) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(SCRIPT_PATH), *args]
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
    )


class TestMissionCtlCore(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="mctl_test_"))
        self.archive = self.tmp / "archive"
        self.archive.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_sources_are_pure_ascii(self) -> None:
        for path in (TEST_PATH, SCRIPT_PATH):
            self.assertTrue(path.exists(), f"Missing file: {path}")
            content = path.read_text(encoding="utf-8")
            bad = [(i + 1, ch) for i, ch in enumerate(content) if ord(ch) >= 128]
            self.assertEqual(bad, [], f"Non-ASCII chars in {path}: {bad[:5]}")

    def test_slug_resolution_and_worktree_safeguard(self) -> None:
        repo = self.tmp / "My_Project"
        init_git_repo(repo, origin_url="git@github.com:org/fancy-origin.git")

        res = run_ctl("slug", "--cwd", str(repo), "--archive-dir", str(self.archive))
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "fancy-origin")

        # Archive safeguard: if dir_slug/lessons exists and origin_slug/lessons does not, keep dir_slug
        (self.archive / "my-project" / "lessons").mkdir(parents=True)
        res = run_ctl("slug", "--cwd", str(repo), "--archive-dir", str(self.archive))
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "my-project")

        # If origin_slug/lessons also exists, origin_slug wins
        (self.archive / "fancy-origin" / "lessons").mkdir(parents=True)
        res = run_ctl("slug", "--cwd", str(repo), "--archive-dir", str(self.archive))
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "fancy-origin")

        # Worktree inherits main repo resolution and .mission-slug override
        (repo / ".mission-slug").write_text("custom_name\n", encoding="utf-8")
        wt = self.tmp / "wt-feature"
        run_git(repo, "worktree", "add", "-b", "feat/wt", str(wt))
        res = run_ctl("slug", "--cwd", str(wt), "--archive-dir", str(self.archive))
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "custom-name")

        # Non-git dir falls back to normalized directory name
        nongit = self.tmp / "Solo Workspace"
        nongit.mkdir()
        res = run_ctl("slug", "--cwd", str(nongit), "--archive-dir", str(self.archive))
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout.strip(), "solo-workspace")

    def test_init_preserves_index_and_uses_git_info_exclude(self) -> None:
        repo = self.tmp / "app"
        init_git_repo(repo, origin_url="https://github.com/org/app.git")
        (repo / "a.txt").write_text("staged v1\n", encoding="utf-8")
        run_git(repo, "add", "a.txt")
        (repo / "README.md").write_text("dirty unstaged\n", encoding="utf-8")
        (repo / "untracked.txt").write_text("hello\n", encoding="utf-8")

        res = run_ctl(
            "init",
            "--cwd",
            str(repo),
            "--archive-dir",
            str(self.archive),
            "--title",
            "Add Refund Guard",
            "--objective",
            "Ensure refund checks idempotency",
            "--mode",
            "inline",
            "--task",
            "Implement guard",
            "--criteria",
            "All tests pass",
        )
        self.assertEqual(res.returncode, 0, res.stderr)

        # User staged/unstaged index state must remain untouched
        cached = run_git(repo, "diff", "--cached", "--name-only").stdout.strip().splitlines()
        self.assertEqual(cached, ["a.txt"])
        unstaged = run_git(repo, "diff", "--name-only").stdout.strip().splitlines()
        self.assertEqual(unstaged, ["README.md"])

        # _planning/ must be ignored via .git/info/exclude and invisible to git status
        status = run_git(repo, "status", "--short").stdout
        self.assertNotIn("_planning", status)
        exclude_text = (repo / ".git" / "info" / "exclude").read_text(encoding="utf-8")
        self.assertIn("_planning/", exclude_text)

        # Collision creates -2 folder
        res2 = run_ctl(
            "init",
            "--cwd",
            str(repo),
            "--archive-dir",
            str(self.archive),
            "--title",
            "Add Refund Guard",
            "--objective",
            "Second run",
        )
        self.assertEqual(res2.returncode, 0, res2.stderr)
        planning_dirs = sorted(p.name for p in (repo / "_planning").iterdir() if p.is_dir())
        self.assertEqual(len(planning_dirs), 2)
        self.assertTrue(planning_dirs[1].endswith("-2"))

    def test_init_works_on_unborn_head(self) -> None:
        repo = self.tmp / "fresh"
        init_git_repo(repo, with_commit=False)
        res = run_ctl(
            "init",
            "--cwd",
            str(repo),
            "--archive-dir",
            str(self.archive),
            "--title",
            "Bootstrap",
            "--objective",
            "Initial setup",
            "--task",
            "Create src file",
            "--criteria",
            "File exists",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        mission_dirs = list((repo / "_planning").iterdir())
        self.assertEqual(len(mission_dirs), 1)
        plan = (mission_dirs[0] / "plan.md").read_text(encoding="utf-8")
        self.assertIn("UNBORN", plan)

    def test_task_done_gates_and_diff_and_audit(self) -> None:
        repo = self.tmp / "svc"
        init_git_repo(repo, origin_url="https://github.com/org/svc.git")

        res = run_ctl(
            "init",
            "--cwd",
            str(repo),
            "--archive-dir",
            str(self.archive),
            "--title",
            "Fix Counter",
            "--objective",
            "Increment safely",
            "--mode",
            "inline",
            "--task",
            "Update counter module",
            "--task",
            "Verify unchanged docs",
            "--criteria",
            "Unit suite passes",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        mission_dir = next((repo / "_planning").iterdir())
        plan_path = mission_dir / "plan.md"

        # 1. Start T1
        self.assertEqual(
            run_ctl("task-start", "T1", "--mission", str(mission_dir)).returncode,
            0,
        )

        # 2. Failing command must reject task-done and preserve [ ]
        fail_res = run_ctl(
            "task-done",
            "T1",
            "--mission",
            str(mission_dir),
            "--",
            sys.executable,
            "-c",
            "import sys; print('boom'); sys.exit(3)",
        )
        self.assertEqual(fail_res.returncode, 3)
        self.assertIn("- [ ] **T1**:", plan_path.read_text(encoding="utf-8"))

        # 3. Passing command with NO file edits must fail with exit 2 unless --verify-only
        noop_res = run_ctl(
            "task-done",
            "T1",
            "--mission",
            str(mission_dir),
            "--",
            sys.executable,
            "-c",
            "print('ok')",
        )
        self.assertEqual(noop_res.returncode, 2)
        self.assertIn("- [ ] **T1**:", plan_path.read_text(encoding="utf-8"))

        # 4. Edit file and succeed
        (repo / "counter.py").write_text("VALUE = 1\n", encoding="utf-8")
        pass_res = run_ctl(
            "task-done",
            "T1",
            "--mission",
            str(mission_dir),
            "--",
            sys.executable,
            "-c",
            "print('passed 1 test')",
        )
        self.assertEqual(pass_res.returncode, 0, pass_res.stderr)
        self.assertIn("- [x] **T1**:", plan_path.read_text(encoding="utf-8"))
        self.assertTrue((mission_dir / "logs" / "task-T1.log").exists())

        # 5. Anti-cheating check: T2 without edits fails unless --verify-only
        noop_t2 = run_ctl(
            "task-done",
            "T2",
            "--mission",
            str(mission_dir),
            "--",
            sys.executable,
            "-c",
            "print('still clean')",
        )
        self.assertEqual(noop_t2.returncode, 2)

        # Complete T2 with --verify-only
        ok_t2 = run_ctl(
            "task-done",
            "T2",
            "--mission",
            str(mission_dir),
            "--verify-only",
            "--",
            sys.executable,
            "-c",
            "print('verified')",
        )
        self.assertEqual(ok_t2.returncode, 0, ok_t2.stderr)
        self.assertIn("- [x] **T2**:", plan_path.read_text(encoding="utf-8"))

        # 6. Diff check shows counter.py
        diff_stat = run_ctl("diff", "--mission", str(mission_dir), "--stat")
        self.assertEqual(diff_stat.returncode, 0, diff_stat.stderr)
        self.assertIn("counter.py", diff_stat.stdout)

        # 7. Audit fails until criteria, review pass, and distill/skip_distill exist
        audit_early = run_ctl("audit", "--mission", str(mission_dir))
        self.assertNotEqual(audit_early.returncode, 0)

        # Ruling + criteria + revise review -> still fails audit
        self.assertEqual(
            run_ctl(
                "ruling",
                "--mission",
                str(mission_dir),
                "--decision",
                "Use int constant",
                "--why",
                "Simple single value",
                "--cost",
                "Trivial to change",
            ).returncode,
            0,
        )
        self.assertEqual(
            run_ctl("check-criteria", "--mission", str(mission_dir), "--all").returncode,
            0,
        )
        self.assertEqual(
            run_ctl(
                "review-result",
                "--mission",
                str(mission_dir),
                "--verdict",
                "revise",
                "--summary",
                "Add type hint",
            ).returncode,
            0,
        )
        self.assertNotEqual(
            run_ctl("audit", "--mission", str(mission_dir)).returncode,
            0,
        )

        # Pass review
        self.assertEqual(
            run_ctl(
                "review-result",
                "--mission",
                str(mission_dir),
                "--verdict",
                "pass",
                "--summary",
                "Looks clean",
            ).returncode,
            0,
        )

        # Tamper test: simulate manual [x] T3 without task_done event -> audit must fail
        plan_text = plan_path.read_text(encoding="utf-8").replace(
            "- [x] **T2**: Verify unchanged docs",
            "- [x] **T2**: Verify unchanged docs\n- [x] **T3**: Cheated task",
        )
        plan_path.write_text(plan_text, encoding="utf-8")
        events_path = mission_dir / "logs" / ".events.jsonl"
        with events_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"event": "skip_distill", "reason": "test"}) + "\n")
        audit_cheat = run_ctl("audit", "--mission", str(mission_dir))
        self.assertNotEqual(audit_cheat.returncode, 0)

        # Restore plan without T3 -> audit succeeds and deletes logs/
        plan_path.write_text(
            plan_text.replace("\n- [x] **T3**: Cheated task", ""),
            encoding="utf-8",
        )
        audit_ok = run_ctl("audit", "--mission", str(mission_dir))
        self.assertEqual(audit_ok.returncode, 0, audit_ok.stdout + audit_ok.stderr)
        self.assertFalse((mission_dir / "logs").exists())
        final_plan = plan_path.read_text(encoding="utf-8")
        self.assertIn("Status: `completed`", final_plan)
        self.assertIn("- [Audit] pass", final_plan)

    def test_written_files_use_lf_line_endings(self) -> None:
        # Text-mode writes translate "\n" to os.linesep, which made every
        # generated file CRLF on Windows. Each writer must emit LF on any OS.
        repo = self.tmp / "eol"
        init_git_repo(repo, origin_url="https://github.com/org/eol.git")
        res = run_ctl(
            "init",
            "--cwd",
            str(repo),
            "--archive-dir",
            str(self.archive),
            "--title",
            "Line Endings",
            "--objective",
            "Keep generated files LF",
            "--task",
            "Touch a file",
            "--criteria",
            "Only LF bytes",
        )
        self.assertEqual(res.returncode, 0, res.stderr)
        mission_dir = next((repo / "_planning").iterdir())

        self.assertEqual(
            run_ctl("task-start", "T1", "--mission", str(mission_dir)).returncode,
            0,
        )
        (repo / "touched.txt").write_text("x\n", encoding="utf-8")
        done = run_ctl(
            "task-done",
            "T1",
            "--mission",
            str(mission_dir),
            "--",
            sys.executable,
            "-c",
            "print('line 1'); print('line 2')",
        )
        self.assertEqual(done.returncode, 0, done.stderr)

        distilled = run_ctl(
            "distill",
            "--mission",
            str(mission_dir),
            "--archive-dir",
            str(self.archive),
            "--name",
            "lf-line-endings",
            "--description",
            "Write LF line endings on every OS",
            "--keywords",
            "newline, crlf, \u6362\u884c",
            "--evidence",
            "task-T1 log",
            "--body",
            "Open text files for writing with an explicit newline argument so Windows does not translate LF into CRLF.",
        )
        self.assertEqual(distilled.returncode, 0, distilled.stderr)

        written = [
            mission_dir / "plan.md",
            mission_dir / "logs" / ".events.jsonl",
            mission_dir / "logs" / "task-T1.log",
            Path(distilled.stdout.strip()),
        ]
        # init skips the exclude entry when a global ignore already covers _planning/.
        exclude = repo / ".git" / "info" / "exclude"
        if b"_planning/" in exclude.read_bytes():
            written.append(exclude)
        for path in written:
            self.assertNotIn(b"\r", path.read_bytes(), str(path))


class TestMissionCtlArchiveAndBilingual(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="mctl_arch_"))
        self.archive = self.tmp / "archive"
        self.archive.mkdir(parents=True, exist_ok=True)
        self.repo = self.tmp / "sample-app"
        init_git_repo(self.repo, origin_url="https://github.com/org/sample-app.git")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_lesson(self, ns: str, filename: str, raw: str) -> Path:
        lessons_dir = self.archive / ns / "lessons"
        lessons_dir.mkdir(parents=True, exist_ok=True)
        p = lessons_dir / filename
        p.write_text(raw, encoding="utf-8")
        return p

    def test_match_lessons_stopword_rejection_word_boundary_and_cjk_bigrams(self) -> None:
        self._write_lesson(
            "sample-app",
            "2026-07-01-token-integrity.md",
            '---\n'
            'name: "token-integrity"\n'
            'description: "Verify token format in storage layer"\n'
            'keywords: ["token", "format", "storage"]\n'
            'mission_date: "2026-07-01"\n'
            '---\n\n'
            '# Lesson: token-integrity\n\n'
            '**Lesson:** Check token length before writing.\n',
        )
        self._write_lesson(
            "sample-app",
            "2026-07-02-refund-idempotency.md",
            '---\n'
            'name: "refund-idempotency"\n'
            'description: "\u9000\u6b3e\u5e42\u7b49\u6821\u9a8c\u5fc5\u987b\u9501\u8ba2\u5355"\n'
            'keywords: ["refund", "idempotency", "\u9000\u6b3e", "\u5e42\u7b49"]\n'
            'mission_date: "2026-07-02"\n'
            '---\n\n'
            '# Lesson: refund-idempotency\n\n'
            '**Lesson:** Use an idempotency key for refunds.\n',
        )

        # 1. Pure stopwords or substring traps ('in' vs 'integrity', 'to' vs 'token') return 0 matches
        res_noise = run_ctl(
            "match-lessons",
            "--cwd",
            str(self.repo),
            "--archive-dir",
            str(self.archive),
            "--query",
            "add a new file in the code to fix for and with",
        )
        self.assertEqual(res_noise.returncode, 0, res_noise.stderr)
        self.assertEqual(res_noise.stdout.strip(), "")

        # 2. Word boundary: 'form' must NOT match keyword 'format'; 'for' must NOT match 'format'
        res_sub = run_ctl(
            "match-lessons",
            "--cwd",
            str(self.repo),
            "--archive-dir",
            str(self.archive),
            "--query",
            "update form validation logic",
        )
        self.assertEqual(res_sub.returncode, 0, res_sub.stderr)
        self.assertNotIn("token-integrity", res_sub.stdout)

        # 3. CJK bigram query matches CJK lesson and populates init pointers
        res_cjk = run_ctl(
            "match-lessons",
            "--cwd",
            str(self.repo),
            "--archive-dir",
            str(self.archive),
            "--query",
            "\u4fee\u590d\u8ba2\u5355\u9000\u6b3e\u5e42\u7b49\u95ee\u9898",
        )
        self.assertEqual(res_cjk.returncode, 0, res_cjk.stderr)
        self.assertIn("refund-idempotency", res_cjk.stdout)

        # 4. init automatically integrates matched lessons into plan.md
        res_init = run_ctl(
            "init",
            "--cwd",
            str(self.repo),
            "--archive-dir",
            str(self.archive),
            "--title",
            "Fix Refund",
            "--objective",
            "\u9000\u6b3e\u5e42\u7b49\u4fee\u590d",
        )
        self.assertEqual(res_init.returncode, 0, res_init.stderr)
        self.assertIn("refund-idempotency", res_init.stdout)

    def test_distill_validation_and_skip_trigger_gate(self) -> None:
        res_init = run_ctl(
            "init",
            "--cwd",
            str(self.repo),
            "--archive-dir",
            str(self.archive),
            "--title",
            "Auth Fix",
            "--objective",
            "Fix session timeout",
            "--task",
            "Patch session code",
            "--criteria",
            "Tests pass",
        )
        self.assertEqual(res_init.returncode, 0, res_init.stderr)
        mission_dir = next((self.repo / "_planning").iterdir())

        # Clean run without failures -> skip-distill succeeds
        res_clean = run_ctl(
            "init",
            "--cwd",
            str(self.repo),
            "--archive-dir",
            str(self.archive),
            "--title",
            "Clean Task",
            "--objective",
            "Simple edit",
        )
        self.assertEqual(res_clean.returncode, 0)
        clean_dir = Path(res_clean.stdout.splitlines()[0].strip())
        self.assertEqual(
            run_ctl(
                "skip-distill",
                "--mission",
                str(clean_dir),
                "--reason",
                "Routine typo fix with zero blockers",
            ).returncode,
            0,
        )

        # Fail T1 once to trip distillation trigger
        run_ctl(
            "task-done",
            "T1",
            "--mission",
            str(mission_dir),
            "--",
            sys.executable,
            "-c",
            "import sys; sys.exit(1)",
        )
        # skip-distill without --local-only must fail with exit 2
        res_block = run_ctl(
            "skip-distill",
            "--mission",
            str(mission_dir),
            "--reason",
            "Want to skip",
        )
        self.assertEqual(res_block.returncode, 2)

        # Distill rejects missing CJK keyword unless --ascii-only
        res_no_cjk = run_ctl(
            "distill",
            "--mission",
            str(mission_dir),
            "--archive-dir",
            str(self.archive),
            "--name",
            "session-timeout",
            "--description",
            "Set explicit timeout",
            "--keywords",
            "session, timeout",
            "--evidence",
            "task-T1 failure then pass",
            "--body",
            "Always configure explicit timeout values on network clients so idle sockets fail fast cleanly.",
        )
        self.assertEqual(res_no_cjk.returncode, 2)

        # Distill rejects overly short body (< 10 units)
        res_short = run_ctl(
            "distill",
            "--mission",
            str(mission_dir),
            "--archive-dir",
            str(self.archive),
            "--name",
            "session-timeout",
            "--description",
            "Set timeout",
            "--keywords",
            "session, timeout, \u8d85\u65f6",
            "--evidence",
            "task-T1 log",
            "--body",
            "Too short.",
        )
        self.assertEqual(res_short.returncode, 2)

        # Distill succeeds with bilingual keywords, valid length, and colon-safe YAML
        res_ok = run_ctl(
            "distill",
            "--mission",
            str(mission_dir),
            "--archive-dir",
            str(self.archive),
            "--name",
            "session-timeout",
            "--description",
            "Timeout rule: always configure socket read timeout",
            "--keywords",
            "session, timeout, \u4f1a\u8bdd, \u8d85\u65f6",
            "--evidence",
            "task-T1 exit=1 before explicit timeout fix",
            "--body",
            "Client calls hang indefinitely when timeout is omitted: always pass an explicit connect and read timeout.",
        )
        self.assertEqual(res_ok.returncode, 0, res_ok.stderr)
        lesson_file = Path(res_ok.stdout.strip())
        self.assertTrue(lesson_file.is_file())
        content = lesson_file.read_text(encoding="utf-8")
        self.assertIn("**Evidence:** task-T1 exit=1", content)
        self.assertIn('keywords: ["session", "timeout",', content)

    def test_doctor_archive_merges_and_repairs_yaml_preserving_single_slug(self) -> None:
        repos_dir = self.tmp / "repos"
        # Repo A: dir 'alpha', remote 'alpha-service', BOTH exist in archive -> merge alpha -> alpha-service
        init_git_repo(repos_dir / "Alpha", origin_url="git@github.com:org/Alpha-Service.git")
        # Repo B: dir 'Beta', remote 'remote_beta_app', ONLY 'beta' exists in archive -> preserve 'beta'
        init_git_repo(repos_dir / "Beta", origin_url="git@github.com:org/remote_beta_app.git")
        # Non-kebab namespace Gamma_Client -> normalize to gamma-client

        self._write_lesson(
            "alpha",
            "2026-06-01-scalar-kw.md",
            "---\n"
            "name: scalar-kw\n"
            "description: Broken: unquoted colon and `backtick` scalar\n"
            "keywords: replay, cli, \u56de\u653e\n"
            "metadata:\n"
            "  mission_date: 2026-06-01\n"
            "---\n\n"
            "# Lesson: scalar-kw\n\n"
            "**Lesson:** Exact verbatim body line 1.\n"
            "Exact verbatim body line 2.\n",
        )
        self._write_lesson(
            "alpha-service",
            "2026-06-05-clean.md",
            '---\n'
            'name: "clean"\n'
            'description: "Clean lesson"\n'
            'keywords: ["clean", "service"]\n'
            'mission_date: "2026-06-05"\n'
            '---\n\n'
            '# Lesson: clean\n\n'
            '**Lesson:** Keep this body untouched.\n',
        )
        self._write_lesson(
            "Gamma_Client",
            "2026-06-02-gamma-tip.md",
            "---\n"
            "name: gamma-tip\n"
            "description: `leading backtick tip`\n"
            "keywords: build, rust\n"
            "mission_date: 2026-06-02\n"
            "---\n\n"
            "**Lesson:** Gamma body preserved.\n",
        )
        self._write_lesson(
            "beta",
            "2026-06-03-beta-rule.md",
            '---\n'
            'name: "beta-rule"\n'
            'description: "Beta invariant"\n'
            'keywords: ["beta", "grid"]\n'
            'mission_date: "2026-06-03"\n'
            '---\n\n'
            '**Lesson:** Beta stays under beta namespace.\n',
        )

        # Dry run leaves archive untouched
        dry = run_ctl(
            "doctor-archive",
            "--archive-dir",
            str(self.archive),
            "--scan-repos",
            str(repos_dir),
            "--dry-run",
        )
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertIn("alpha -> alpha-service", dry.stdout)
        self.assertIn("Gamma_Client -> gamma-client", dry.stdout)
        self.assertNotIn("beta ->", dry.stdout)
        self.assertTrue((self.archive / "alpha").exists())

        # Apply with backup
        backup = self.tmp / "archive-backup"
        app = run_ctl(
            "doctor-archive",
            "--archive-dir",
            str(self.archive),
            "--scan-repos",
            str(repos_dir),
            "--backup-dir",
            str(backup),
            "--apply",
        )
        self.assertEqual(app.returncode, 0, app.stdout + app.stderr)
        self.assertTrue((backup / "alpha" / "lessons" / "2026-06-01-scalar-kw.md").is_file())
        self.assertFalse((self.archive / "alpha").exists())
        self.assertFalse((self.archive / "Gamma_Client").exists())
        self.assertTrue((self.archive / "beta" / "lessons" / "2026-06-03-beta-rule.md").is_file())
        self.assertTrue((self.archive / "gamma-client" / "lessons" / "2026-06-02-gamma-tip.md").is_file())

        merged = (self.archive / "alpha-service" / "lessons" / "2026-06-01-scalar-kw.md").read_text(
            encoding="utf-8"
        )
        self.assertIn('keywords: ["replay", "cli", "\u56de\u653e"]', merged)
        self.assertIn('mission_date: "2026-06-01"', merged)
        self.assertIn("Exact verbatim body line 1.\nExact verbatim body line 2.", merged)

        # Repaired archive matches CJK query on alpha-service
        res_match = run_ctl(
            "match-lessons",
            "--cwd",
            str(repos_dir / "Alpha"),
            "--archive-dir",
            str(self.archive),
            "--query",
            "\u56de\u653e",
        )
        self.assertEqual(res_match.returncode, 0, res_match.stderr)
        self.assertIn("scalar-kw", res_match.stdout)


if __name__ == "__main__":
    unittest.main()
