# Copyright 2026 Scion Frontiers & Antigravity - Rareș Cristea
# Test Suite for Gitingest, GitMCP, and ECC Integrations

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.ingest.gitingest_bridge import GitingestBridge
from core.git_mcp.git_mcp_bridge import GitMCPBridge
from core.ecc.ecc_lifecycle import (
    ECCLifecycleManager,
    ECCStage,
    ContextBudgetManager,
    AgentShieldScanner
)
from plugins.plugin_manager import PluginManager

class TestGitingestGitMCPECC(unittest.TestCase):

    def test_gitingest_availability(self):
        self.assertTrue(GitingestBridge.is_available(), "gitingest package should be installed and available")

    def test_gitingest_ingest_directory(self):
        test_dir = os.path.join(BASE_DIR, "core", "ingest")
        result = GitingestBridge.ingest_path(test_dir)
        self.assertTrue(result.get("success"))
        self.assertIn("gitingest_bridge.py", result.get("tree", ""))
        self.assertGreater(result.get("estimated_tokens", 0), 0)
        self.assertIn("class GitingestBridge", result.get("content", ""))

    def test_gitingest_tree_only(self):
        test_dir = os.path.join(BASE_DIR, "core", "ingest")
        tree = GitingestBridge.get_tree_only(test_dir)
        self.assertIn("gitingest_bridge.py", tree)

    def test_gitingest_budget_truncation(self):
        test_dir = os.path.join(BASE_DIR, "core")
        # Ingest with tiny token budget
        result = GitingestBridge.ingest_path(test_dir, token_budget=100)
        self.assertTrue(result.get("is_truncated"))
        self.assertIn("[REMAINDER OF DIGEST TRUNCATED", result.get("content"))

    def test_gitmcp_url_generation(self):
        url = GitMCPBridge.get_repo_mcp_url("idosal", "git-mcp")
        self.assertEqual(url, "https://gitmcp.io/idosal/git-mcp")
        self.assertEqual(GitMCPBridge.get_generic_docs_url(), "https://gitmcp.io/docs")

    def test_gitmcp_lmstudio_config(self):
        config = GitMCPBridge.generate_lmstudio_mcp_config()
        self.assertIn("mcp-remote", config["args"])
        self.assertIn("https://gitmcp.io/docs", config["args"])

    def test_gitmcp_catalog(self):
        catalog = GitMCPBridge.get_supported_catalogs()
        names = [item["name"] for item in catalog]
        self.assertIn("mlx-swift", names)
        self.assertIn("llama.cpp", names)
        self.assertIn("gitingest", names)
        self.assertIn("ECC", names)

    def test_ecc_lifecycle_transitions(self):
        mgr = ECCLifecycleManager(task_name="Unit_Test_Feature")
        self.assertEqual(mgr.current_stage, ECCStage.PLAN)

        mgr.record_stage(ECCStage.PLAN, "Plan architecture")
        self.assertEqual(mgr.current_stage, ECCStage.TEST)

        mgr.record_stage(ECCStage.TEST, "Write unit tests")
        self.assertEqual(mgr.current_stage, ECCStage.IMPLEMENT)

        mgr.record_stage(ECCStage.IMPLEMENT, "Implement code changes")
        self.assertEqual(mgr.current_stage, ECCStage.REVIEW)

        mgr.record_stage(ECCStage.REVIEW, "Review diffs and quality")
        self.assertEqual(mgr.current_stage, ECCStage.VERIFY)

        mgr.record_stage(ECCStage.VERIFY, "All tests pass")
        self.assertEqual(mgr.current_stage, ECCStage.REMEMBER)

        mgr.record_stage(ECCStage.REMEMBER, "Saved to long term memory")
        status = mgr.get_status()
        self.assertTrue(status["is_completed"])
        self.assertEqual(len(status["completed_stages"]), 6)

    def test_ecc_context_budget(self):
        budget = ContextBudgetManager(context_limit=32768)
        
        # 10k tokens (~30%) -> Healthy
        res_green = budget.evaluate_pressure(10000)
        self.assertEqual(res_green["indicator"], "GREEN")
        self.assertFalse(res_green["requires_autoreset"])

        # 25k tokens (~76%) -> Moderate Yellow
        res_yellow = budget.evaluate_pressure(25000)
        self.assertEqual(res_yellow["indicator"], "YELLOW")

        # 28k tokens (~85%) -> Orange
        res_orange = budget.evaluate_pressure(28000)
        self.assertEqual(res_orange["indicator"], "ORANGE")

        # 30k tokens (~91%) -> Red Critical
        res_red = budget.evaluate_pressure(30000)
        self.assertEqual(res_red["indicator"], "RED")
        self.assertTrue(res_red["requires_autoreset"])

    def test_ecc_agentshield_scanner(self):
        # Safe content
        safe_res = AgentShieldScanner.scan_content("def hello(): return 'world'")
        self.assertTrue(safe_res["is_safe"])
        self.assertEqual(safe_res["total_findings"], 0)

        # Content with leaked secret
        secret_res = AgentShieldScanner.scan_content("API_KEY = 'sk-123456789012345678901234'")
        self.assertFalse(secret_res["is_safe"])
        self.assertEqual(secret_res["findings"][0]["category"], "secret_leak")

        # Content with dangerous command
        cmd_res = AgentShieldScanner.scan_content("sudo rm -rf /")
        self.assertFalse(cmd_res["is_safe"])
        self.assertEqual(cmd_res["findings"][0]["severity"], "FATAL")

    def test_plugin_manager_catalog_includes_new_plugins(self):
        pm = PluginManager()
        names = [p.name for p in pm.list_plugins()]
        self.assertIn("repo-ingest", names)
        self.assertIn("git-mcp", names)
        self.assertIn("ecc-os", names)

        # Test plugin methods
        ingest_p = pm.get_plugin("repo-ingest")
        self.assertIsNotNone(ingest_p)
        tree = ingest_p.get_tree(os.path.join(BASE_DIR, "core", "ingest"))
        self.assertIn("gitingest_bridge.py", tree)

        gitmcp_p = pm.get_plugin("git-mcp")
        self.assertIsNotNone(gitmcp_p)
        cfg = gitmcp_p.get_mcp_config()
        self.assertIn("mcp-remote", cfg["args"])

        ecc_p = pm.get_plugin("ecc-os")
        self.assertIsNotNone(ecc_p)
        budget_res = ecc_p.evaluate_context_budget(5000)
        self.assertEqual(budget_res["indicator"], "GREEN")


if __name__ == "__main__":
    unittest.main()
