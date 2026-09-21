#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# VeRO Trusted Evaluator & Pareto Objective Scorer

from __future__ import annotations
from dataclasses import dataclass
import logging
import subprocess
import time
from typing import Callable, Dict, List, Optional

logger = logging.getLogger("vero.evaluator")

@dataclass
class ParetoMetrics:
    accuracy: float = 0.0      # 0.0 to 1.0 (Pass rate)
    latency_ms: float = 0.0    # Execution duration in milliseconds
    cost_usd: float = 0.0      # Cost of inference in USD
    memory_mb: float = 0.0     # Peak memory consumption

    @property
    def passed(self) -> bool:
        return self.accuracy >= 0.999

@dataclass
class EvaluationResult:
    candidate_id: str
    metrics: ParetoMetrics
    pareto_score: float
    feedback: str
    diagnostics: Dict[str, any]

class TrustedEvaluator:
    """Evaluates candidates against test suites and computes multi-objective Pareto scores.
    Acts as the trusted boundary sidecar that untrusted agent code cannot manipulate.
    """

    def __init__(
        self,
        alpha_accuracy: float = 100.0,
        beta_latency: float = 0.01,
        gamma_cost: float = 10.0,
    ):
        self.alpha = alpha_accuracy
        self.beta = beta_latency
        self.gamma = gamma_cost

    def compute_score(self, metrics: ParetoMetrics) -> float:
        """Computes the scalarized Pareto objective score."""
        # Accuracy dominates; latency and cost penalize
        if not metrics.passed:
            # Harsh penalty if tests fail
            return metrics.accuracy * 50.0
        return (self.alpha * metrics.accuracy) - (self.beta * metrics.latency_ms) - (self.gamma * metrics.cost_usd)

    def evaluate_command(
        self,
        candidate_id: str,
        test_command: List[str],
        cwd: str,
        cost_usd: float = 0.0,
        timeout_sec: float = 60.0,
    ) -> EvaluationResult:
        """Executes test_command in the candidate directory and records accuracy and latency."""
        start = time.perf_counter()
        passed_tests = 0
        total_tests = 1
        diagnostics = {}
        feedback = ""

        try:
            res = subprocess.run(
                test_command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000.0

            if res.returncode == 0:
                passed_tests = 1
                feedback = "All test assertions passed successfully."
            else:
                feedback = f"Evaluation failed with exit code {res.returncode}:\n{res.stderr or res.stdout}"

            diagnostics = {
                "exit_code": res.returncode,
                "stdout": res.stdout[-2000:],
                "stderr": res.stderr[-2000:],
            }

        except subprocess.TimeoutExpired:
            elapsed_ms = timeout_sec * 1000.0
            feedback = f"Evaluation timed out after {timeout_sec}s"
            diagnostics = {"exit_code": -1, "error": "TimeoutExpired"}
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            feedback = f"Evaluation encountered error: {str(e)}"
            diagnostics = {"exit_code": -2, "error": str(e)}

        acc = float(passed_tests) / float(total_tests)
        metrics = ParetoMetrics(
            accuracy=acc,
            latency_ms=elapsed_ms,
            cost_usd=cost_usd,
        )
        score = self.compute_score(metrics)

        return EvaluationResult(
            candidate_id=candidate_id,
            metrics=metrics,
            pareto_score=score,
            feedback=feedback,
            diagnostics=diagnostics,
        )
