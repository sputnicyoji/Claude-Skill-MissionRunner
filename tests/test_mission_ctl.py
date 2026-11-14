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


if __name__ == "__main__":
    unittest.main()
