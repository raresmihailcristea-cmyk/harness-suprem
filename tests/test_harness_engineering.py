#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Test suite for Harness Engineering Extensions (Harness-Coder, LoopGate, Skeptic, CI/CD)

import os
import shutil
import tempfile
import unittest

from core.resilience import ActionNormalizer, ResilientRetryEngine
from core.gates import QualityGateRunner
from core.skeptic import SkepticalEvaluatorSession, StructuredStateManager
from core.enterprise import CICDGovernanceTool

class TestHarnessCoderResilience(unittest.TestCase):
    def test_markdown_fence_and_wrapper_normalization(self):
        noisy_output = """
Here is what you should do:
```json
{
  "next_action": {
    "tool_name": "bash",
    "arguments": "pytest tests/ -v"
  }
}
```
Hope that works!
"""
        action = ActionNormalizer.normalize_action(noisy_output)
        self.assertTrue(action["valid"])
        self.assertEqual(action["tool"], "exec")
        self.assertEqual(action["args"]["command"], "pytest tests/ -v")

    def test_retry_engine_transient_recovery(self):
        engine = ResilientRetryEngine(max_retries=2, initial_backoff_sec=0.05, backoff_multiplier=1.5)
        attempts = 0

        def flaky_api_call():
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise ConnectionError("HTTP 429: Too Many Requests")
            return {"status": "ok", "data": "response"}

        res = engine.execute_with_retry(flaky_api_call)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(engine.get_retry_count(), 1)
        self.assertEqual(engine.retry_events[0]["event"], "model_retry")

class TestLoopGateQuality(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="loopgate_test_")
        self.test_dir = os.path.join(self.tmpdir, "tests")
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_detect_hollow_assertions(self):
        # Create test with fake assertion `assert True`
        hollow_file = os.path.join(self.test_dir, "test_hollow.py")
        with open(hollow_file, "w") as f:
            f.write("def test_fake():\n    assert True\n")

        runner = QualityGateRunner(self.tmpdir)
        passed, score, warns = runner.check_mutation_assertions(self.test_dir)
        self.assertFalse(passed)
        self.assertLess(score, 100.0)
        self.assertIn("Hollow assertion detected", warns[0])

    def test_meaningful_assertions_pass(self):
        valid_file = os.path.join(self.test_dir, "test_valid.py")
        with open(valid_file, "w") as f:
            f.write("def test_real():\n    x = 10 + 5\n    assert x == 15\n")

        runner = QualityGateRunner(self.tmpdir)
        passed, score, warns = runner.check_mutation_assertions(self.test_dir)
        self.assertTrue(passed)
        self.assertEqual(score, 100.0)

class TestSkepticalEvaluatorAndState(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="skeptic_test_")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_skeptical_verdict_rejection_and_approval(self):
        evaluator = SkepticalEvaluatorSession()

        # Reject when criteria not met
        v_fail = evaluator.audit_task_completion(
            task_title="Add Rate Limiting",
            acceptance_criteria=["Throttle requests to 100/min", "Emit HTTP 429"],
            code_diff="def hello(): return 'world'",
            test_results={"passed": True, "output": "ok"},
        )
        self.assertFalse(v_fail.approved)
        self.assertEqual(v_fail.verdict, "REJECTED")

        # Approve when criteria present in diff
        v_ok = evaluator.audit_task_completion(
            task_title="Add Rate Limiting",
            acceptance_criteria=["Throttle requests to 100/min", "Emit HTTP 429"],
            code_diff="def throttle(): return 'Throttle requests to 100/min with HTTP 429'",
            test_results={"passed": True, "output": "ok"},
        )
        self.assertTrue(v_ok.approved)
        self.assertEqual(v_ok.verdict, "APPROVED")

    def test_structured_json_state_persistence(self):
        state_mgr = StructuredStateManager(self.tmpdir)
        plan = state_mgr.create_plan(
            plan_id="TICKET-101",
            title="Database Migration",
            summary="Migrate sqlite to postgres",
            tasks=[{"title": "Schema creation", "acceptance_criteria": ["run migrations"]}],
        )
        self.assertEqual(len(plan.tasks), 1)

        loaded = state_mgr.load_plan("TICKET-101")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.title, "Database Migration")
        self.assertEqual(loaded.tasks[0].title, "Schema creation")

class TestEnterpriseCICD(unittest.TestCase):
    def test_pipeline_generation(self):
        yaml_content = CICDGovernanceTool.generate_pipeline_yaml("my-agent-service", stack="python")
        self.assertIn("my-agent-service-ci", yaml_content)
        self.assertIn("./apex-wrapper.sh --gate", yaml_content)

    def test_failure_log_triage(self):
        log = """
Running tests...
test_auth.py::test_login PASSED
test_payment.py::test_checkout FAILED [100%]
ERROR: PaymentGatewayTimeout: Gateway unreachable
"""
        triage = CICDGovernanceTool.triage_failure_log(log)
        self.assertIn("PaymentGatewayTimeout", triage["root_cause"])
        self.assertEqual(triage["failed_tests_count"], 1)

if __name__ == "__main__":
    unittest.main()
