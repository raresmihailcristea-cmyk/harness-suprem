#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Better Harness (QoderAI) Loop Engineering & Learning Capture Engine

from __future__ import annotations
import logging
import os
import time
from typing import Any, Dict, List, Optional

from .models import AuditReport, Finding

logger = logging.getLogger("core.audit.learning")

class LearningCaptureEngine:
    """Closes the feedback-to-feedforward loop by converting audit findings into durable AGENTS.md rules."""

    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)
        self.agents_md_path = os.path.join(self.repo_root, ".supreme", "AGENTS.md")

    def synthesize_learning_rules(self, report: AuditReport) -> List[str]:
        """Extracts actionable rules from audit findings to update future feedforward instructions."""
        rules = []
        for f in report.findings:
            rule_entry = f"- [LEARNED RULE from {f.finding_id}] {f.title}: {f.scoped_ai_fix}"
            rules.append(rule_entry)
        return rules

    def apply_learning_to_instructions(self, rules: List[str]) -> bool:
        """Appends captured rules to .supreme/AGENTS.md within a managed block."""
        if not rules:
            return False

        os.makedirs(os.path.dirname(self.agents_md_path), exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        block = f"\n\n<!-- BETTER HARNESS LOOP ENGINEERING: {timestamp} -->\n"
        block += "### Captured Workflow Improvements\n"
        for r in rules:
            block += f"{r}\n"
        block += "<!-- END LOOP ENGINEERING BLOCK -->\n"

        with open(self.agents_md_path, "a", encoding="utf-8") as f:
            f.write(block)

        logger.info("Successfully persisted %d learned rules to %s", len(rules), self.agents_md_path)
        return True
