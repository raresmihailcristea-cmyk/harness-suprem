"""Unit Tests for MemPalace Native Integration and Context AutoReset in Harness-Suprem.

Copyright 2026 Scion Frontiers & Antigravity.
"""

import unittest
import os
import json
from pathlib import Path

from core.memory.mempalace.palace_bridge import MemPalaceBridge
from core.memory.context_autoreset import ContextAutoResetter
from plugins.plugin_manager import PluginManager, MemoryCorePlugin


class TestMemPalaceIntegration(unittest.TestCase):
    """Test suite verifying live MemPalace integration."""

    def setUp(self):
        self.bridge = MemPalaceBridge()
        self.resetter = ContextAutoResetter(max_context_tokens=500, trigger_threshold=0.5)

    def test_mempalace_status_detection(self):
        """Verify MemPalace presence and telemetry reporting."""
        status = self.bridge.get_status()
        self.assertTrue(status.get("is_available"))
        self.assertGreaterEqual(status.get("total_drawers", 0), 200)
        self.assertGreaterEqual(status.get("diary_entries", 0), 200)
        self.assertIn("palace_path", status)

    def test_wake_up_context_generation(self):
        """Verify L0/L1 wake-up context contains user identity and essential story."""
        wake_text = self.bridge.get_wake_up_context(max_tokens=600)
        self.assertIsInstance(wake_text, str)
        self.assertIn("L0 — IDENTITY", wake_text)
        self.assertIn("Rareș Cristea", wake_text)
        self.assertIn("L1 — ESSENTIAL STORY", wake_text)

    def test_search_memory(self):
        """Verify memory search functionality across local palace storage."""
        results = self.bridge.search_memory("agency", limit=5)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertIn("agency", str(results).lower())

    def test_context_autoreset_below_watermark(self):
        """Verify that conversation below watermark does not trigger reset."""
        messages = [
            {"role": "user", "content": "Hello short message"},
            {"role": "assistant", "content": "Short response"}
        ]
        decision = self.resetter.evaluate_and_reset(messages)
        self.assertFalse(decision.triggered)
        self.assertEqual(len(messages), len(decision.retained_messages))
        self.assertEqual(decision.archived_summary, "")

    def test_context_autoreset_above_watermark(self):
        """Verify that conversation exceeding watermark triggers compaction & checkpoint."""
        long_text = "This is a detailed technical specification about Apple MLX architecture. " * 40
        messages = [
            {"role": "system", "content": "System instructions."},
            {"role": "user", "content": f"Turn 1: {long_text}"},
            {"role": "assistant", "content": f"Response 1: {long_text}"},
            {"role": "user", "content": f"Turn 2: {long_text}"},
            {"role": "assistant", "content": f"Response 2: {long_text}"},
            {"role": "user", "content": f"Turn 3: {long_text}"},
            {"role": "assistant", "content": f"Response 3: {long_text}"},
            {"role": "user", "content": "Final prompt asking for next step."}
        ]
        decision = self.resetter.evaluate_and_reset(messages)
        self.assertTrue(decision.triggered)
        self.assertLess(len(decision.retained_messages), len(messages))
        # Verify checkpoint message is present
        has_checkpoint = any("AUTOMATIC MEMPALACE CHECKPOINT" in m.get("content", "") for m in decision.retained_messages)
        self.assertTrue(has_checkpoint)

    def test_plugin_manager_memory_core_integration(self):
        """Verify that PluginManager properly registers and drives MemoryCorePlugin."""
        pm = PluginManager()
        plugin = pm.get_plugin("memory-core")
        self.assertIsNotNone(plugin)
        self.assertIsInstance(plugin, MemoryCorePlugin)
        self.assertTrue(plugin.is_enabled)
        
        status = plugin.get_status()
        self.assertTrue(status.get("is_available"))
        self.assertGreaterEqual(status.get("total_drawers", 0), 200)
        
        wake_up = plugin.get_wake_up_context(max_tokens=400)
        self.assertIn("Rareș Cristea", wake_up)


if __name__ == "__main__":
    unittest.main()
