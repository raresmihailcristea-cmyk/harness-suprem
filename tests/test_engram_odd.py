# Copyright 2026 Scion Frontiers & Antigravity
# Test suite for Engram Persistent Memory & Organic-Driven Development (ODD) Plugin (#25)

import json
import os
import shutil
import tempfile
import unittest

from core.memory import EngramBridge, EngramObservation, EngramSessionSummary
from core.gates import ODDWorkflowEngine, ODDTaskScope, ODDFeatureRecord
from plugins.plugin_manager import PluginManager, EngramMemoryPlugin, ALL_PLUGINS


class TestEngramODD(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="harness_engram_odd_test_")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_engram_binary_availability(self):
        self.assertTrue(EngramBridge.is_available(), "Engram binary should be available at /Users/rarescristea/.local/bin/engram")
        bin_path = EngramBridge.get_binary_path()
        self.assertTrue(os.path.exists(bin_path))

    def test_engram_save_and_search(self):
        # Initialize a dedicated test project in temp dir
        init_res = EngramBridge.init_project("test-engram-proj", cwd=self.test_dir)
        self.assertTrue(init_res["success"])

        # Save an observation
        save_res = EngramBridge.save_observation(
            title="Database Sharding Strategy",
            content="We decided to use consistent hashing with virtual nodes.",
            type="architecture",
            topic_key="architecture/database-sharding",
            project="test-engram-proj",
            cwd=self.test_dir
        )
        self.assertTrue(save_res["success"])

        # Search the observation using SQLite FTS5
        search_results = EngramBridge.search_memory(
            query="consistent hashing",
            project="test-engram-proj",
            cwd=self.test_dir
        )
        self.assertGreater(len(search_results), 0)
        self.assertIn("Database Sharding Strategy", search_results[0]["title"])

    def test_engram_session_summary_formatting(self):
        summary = EngramSessionSummary(
            goal="Implement Engram persistent memory and ODD workflow",
            instructions="Strictly follow Gentleman Programming standards",
            discoveries=["FTS5 token search operates in under 2ms", "ODD prevents planning bloat on small tasks"],
            accomplished=["Created EngramBridge", "Built ODDWorkflowEngine", "Registered Plugin #25"],
            next_steps=["Mirror to LM Studio", "Run ecosystem installer"],
            relevant_files=["core/memory/engram_bridge.py", "core/gates/odd_workflow.py"]
        )

        md = summary.format_markdown()
        self.assertIn("## Goal\nImplement Engram persistent memory", md)
        self.assertIn("## Discoveries\n- FTS5 token search", md)
        self.assertIn("## Accomplished\n- Created EngramBridge", md)
        self.assertIn("## Relevant Files\n- core/memory/engram_bridge.py", md)

    def test_odd_classify_lightweight(self):
        prompt = "Fix small typo in README.md and run lint check"
        scope, reason, score = ODDWorkflowEngine.classify_scope(prompt)
        self.assertEqual(scope, ODDTaskScope.LIGHTWEIGHT)
        self.assertLess(score, 0.50)
        self.assertIn("Lightweight scope detected", reason)

    def test_odd_classify_substantial(self):
        prompt = "Refactor database architecture and implement distributed consensus pipeline with SQLite FTS5"
        scope, reason, score = ODDWorkflowEngine.classify_scope(prompt)
        self.assertEqual(scope, ODDTaskScope.SUBSTANTIAL)
        self.assertGreaterEqual(score, 0.50)
        self.assertIn("Substantial scope detected", reason)

    def test_odd_create_feature_and_decision(self):
        feature = ODDWorkflowEngine.create_or_resume_feature(
            feature_name="OAuth2 Security Gateway",
            goal="Provide multi-tenant PKCE authentication",
            project_dir=self.test_dir
        )
        self.assertEqual(feature.feature_id, "feat-oauth2-security-gateway")
        self.assertEqual(feature.status, "IN_PROGRESS")

        # Verify files were generated in .odd/
        odd_dir = os.path.join(self.test_dir, ".odd")
        json_file = os.path.join(odd_dir, "feat-oauth2-security-gateway.json")
        md_file = os.path.join(odd_dir, "feat-oauth2-security-gateway.md")
        self.assertTrue(os.path.exists(json_file))
        self.assertTrue(os.path.exists(md_file))

        # Record a decision
        dec_res = ODDWorkflowEngine.record_decision(
            feature_id="feat-oauth2-security-gateway",
            decision="Use RS256 JWT tokens with 15min expiry",
            reason="Minimizes token revocation overhead",
            topic_key="security/token-format",
            sync_to_engram=False,  # Isolated for unit test
            project_dir=self.test_dir
        )
        self.assertEqual(dec_res["total_decisions"], 1)

        # Check markdown contents
        with open(md_file, "r") as f:
            md_text = f.read()
        self.assertIn("Use RS256 JWT tokens with 15min expiry", md_text)

    def test_odd_tdd_evidence_gate(self):
        evidence = ODDWorkflowEngine.verify_tdd_evidence(
            test_command="python3 -c 'assert 2 + 2 == 4'",
            project_dir=self.test_dir
        )
        self.assertTrue(evidence["passed"])
        self.assertEqual(evidence["returncode"], 0)
        self.assertGreater(evidence["duration_ms"], 0)

    def test_plugin_manager_engram_registered(self):
        mgr = PluginManager()
        plugin = mgr.get_plugin("engram-memory")
        self.assertIsNotNone(plugin)
        self.assertEqual(plugin.category, "memory")
        self.assertEqual(len(ALL_PLUGINS), 25)

        # Test classify method through plugin interface
        classify_res = plugin.odd_classify("Quick typo fix in docs")
        self.assertEqual(classify_res["scope"], "LIGHTWEIGHT")


if __name__ == "__main__":
    unittest.main()
