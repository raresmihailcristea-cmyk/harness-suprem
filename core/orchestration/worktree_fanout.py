# Copyright 2026 Scion Frontiers & Antigravity - Rareș Cristea
# Parallel Worktree Fan-Out Orchestration Engine
# Inspired by stablyai/orca (https://github.com/stablyai/orca)

from __future__ import annotations
import concurrent.futures
from dataclasses import dataclass, field
import json
import logging
import os
import shutil
import subprocess
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger("supreme.fanout")

@dataclass
class FanoutAgentConfig:
    agent_id: str
    name: str
    engine: str = "mlx"  # "mlx", "llama_cpp", "custom"
    system_prompt_override: Optional[str] = None
    temperature: float = 0.2

@dataclass
class FanoutCandidateResult:
    agent_id: str
    agent_name: str
    branch_name: str
    worktree_path: str
    base_commit: str
    commit_hash: Optional[str] = None
    diff: str = ""
    tests_passed: bool = False
    tests_output: str = ""
    score: float = 0.0
    latency_sec: float = 0.0
    status: str = "initialized"  # "initialized", "running", "evaluated", "winner", "rejected"
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "branch_name": self.branch_name,
            "worktree_path": self.worktree_path,
            "commit_hash": self.commit_hash,
            "tests_passed": self.tests_passed,
            "score": round(self.score, 2),
            "latency_sec": round(self.latency_sec, 2),
            "status": self.status,
            "error": self.error,
            "diff_summary": f"{len(self.diff.splitlines())} lines changed" if self.diff else "No changes"
        }

