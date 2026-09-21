"""Unit Tests for llama.cpp Engine Bridge and Dual-Engine Router in Harness-Suprem.

Copyright 2026 Scion Frontiers & Antigravity.
"""

import unittest
import os
from pathlib import Path

from core.engine import LlamaBridge, DualEngineRouter, EngineType


class TestLlamaEngineIntegration(unittest.TestCase):
    """Test suite verifying llama.cpp integration and dual-engine router."""

    def setUp(self):
        self.bridge = LlamaBridge()
        self.router = DualEngineRouter()

    def test_llama_binary_installed(self):
        """Verify that llama-server binary is present and executable."""
        self.assertTrue(self.bridge.is_installed())
        self.assertEqual(self.bridge.bin_path, "/opt/homebrew/bin/llama-server")

    def test_gguf_model_presence(self):
        """Verify that default GGUF model is available in local cache."""
        self.assertTrue(self.bridge.is_model_available())
        self.assertTrue(self.bridge.model_path.endswith(".gguf"))
        status = self.bridge.get_status()
        self.assertGreater(status["model_size_gb"], 5.0)

    def test_llama_status_structure(self):
        """Verify structure of llama-server status dictionary."""
        status = self.bridge.get_status()
        self.assertEqual(status["engine"], "llama.cpp")
        self.assertEqual(status["port"], 5249)
        self.assertIn("Metal GPU", status["metal_acceleration"])
        self.assertEqual(status["context_size"], 16384)

    def test_dual_engine_router_switching(self):
        """Verify routing behavior and port switching between MLX and llama.cpp."""
        # Initial state should be MLX
        self.assertEqual(self.router.active_engine, EngineType.MLX)
        self.assertEqual(self.router.get_active_port(), 5248)

        # Switch to llama.cpp
        self.router.set_engine(EngineType.LLAMA_CPP)
        self.assertEqual(self.router.active_engine, EngineType.LLAMA_CPP)
        self.assertEqual(self.router.get_active_port(), 5249)

        # Verify combined status
        combined = self.router.get_status()
        self.assertEqual(combined["active_engine"], "llama_cpp")
        self.assertEqual(combined["active_port"], 5249)
        self.assertIn("mlx", combined)
        self.assertIn("llama_cpp", combined)

    def test_gbnf_grammars_presence(self):
        """Verify that strict GBNF grammars for JSON and code patches are present."""
        grammars_dir = Path(__file__).resolve().parent.parent / "core" / "engine" / "grammars"
        json_grammar = grammars_dir / "json_strict.gbnf"
        code_grammar = grammars_dir / "code_patch.gbnf"

        self.assertTrue(json_grammar.exists(), f"Missing {json_grammar}")
        self.assertTrue(code_grammar.exists(), f"Missing {code_grammar}")

        content_json = json_grammar.read_text()
        self.assertIn("root ::= object", content_json)

        content_code = code_grammar.read_text()
        self.assertIn("root ::= header body footer", content_code)


if __name__ == "__main__":
    unittest.main()
