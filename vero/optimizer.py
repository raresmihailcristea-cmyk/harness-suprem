#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# VeRO Recursive Optimizer (Hill-Climbing Search Loop)

from __future__ import annotations
from dataclasses import dataclass
import json
import logging
import os
import time
from typing import Callable, Dict, List, Optional

from .gateway import InferenceGateway, BudgetExceededError
from .candidate_repo import CandidateRepository, Candidate
from .evaluator import TrustedEvaluator, EvaluationResult, ParetoMetrics

logger = logging.getLogger("vero.optimizer")

@dataclass
class OptimizationRound:
    round_idx: int
    candidate_id: str
    action: str  # "selected" or "rejected"
    old_score: float
    new_score: float
    metrics: ParetoMetrics
    commit_hash: Optional[str] = None

class RecursiveOptimizer:
    """Orchestrates the Version -> Evaluate -> Select (Hill-Climbing) loop across agent iterations."""

    def __init__(
        self,
        repo: CandidateRepository,
        evaluator: TrustedEvaluator,
        gateway: Optional[InferenceGateway] = None,
        max_iterations: int = 10,
    ):
        self.repo = repo
        self.evaluator = evaluator
        self.gateway = gateway or InferenceGateway()
        self.max_iterations = max_iterations
        self.history: List[OptimizationRound] = []
        self.best_score: float = float("-inf")
        self.best_candidate_id: Optional[str] = None

    def run_optimization_loop(
        self,
        test_command: List[str],
        propose_candidate_fn: Callable[[Candidate, int, Optional[EvaluationResult]], None],
        initial_baseline_name: str = "baseline",
    ) -> Dict[str, any]:
        """Executes the hill-climbing optimization process."""
        logger.info("Starting VeRO optimization loop (max %d iterations)", self.max_iterations)

        # 1. Score initial baseline
        baseline_res = self.evaluator.evaluate_command(
            candidate_id=initial_baseline_name,
            test_command=test_command,
            cwd=self.repo.repo_root,
        )
        self.best_score = baseline_res.pareto_score
        self.best_candidate_id = initial_baseline_name
        logger.info("Baseline score: %.2f (Accuracy: %.1f%%, Latency: %.1fms)",
                    baseline_res.pareto_score, baseline_res.metrics.accuracy * 100, baseline_res.metrics.latency_ms)

        prev_result: Optional[EvaluationResult] = baseline_res

        # 2. Iterate hill-climbing
        for i in range(1, self.max_iterations + 1):
            candidate_id = f"iter-{i:03d}"
            logger.info("--- [VeRO Round %d/%d] Creating Candidate: %s ---", i, self.max_iterations, candidate_id)

            # Create isolated worktree
            cand = self.repo.create_candidate_worktree(candidate_id)

            try:
                # Agent proposes changes in the candidate worktree
                propose_candidate_fn(cand, i, prev_result)

                # Commit changes
                commit_hash = self.repo.commit_candidate(candidate_id, f"VeRO auto-optimized candidate {candidate_id}")

                # Evaluate candidate
                eval_res = self.evaluator.evaluate_command(
                    candidate_id=candidate_id,
                    test_command=test_command,
                    cwd=cand.worktree_path,
                )
                prev_result = eval_res

                logger.info("Candidate %s Score: %.2f (vs Best: %.2f)",
                            candidate_id, eval_res.pareto_score, self.best_score)

                # Hill-climbing decision
                if eval_res.pareto_score > self.best_score and eval_res.metrics.passed:
                    logger.info(">>> IMPROVEMENT DETECTED! Selecting candidate %s (+%.2f pts)",
                                candidate_id, eval_res.pareto_score - self.best_score)
                    self.best_score = eval_res.pareto_score
                    self.best_candidate_id = candidate_id
                    self.repo.select_candidate(candidate_id)

                    self.history.append(OptimizationRound(
                        round_idx=i,
                        candidate_id=candidate_id,
                        action="selected",
                        old_score=self.best_score,
                        new_score=eval_res.pareto_score,
                        metrics=eval_res.metrics,
                        commit_hash=commit_hash,
                    ))
                else:
                    logger.info("<<< No improvement or tests failed. Rolling back candidate %s", candidate_id)
                    self.repo.cleanup_worktree(candidate_id)

                    self.history.append(OptimizationRound(
                        round_idx=i,
                        candidate_id=candidate_id,
                        action="rejected",
                        old_score=self.best_score,
                        new_score=eval_res.pareto_score,
                        metrics=eval_res.metrics,
                        commit_hash=commit_hash,
                    ))

            except BudgetExceededError as e:
                logger.warning("VeRO budget exceeded: %s. Halting optimization loop.", str(e))
                self.repo.cleanup_worktree(candidate_id)
                break
            except Exception as e:
                logger.error("Error during candidate %s execution: %s", candidate_id, str(e))
                self.repo.cleanup_worktree(candidate_id)

        summary = {
            "initial_score": baseline_res.pareto_score,
            "final_score": self.best_score,
            "net_gain": self.best_score - baseline_res.pareto_score,
            "best_candidate": self.best_candidate_id,
            "total_rounds_executed": len(self.history),
            "rounds": [r.__dict__ for r in self.history],
        }
        return summary