class WorktreeFanoutManager:
    """
    Orca-style Parallel Worktree Fan-Out Orchestrator.
    Dispatches a prompt across multiple independent agent candidates in parallel,
    each running inside its own isolated Git worktree, verifies test results,
    ranks the diffs, and merges the winning solution.
    """

    WORKTREES_DIR_NAME = ".harness_worktrees"

    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        self.worktrees_dir = os.path.join(self.repo_root, self.WORKTREES_DIR_NAME)
        os.makedirs(self.worktrees_dir, exist_ok=True)
        self.results: Dict[str, FanoutCandidateResult] = {}

    def _run_git(self, args: List[str], cwd: Optional[str] = None) -> str:
        res = subprocess.run(
            ["git"] + args,
            cwd=cwd or self.repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip()

    def get_current_commit(self) -> str:
        return self._run_git(["rev-parse", "HEAD"])

    def create_worktree(self, agent_id: str) -> Tuple[str, str]:
        """Creates an isolated git worktree branch for a candidate agent."""
        base_commit = self.get_current_commit()
        branch_name = f"fanout/{agent_id}"
        worktree_path = os.path.join(self.worktrees_dir, agent_id)

        # Cleanup existing worktree if present
        if os.path.exists(worktree_path):
            self.remove_worktree(agent_id, branch_name)

        self._run_git(["worktree", "add", "-b", branch_name, worktree_path, base_commit])
        logger.info(f"[Fanout] Created isolated worktree for agent {agent_id} at {worktree_path}")
        return branch_name, worktree_path

    def remove_worktree(self, agent_id: str, branch_name: Optional[str] = None) -> None:
        """Safely tears down the worktree and deletes the ephemeral branch."""
        worktree_path = os.path.join(self.worktrees_dir, agent_id)
        branch = branch_name or f"fanout/{agent_id}"

        try:
            self._run_git(["worktree", "remove", "--force", worktree_path])
        except Exception:
            if os.path.exists(worktree_path):
                shutil.rmtree(worktree_path, ignore_errors=True)
            self._run_git(["worktree", "prune"])

        try:
            self._run_git(["branch", "-D", branch])
        except Exception:
            pass

    def execute_candidate(
        self,
        agent: FanoutAgentConfig,
        task_fn: Callable[[str, FanoutAgentConfig], None],
        test_command: Optional[str] = None
    ) -> FanoutCandidateResult:
        """
        Executes a single candidate agent in its worktree, runs test suite,
        calculates diff and evaluation score.
        """
        start_time = time.time()
        base_commit = self.get_current_commit()
        branch_name, worktree_path = self.create_worktree(agent.agent_id)

        result = FanoutCandidateResult(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            branch_name=branch_name,
            worktree_path=worktree_path,
            base_commit=base_commit,
            status="running"
        )

        try:
            # 1. Execute task mutation function inside worktree
            task_fn(worktree_path, agent)

            # 2. Stage and commit changes
            self._run_git(["add", "-A"], cwd=worktree_path)
            status_output = self._run_git(["status", "--porcelain"], cwd=worktree_path)

            if status_output.strip():
                self._run_git(
                    ["-c", "user.name=Fanout Agent", "-c", "user.email=fanout@harness.local",
                     "commit", "-m", f"Fanout solution by {agent.name} ({agent.engine})"],
                    cwd=worktree_path
                )
                commit_hash = self._run_git(["rev-parse", "HEAD"], cwd=worktree_path)
                result.commit_hash = commit_hash
                result.diff = self._run_git(["diff", f"{base_commit}..HEAD"], cwd=worktree_path)
            else:
                result.diff = ""
                result.commit_hash = base_commit

            # 3. Run verification test command if provided
            tests_passed = True
            test_out = "No test command specified"
            if test_command:
                test_proc = subprocess.run(
                    test_command,
                    shell=True,
                    cwd=worktree_path,
                    capture_output=True,
                    text=True
                )
                tests_passed = (test_proc.returncode == 0)
                test_out = test_proc.stdout + "\n" + test_proc.stderr

            result.tests_passed = tests_passed
            result.tests_output = test_out

            # 4. Compute evaluation score
            # Base 100 for passing tests, penalized by latency and excessive diff size
            elapsed = time.time() - start_time
            result.latency_sec = elapsed

            if tests_passed:
                base_score = 100.0
                latency_penalty = min(20.0, elapsed * 2.0)
                score = max(50.0, base_score - latency_penalty)
            else:
                score = 0.0

            result.score = score
            result.status = "evaluated"

        except Exception as e:
            logger.error(f"[Fanout] Error in candidate {agent.agent_id}: {e}")
            result.error = str(e)
            result.status = "error"
            result.score = 0.0
            result.latency_sec = time.time() - start_time

        self.results[agent.agent_id] = result
        return result

    def dispatch_parallel(
        self,
        agents: List[FanoutAgentConfig],
        task_fn: Callable[[str, FanoutAgentConfig], None],
        test_command: Optional[str] = None,
        max_workers: int = 4
    ) -> List[FanoutCandidateResult]:
        """
        Dispatches all candidate agents in parallel across separate worktrees.
        """
        logger.info(f"[Fanout] Launching parallel fanout across {len(agents)} agents...")
        futures = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            for ag in agents:
                f = executor.submit(self.execute_candidate, ag, task_fn, test_command)
                futures[f] = ag.agent_id

            results = []
            for f in concurrent.futures.as_completed(futures):
                res = f.result()
                results.append(res)

        # Sort results by score descending, then latency ascending
        results.sort(key=lambda r: (r.score, -r.latency_sec), reverse=True)
        return results

    def select_and_merge_winner(self, winner_agent_id: str, cleanup_others: bool = True) -> bool:
        """
        Merges the selected winning candidate into the base repository
        and cleans up the ephemeral worktrees.
        """
        winner = self.results.get(winner_agent_id)
        if not winner or not winner.commit_hash:
            raise ValueError(f"Winner candidate {winner_agent_id} not found or has no commit.")

        # Merge winner into main repo
        logger.info(f"[Fanout] Merging winning candidate {winner.agent_name} ({winner.commit_hash}) into base repo...")
        self._run_git(["merge", "--ff-only", winner.commit_hash])
        winner.status = "winner"

        if cleanup_others:
            for ag_id, res in list(self.results.items()):
                self.remove_worktree(ag_id, res.branch_name)

        return True

    def cleanup_all(self) -> None:
        """Cleans up all worktrees and prunes git references."""
        if os.path.exists(self.worktrees_dir):
            for entry in os.listdir(self.worktrees_dir):
                self.remove_worktree(entry)
        self._run_git(["worktree", "prune"])
