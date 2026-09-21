#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Test suite for VeRO Engine components

import os
import shutil
import tempfile
import unittest

from vero.gateway import InferenceGateway, BudgetExceededError, ScopeBudget
from vero.evaluator import TrustedEvaluator, ParetoMetrics
from vero.candidate_repo import CandidateRepository
from vero.optimizer import RecursiveOptimizer

class TestVeROGateway(unittest.TestCase):
    def test_token_and_cost_metering(self):
        gw = InferenceGateway(default_budget=ScopeBudget(max_tokens=10_000, max_usd=1.00))
        cost1 = gw.record_call(
            scope_id="cand-1",
            model="deepseek-ai/deepseek-v3",
            input_tokens=1000,
            output_tokens=500,
            cached_tokens=200,
            reasoning_tokens=300,
        )
        self.assertGreater(cost1, 0.0)
        usage = gw.get_scope_usage("cand-1")
        self.assertEqual(usage.input_tokens, 1000)
        self.assertEqual(usage.output_tokens, 500)
        self.assertEqual(usage.total_tokens, 1800)

    def test_budget_exceeded(self):
        gw = InferenceGateway(default_budget=ScopeBudget(max_tokens=500, max_usd=0.01))
        with self.assertRaises(BudgetExceededError):
            gw.record_call("cand-overflow", "anthropic/claude-opus-4", input_tokens=400, output_tokens=300)

class TestVeROEvaluator(unittest.TestCase):
    def test_pareto_scoring(self):
        evaluator = TrustedEvaluator(alpha_accuracy=100.0, beta_latency=0.01, gamma_cost=10.0)
        # Passed metrics
        m_good = ParetoMetrics(accuracy=1.0, latency_ms=50.0, cost_usd=0.05)
        score_good = evaluator.compute_score(m_good)
        self.assertGreater(score_good, 90.0)

        # Failed metrics
        m_bad = ParetoMetrics(accuracy=0.5, latency_ms=50.0, cost_usd=0.05)
        score_bad = evaluator.compute_score(m_bad)
        self.assertLess(score_bad, score_good)

class TestVeROOptimizerWorkflow(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="vero_test_")
        # Init dummy git repo
        import subprocess
        subprocess.run(["git", "init", "-b", "main"], cwd=self.tmpdir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "VeRO Tester"], cwd=self.tmpdir, check=True)
        subprocess.run(["git", "config", "user.email", "test@vero.local"], cwd=self.tmpdir, check=True)

        # Create target script to optimize
        self.target_file = os.path.join(self.tmpdir, "math_func.py")
        with open(self.target_file, "w") as f:
            f.write("def compute():\n    return 10\n")

        # Create test script
        self.test_file = os.path.join(self.tmpdir, "test_func.py")
        with open(self.test_file, "w") as f:
            f.write("import math_func\nassert math_func.compute() >= 20\n")

        subprocess.run(["git", "add", "-A"], cwd=self.tmpdir, check=True)
        subprocess.run(["git", "commit", "-m", "initial baseline"], cwd=self.tmpdir, check=True, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_hill_climbing_selection_and_rollback(self):
        repo = CandidateRepository(self.tmpdir)
        evaluator = TrustedEvaluator()
        optimizer = RecursiveOptimizer(repo, evaluator, max_iterations=2)

        def mock_proposer(cand, round_idx, prev_res):
            target = os.path.join(cand.worktree_path, "math_func.py")
            if round_idx == 1:
                # Fails assertion (returns 15, test expects >= 20)
                with open(target, "w") as f:
                    f.write("def compute():\n    return 15\n")
            elif round_idx == 2:
                # Passes assertion (returns 25)
                with open(target, "w") as f:
                    f.write("def compute():\n    return 25\n")

        test_cmd = ["python3", "test_func.py"]
        summary = optimizer.run_optimization_loop(test_cmd, mock_proposer)

        self.assertEqual(summary["total_rounds_executed"], 2)
        # Round 1 should be rejected, round 2 selected
        self.assertEqual(summary["rounds"][0]["action"], "rejected")
        self.assertEqual(summary["rounds"][1]["action"], "selected")
        self.assertEqual(summary["best_candidate"], "iter-002")

if __name__ == "__main__":
    unittest.main()
