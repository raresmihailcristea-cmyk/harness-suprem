#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Test suite for Better Harness (QoderAI) Work Loop Auditor, HTML Reporter & Learning Capture

import os
import shutil
import tempfile
import unittest

from core.audit import (
    AuditReport,
    CheckResult,
    DimensionEvaluation,
    DimensionId,
    EvidenceState,
    Finding,
    HTMLReporter,
    LearningCaptureEngine,
    TaskEpisode,
    WorkLoopAuditor,
)

class TestBetterHarnessAudit(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.auditor = WorkLoopAuditor()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_evidence_state_and_models(self):
        self.assertEqual(EvidenceState.OUTCOME_SUPPORTED.value, "Outcome-supported")
        self.assertEqual(EvidenceState.EXERCISED.value, "Exercised")
        self.assertEqual(EvidenceState.WIRED.value, "Wired")
        self.assertEqual(EvidenceState.PRESENT.value, "Present")
        self.assertEqual(EvidenceState.MISSING.value, "Missing")
        self.assertEqual(EvidenceState.UNOBSERVED.value, "Unobserved")
        self.assertEqual(EvidenceState.NOT_APPLICABLE.value, "Not applicable")

        check = CheckResult(
            check_id="test-check",
            name="Test Check",
            dimension_id=DimensionId.TASK_UNDERSTANDING,
            state=EvidenceState.PRESENT,
            summary="Test summary",
            evidence=["file: README.md"]
        )
        self.assertEqual(check.check_id, "test-check")
        self.assertEqual(check.state, EvidenceState.PRESENT)

    def test_auditor_empty_episode_produces_findings(self):
        empty_episode = TaskEpisode(
            episode_id="ep-empty-001",
            goal="",
            prompts=[],
            tool_calls=[],
            code_diff="",
            test_results={},
            git_commits=[]
        )
        report = self.auditor.evaluate_episode(empty_episode)
        self.assertIsInstance(report, AuditReport)
        self.assertEqual(report.episode_id, "ep-empty-001")
        self.assertLess(report.overall_score, 50.0)
        self.assertTrue(len(report.findings) > 0)
        # Check all 5 dimensions exist
        self.assertIn("task-understanding", report.dimensions)
        self.assertIn("controlled-execution", report.dimensions)
        self.assertIn("change-validation", report.dimensions)
        self.assertIn("reliable-delivery", report.dimensions)
        self.assertIn("learning-capture", report.dimensions)

    def test_auditor_healthy_episode(self):
        healthy_episode = TaskEpisode(
            episode_id="ep-success-002",
            goal="Implement resilient retry engine and add AST validation gates",
            prompts=["Please implement retry and gates with tests"],
            tool_calls=[
                {"tool": "exec", "args": {"command": "python3 -m unittest discover"}},
                {"tool": "file_write", "args": {"path": "core/resilience/retry.py"}}
            ],
            code_diff="""
+def resilient_retry():
+    pass
""",
            test_results={"status": "passed", "total": 12, "failed": 0},
            git_commits=["feat: add resilient retry and quality gate runner"]
        )
        report = self.auditor.evaluate_episode(healthy_episode)
        self.assertGreater(report.overall_score, 60.0)
        
        # Verify validation dimension is high
        val_dim = report.dimensions["change-validation"]
        self.assertGreaterEqual(val_dim.score, 60.0)

    def test_html_reporter_output(self):
        episode = TaskEpisode(
            episode_id="ep-html-003",
            goal="Verify HTML reporter rendering",
            prompts=["Test prompt"],
            tool_calls=[{"tool": "exec", "args": {"command": "echo 'test'"}}],
            code_diff="+ echo 'test'",
            test_results={"status": "passed", "total": 5, "failed": 0},
            git_commits=["test commit"]
        )
        report = self.auditor.evaluate_episode(episode)
        html_out = os.path.join(self.temp_dir, "audit_report.html")
        rendered_path = HTMLReporter.render_report(report, html_out)

        self.assertTrue(os.path.exists(rendered_path))
        with open(rendered_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("<!DOCTYPE html>", content)
            self.assertIn("Better Harness Work Loop Audit", content)
            self.assertIn("ep-html-003", content)
            self.assertIn("Task Understanding", content)
            self.assertIn("Change Validation", content)

    def test_learning_capture_engine(self):
        engine = LearningCaptureEngine(repo_root=self.temp_dir)
        finding = Finding(
            finding_id="F-001",
            title="Untested Mutation Detected",
            dimension_id=DimensionId.CHANGE_VALIDATION,
            severity="High",
            impact="Code was committed without AST mutation test coverage.",
            expected_output="AST test coverage on newly added functions",
            scoped_ai_fix="Run AST mutation checks in core/gates/quality_gate.py before committing.",
            acceptance_checks=["AST mutation gate returns score >= 0.8"]
        )
        report = AuditReport(
            report_id="rep-001",
            timestamp=1700000000.0,
            episode_id="ep-learn-004",
            overall_score=55.0,
            findings=[finding]
        )

        rules = engine.synthesize_learning_rules(report)
        self.assertEqual(len(rules), 1)
        self.assertIn("LEARNED RULE from F-001", rules[0])
        self.assertIn("AST mutation checks", rules[0])

        applied = engine.apply_learning_to_instructions(rules)
        self.assertTrue(applied)

        agents_md = os.path.join(self.temp_dir, ".supreme", "AGENTS.md")
        self.assertTrue(os.path.exists(agents_md))
        with open(agents_md, "r", encoding="utf-8") as f:
            md_content = f.read()
            self.assertIn("BETTER HARNESS LOOP ENGINEERING", md_content)
            self.assertIn("LEARNED RULE from F-001", md_content)

if __name__ == "__main__":
    unittest.main()
