#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# VeRO Harness Conformance Test Suite (harness-conformance)

from __future__ import annotations
import json
import logging
import os
import shutil
import subprocess
import sys
from typing import Dict, List, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("vero.conformance")

class HarnessConformanceRunner:
    """Automated conformance test suite to verify the harness runtime, auth, and 16 plugins."""

    def __init__(self, harness_root: str):
        self.harness_root = os.path.abspath(harness_root)

    def check_system_tools(self) -> Dict[str, bool]:
        tools = ["python3", "jq", "ripgrep", "git", "zsh"]
        results = {}
        for tool in tools:
            # Check ripgrep either as 'rg' or 'ripgrep'
            cmd = "rg" if tool == "ripgrep" else tool
            results[tool] = shutil.which(cmd) is not None
        return results

    def check_provider_credentials(self) -> Dict[str, bool]:
        keys = [
            "DEEPSEEK_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "XAI_API_KEY",
            "NVIDIA_API_KEY",
            "GOOGLE_APPLICATION_CREDENTIALS",
        ]
        return {k: bool(os.environ.get(k)) for k in keys}

    def check_plugins_readiness(self) -> Dict[str, any]:
        sys.path.insert(0, self.harness_root)
        try:
            from plugins.plugin_manager import ALL_16_PLUGINS
            return {
                "total_plugins": len(ALL_16_PLUGINS),
                "plugins": {p.name: {"category": p.category, "enabled": p.enabled} for p in ALL_16_PLUGINS}
            }
        except Exception as e:
            return {"error": str(e), "total_plugins": 0}

    def run_full_conformance(self) -> Dict[str, any]:
        logger.info("Executing VeRO Harness Conformance Suite...")

        tools_status = self.check_system_tools()
        creds_status = self.check_provider_credentials()
        plugins_status = self.check_plugins_readiness()

        has_any_credential = any(creds_status.values())
        all_core_tools = tools_status["python3"] and tools_status["git"]
        plugins_healthy = plugins_status.get("total_plugins") == 16

        overall_conformance = all_core_tools and plugins_healthy

        report = {
            "harness": "supreme",
            "conformance_passed": overall_conformance,
            "core_tools": tools_status,
            "credentials": creds_status,
            "has_active_credentials": has_any_credential,
            "plugins": plugins_status,
        }

        logger.info("Conformance Result: %s (16/16 Plugins: %s, Tools: %s)",
                    "PASSED" if overall_conformance else "FAILED",
                    "OK" if plugins_healthy else "FAIL",
                    "OK" if all_core_tools else "FAIL")
        return report

if __name__ == "__main__":
    runner = HarnessConformanceRunner(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    rep = runner.run_full_conformance()
    print("\n--- Conformance Summary Report ---")
    print(json.dumps(rep, indent=2))
    sys.exit(0 if rep["conformance_passed"] else 1)
