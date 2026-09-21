#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# VeRO Candidate Repository & Git Worktree Manager

from __future__ import annotations
from dataclasses import dataclass, field
import json
import logging
import os
import shutil
import subprocess
from typing import Dict, List, Optional

logger = logging.getLogger("vero.candidate_repo")

@dataclass
class Candidate:
    candidate_id: str
    branch_name: str
    worktree_path: str
    base_commit: str
    candidate_commit: Optional[str] = None
    status: str = "initialized"  # "initialized", "evaluated", "selected", "rejected"
    metadata: Dict[str, any] = field(default_factory=dict)

class CandidateRepository:
    """Manages Git-versioned candidate artifacts and isolated worktrees for zero-pollution experiments."""

    def __init__(self, repo_root: str, worktrees_dir: Optional[str] = None):
        self.repo_root = os.path.abspath(repo_root)
        self.worktrees_dir = os.path.abspath(worktrees_dir or os.path.join(self.repo_root, ".vero_worktrees"))
        os.makedirs(self.worktrees_dir, exist_ok=True)
        self.candidates: Dict[str, Candidate] = {}

    def _run_git(self, args: List[str], cwd: Optional[str] = None) -> str:
        res = subprocess.run(
            ["git"] + args,
            cwd=cwd or self.repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()

    def get_current_commit(self) -> str:
        return self._run_git(["rev-parse", "HEAD"])

    def create_candidate_worktree(self, candidate_id: str) -> Candidate:
        """Creates an isolated git worktree branch for the candidate."""
        base_commit = self.get_current_commit()
        branch_name = f"vero/candidate-{candidate_id}"
        worktree_path = os.path.join(self.worktrees_dir, candidate_id)

        if os.path.exists(worktree_path):
            self.cleanup_worktree(candidate_id)

        # Create branch from current base and check out in worktree
        self._run_git(["worktree", "add", "-b", branch_name, worktree_path, base_commit])
        logger.info("Created isolated worktree for candidate %s at %s", candidate_id, worktree_path)

        candidate = Candidate(
            candidate_id=candidate_id,
            branch_name=branch_name,
            worktree_path=worktree_path,
            base_commit=base_commit,
        )
        self.candidates[candidate_id] = candidate
        return candidate

    def commit_candidate(self, candidate_id: str, message: str) -> str:
        """Stages all changes in the candidate worktree and commits them."""
        cand = self.candidates.get(candidate_id)
        if not cand:
            raise ValueError(f"Candidate {candidate_id} not found")

        self._run_git(["add", "-A"], cwd=cand.worktree_path)
        commit_hash = self._run_git(
            ["-c", "user.name=VeRO Optimizer", "-c", "user.email=vero@localhost", "commit", "-m", message],
            cwd=cand.worktree_path,
        )
        head_commit = self._run_git(["rev-parse", "HEAD"], cwd=cand.worktree_path)
        cand.candidate_commit = head_commit
        cand.status = "committed"
        return head_commit

    def select_candidate(self, candidate_id: str) -> None:
        """Selects a winning candidate and merges its changes into the main repo."""
        cand = self.candidates.get(candidate_id)
        if not cand or not cand.candidate_commit:
            raise ValueError(f"Candidate {candidate_id} has no valid commit to select")

        # Fast-forward or merge candidate commit to repo root
        self._run_git(["merge", "--ff-only", cand.candidate_commit])
        cand.status = "selected"
        logger.info("Candidate %s SELECTED and merged to main repository", candidate_id)
        self.cleanup_worktree(candidate_id)

    def cleanup_worktree(self, candidate_id: str) -> None:
        """Removes the worktree and deletes the ephemeral branch if rejected."""
        cand = self.candidates.get(candidate_id)
        path = os.path.join(self.worktrees_dir, candidate_id)

        try:
            self._run_git(["worktree", "remove", "--force", path])
        except Exception:
            if os.path.exists(path):
                shutil.rmtree(path, ignore_errors=True)

        if cand and cand.status != "selected":
            try:
                self._run_git(["branch", "-D", cand.branch_name])
            except Exception:
                pass
            cand.status = "rejected"
            logger.info("Candidate %s REJECTED; worktree and branch cleaned up", candidate_id)
