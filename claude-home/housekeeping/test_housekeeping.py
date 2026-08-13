#!/usr/bin/env python3
"""Tests for the housekeeping cleanup rules.

Run:  python3 claude-home/housekeeping/test_housekeeping.py

Two layers:
  * the pure decision functions, exercised directly;
  * the worktree fact-collection, exercised against real throwaway git
    repositories built in a temporary directory — never against real data.

Every test here is meant to go red when its rule is removed from the script.
A test that stays green while the rule is broken is not a test.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import housekeeping as hk  # noqa: E402


def never_called() -> int:
    raise AssertionError("size must not be computed on this branch")


class JobRules(unittest.TestCase):
    """Spec 5.1 (deletion) and 5.3 (protection) for ~/.claude/jobs."""

    def decide(self, **overrides) -> hk.Verdict:
        args = dict(
            age_days=30.0,
            state="done",
            has_state_file=True,
            live_process=False,
            is_current=False,
            size_getter=lambda: 0,
        )
        args.update(overrides)
        return hk.decide_job(**args)

    def test_current_job_directory_is_never_deleted(self):
        verdict = self.decide(age_days=9999.0, is_current=True)
        self.assertEqual(verdict.action, "keep")

    def test_live_process_protects_regardless_of_age(self):
        verdict = self.decide(age_days=9999.0, state="done", live_process=True)
        self.assertEqual(verdict.action, "keep")

    def test_recently_modified_is_protected(self):
        self.assertEqual(self.decide(age_days=0.5).action, "keep")

    def test_working_state_is_protected(self):
        verdict = self.decide(age_days=10.0, state="working")
        self.assertEqual(verdict.action, "keep")

    def test_missing_state_file_and_fresh_is_protected(self):
        verdict = self.decide(age_days=10.0, state=None, has_state_file=False)
        self.assertEqual(verdict.action, "keep")

    def test_done_and_older_than_fourteen_days_is_deleted(self):
        self.assertEqual(self.decide(age_days=15.0).action, "delete")

    def test_exactly_fourteen_days_is_kept(self):
        """The rule says "older than 14", so 14 itself must survive."""
        self.assertEqual(self.decide(age_days=14.0).action, "keep")

    def test_large_and_older_than_two_days_is_deleted(self):
        verdict = self.decide(age_days=3.0, size_getter=lambda: 2 * 1024**3)
        self.assertEqual(verdict.action, "delete")

    def test_large_but_fresh_is_kept(self):
        verdict = self.decide(age_days=1.0, size_getter=never_called)
        self.assertEqual(verdict.action, "keep")

    def test_blocked_past_the_ceiling_is_deleted(self):
        verdict = self.decide(age_days=101.0, state="blocked")
        self.assertEqual(verdict.action, "delete")

    def test_blocked_below_the_ceiling_is_kept(self):
        verdict = self.decide(age_days=99.0, state="blocked")
        self.assertEqual(verdict.action, "keep")

    def test_exactly_at_the_ceiling_is_still_protected(self):
        """The ceiling is "older than 100", so 100 itself still protects."""
        verdict = self.decide(age_days=100.0, state="blocked")
        self.assertEqual(verdict.action, "keep")

    def test_ceiling_does_not_override_a_live_process(self):
        verdict = self.decide(age_days=101.0, state="blocked", live_process=True)
        self.assertEqual(verdict.action, "keep")

    def test_ceiling_does_not_override_the_current_job(self):
        verdict = self.decide(age_days=101.0, state="working", is_current=True)
        self.assertEqual(verdict.action, "keep")

    def test_size_is_not_computed_for_protected_directories(self):
        """Walking 36k files to confirm a decision already made is waste."""
        self.decide(age_days=0.1, size_getter=never_called)


class WorktreeRules(unittest.TestCase):
    """Spec 5.2 (deletion) and 5.3 (locks) for git worktrees."""

    def decide(self, **overrides) -> hk.Verdict:
        args = dict(
            locked=False,
            lock_pid=None,
            lock_pid_alive=False,
            branch="feature",
            dirty=False,
            ahead=0,
            merged=True,
        )
        args.update(overrides)
        return hk.decide_worktree(**args)

    def test_clean_merged_worktree_is_deleted(self):
        self.assertEqual(self.decide().action, "delete")

    def test_uncommitted_work_is_kept(self):
        self.assertEqual(self.decide(dirty=True).action, "keep")

    def test_unmerged_commits_are_kept(self):
        self.assertEqual(self.decide(ahead=3).action, "keep")

    def test_unmerged_branch_is_kept(self):
        self.assertEqual(self.decide(merged=False).action, "keep")

    def test_live_lock_protects(self):
        verdict = self.decide(locked=True, lock_pid=4242, lock_pid_alive=True)
        self.assertEqual(verdict.action, "keep")
        self.assertFalse(verdict.unlock)

    def test_stale_lock_is_released_and_the_worktree_removed(self):
        verdict = self.decide(locked=True, lock_pid=4242, lock_pid_alive=False)
        self.assertEqual(verdict.action, "delete")
        self.assertTrue(verdict.unlock)

    def test_stale_lock_is_released_but_dirty_worktree_still_kept(self):
        """Releasing a lock is not permission to delete."""
        verdict = self.decide(locked=True, lock_pid=4242, lock_pid_alive=False, dirty=True)
        self.assertEqual(verdict.action, "keep")
        self.assertTrue(verdict.unlock)

    def test_lock_without_a_readable_pid_is_never_touched(self):
        verdict = self.decide(locked=True, lock_pid=None)
        self.assertEqual(verdict.action, "keep")
        self.assertFalse(verdict.unlock)

    def test_detached_head_is_kept(self):
        self.assertEqual(self.decide(branch=None).action, "keep")


class ImageRules(unittest.TestCase):
    """Spec 5.4 for docker images."""

    def test_unused_and_old_is_deleted(self):
        self.assertEqual(hk.decide_image(age_days=101.0, in_use=False).action, "delete")

    def test_unused_but_young_is_kept(self):
        self.assertEqual(hk.decide_image(age_days=99.0, in_use=False).action, "keep")

    def test_exactly_one_hundred_days_is_kept(self):
        """The rule says "older than 100", so 100 itself must survive."""
        self.assertEqual(hk.decide_image(age_days=100.0, in_use=False).action, "keep")

    def test_in_use_is_kept_however_old(self):
        self.assertEqual(hk.decide_image(age_days=9999.0, in_use=True).action, "keep")


class LockParsing(unittest.TestCase):
    def test_pid_is_extracted_from_a_claude_lock_reason(self):
        porcelain = (
            "worktree /repo\nHEAD abc\nbranch refs/heads/master\n\n"
            "worktree /repo/.claude/worktrees/x\nHEAD def\n"
            "branch refs/heads/worktree-x\n"
            "locked claude session do-feature-4qq2-psof (pid 1580358 start 14363310)\n"
        )
        [wt] = hk.parse_worktree_list(Path("/repo"), porcelain)
        self.assertTrue(wt.locked)
        self.assertEqual(wt.lock_pid, 1580358)
        self.assertEqual(wt.branch, "worktree-x")

    def test_bare_lock_without_a_reason_yields_no_pid(self):
        porcelain = (
            "worktree /repo\nHEAD abc\nbranch refs/heads/master\n\n"
            "worktree /repo/wt\nHEAD def\nbranch refs/heads/b\nlocked\n"
        )
        [wt] = hk.parse_worktree_list(Path("/repo"), porcelain)
        self.assertTrue(wt.locked)
        self.assertIsNone(wt.lock_pid)

    def test_the_repository_itself_is_not_listed_as_a_worktree(self):
        porcelain = "worktree /repo\nHEAD abc\nbranch refs/heads/master\n"
        self.assertEqual(hk.parse_worktree_list(Path("/repo"), porcelain), [])


class SizeParsing(unittest.TestCase):
    def test_docker_sizes(self):
        self.assertEqual(hk.parse_human_size("32B"), 32)
        self.assertEqual(hk.parse_human_size("1.5GB"), 1_500_000_000)
        self.assertEqual(hk.parse_human_size("3.139GB*"), 3_139_000_000)
        self.assertEqual(hk.parse_human_size("nonsense"), 0)

    def test_reclaimed_space_in_both_wordings(self):
        """`docker image prune` and `docker buildx prune` word it differently.

        Matching only the first wording made every cache prune report 0B
        freed while it had in fact removed records.
        """
        self.assertEqual(hk.parse_reclaimed("Total reclaimed space: 7.9GB"), 7_900_000_000)
        self.assertEqual(hk.parse_reclaimed("Total:\t1.53GB"), 1_530_000_000)
        self.assertEqual(hk.parse_reclaimed("nothing of the sort"), 0)

    def test_docker_timestamps(self):
        """Both shapes docker emits, including the fractional-second one."""
        images = hk.parse_docker_time("2026-08-09 11:03:22 +0300 +03")
        cache = hk.parse_docker_time("2026-02-10 15:47:56.578713681 +0000 UTC")
        self.assertIsNotNone(images)
        self.assertIsNotNone(cache)
        self.assertLess(cache, images)
        self.assertIsNone(hk.parse_docker_time(""))


def git(repo: Path, *args: str) -> str:
    env = dict(
        os.environ,
        GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
        GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t",
    )
    done = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, check=True
    )
    return done.stdout


class WorktreeFactsOnRealRepositories(unittest.TestCase):
    """The trap from spec 4.3, exercised against actual git repositories.

    An unscoped `git status --short` inside a worktree also reports untracked
    files of the PARENT repository. That made 13 of 23 copies look dirty on
    2026-08-12 while only 10 really were. The check must be scoped to the copy.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "--quiet", "--initial-branch=master")
        (self.repo / "file.txt").write_text("one\n")
        git(self.repo, "add", "file.txt")
        git(self.repo, "commit", "--quiet", "-m", "first")

    def tearDown(self):
        self.tmp.cleanup()

    def add_worktree(self, name: str) -> Path:
        path = self.repo / ".worktrees" / name
        git(self.repo, "worktree", "add", "--quiet", "-b", name, str(path))
        return path

    def evaluate(self, path: Path) -> hk.Verdict:
        porcelain = git(self.repo, "worktree", "list", "--porcelain")
        [wt] = [w for w in hk.parse_worktree_list(self.repo, porcelain) if w.path == path]
        return hk.evaluate_worktree(self.repo, wt, "master")

    def test_clean_merged_worktree_is_removable(self):
        path = self.add_worktree("clean")
        self.assertEqual(self.evaluate(path).action, "delete")

    def test_worktree_with_its_own_uncommitted_file_is_kept(self):
        path = self.add_worktree("dirty")
        (path / "scratch.txt").write_text("unsaved work\n")
        self.assertEqual(self.evaluate(path).action, "keep")

    def test_worktree_with_unmerged_commit_is_kept(self):
        path = self.add_worktree("ahead")
        (path / "new.txt").write_text("two\n")
        git(path, "add", "new.txt")
        git(path, "commit", "--quiet", "-m", "second")
        self.assertEqual(self.evaluate(path).action, "keep")

    def status(self, path: Path, scoped: bool) -> str:
        args = ["git", "-C", str(path), "status", "--short"]
        if scoped:
            args += ["--", "."]
        return subprocess.run(args, capture_output=True, text=True, check=True).stdout

    def test_junk_in_the_parent_does_not_dirty_a_healthy_copy(self):
        path = self.add_worktree("healthy")
        (self.repo / "parent-junk.txt").write_text("belongs to the parent\n")
        self.assertEqual(self.evaluate(path).action, "delete")

    def test_broken_link_leaks_the_parent_and_the_copy_is_kept(self):
        """The trap from spec 4.3, with its actual precondition.

        A healthy worktree is scoped by its own `.git` link. Remove that link
        and git walks up to the PARENT repository instead, reporting the
        parent's untracked files with `../../../` paths — exactly the
        `?? ../../../.beads/` seen on 2026-08-12. Such a copy must be kept:
        whatever git says there describes the parent, not the copy.
        """
        path = self.add_worktree("victim")
        (self.repo / "parent-junk.txt").write_text("belongs to the parent\n")
        (path / ".git").unlink()

        unscoped = self.status(path, scoped=False)
        self.assertIn(
            "parent-junk.txt", unscoped,
            "the trap did not reproduce; this test no longer proves anything",
        )
        self.assertEqual(self.evaluate(path).action, "keep")

    def test_a_copy_answering_for_the_parent_is_kept_even_when_it_reads_clean(self):
        """The dangerous half of the trap.

        With the copy's path ignored by the parent, the scoped status comes
        back empty — "clean" — while describing the parent repository, not the
        copy. Unsaved work inside the copy would be invisible. The only safe
        answer is to refuse to judge it.
        """
        path = self.add_worktree("ignored")
        (self.repo / ".gitignore").write_text(".worktrees/\n")
        git(self.repo, "add", ".gitignore")
        git(self.repo, "commit", "--quiet", "-m", "ignore worktrees")
        (path / "unsaved.txt").write_text("work that must not be lost\n")
        (path / ".git").unlink()

        self.assertEqual(
            self.status(path, scoped=True).strip(), "",
            "the copy no longer reads as clean; this test no longer proves anything",
        )
        self.assertEqual(self.evaluate(path).action, "keep")


if __name__ == "__main__":
    unittest.main(verbosity=2)
