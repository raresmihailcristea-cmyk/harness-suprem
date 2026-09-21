#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Skeptical Evaluator QA Session (Independent Auditor Pattern)

from __future__ import annotations
from dataclasses import dataclass, field
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("core.skeptic.evaluator")

@dataclass
class SkepticalVerdict:
    approved: bool
    verdict: str  # "APPROVED", "REVISION_REQUIRED", "REJECTED"
    score: float  # 0.0 to 100.0
    critique: List[str]
    missing_requirements: List[str]
    risk_assessment: str

class SkepticalEvaluatorSession:
    """Independent skeptical auditor that verifies implementations without generous self-bias."""

    def __init__(self, strictness: float = 1.0):
        self.strictness = strictness

    def audit_task_completion(
        self,
        task_title: str,
        acceptance_criteria: List[str],
        code_diff: str,
        test_results: Dict[str, Any],
    ) -> SkepticalVerdict:
        """Audits whether a task genuinely satisfies acceptance criteria based on code diff and test evidence."""
        critique = []
        missing = []
        passed_tests = test_results.get("passed", False)
        tests_output = str(test_results.get("output", ""))

        # 1. Baseline: Did tests pass?
        if not passed_tests:
            critique.append("Underlying unit test execution failed.")
            return SkepticalVerdict(
                approved=False,
                verdict="REJECTED",
                score=0.0,
                critique=critique,
                missing_requirements=acceptance_criteria,
                risk_assessment="High: Broken functionality",
            )

        # 2. Check if code diff is empty or hollow
        if not code_diff or len(code_diff.strip()) < 10:
            critique.append("No substantial code diff provided for task.")
            return SkepticalVerdict(
                approved=False,
                verdict="REVISION_REQUIRED",
                score=30.0,
                critique=critique,
                missing_requirements=acceptance_criteria,
                risk_assessment="Medium: Hollow change",
            )

        # 3. Verify acceptance criteria keywords in diff or test output
        criteria_passed = 0
        diff_lower = code_diff.lower()
        for criterion in acceptance_criteria:
            crit_words = [w.lower() for w in criterion.split() if len(w) >= 3]
            # Verify if key terms from criterion are reflected in diff or output
            matches = sum(1 for w in crit_words if w in diff_lower or w in tests_output.lower())
            if matches > 0:
                criteria_passed += 1
            else:
                missing.append(criterion)

        score = (criteria_passed / max(len(acceptance_criteria), 1)) * 100.0

        if score >= 90.0:
            verdict = "APPROVED"
            approved = True
            risk = "Low: Implementation matches criteria"
        elif score >= 50.0:
            verdict = "REVISION_REQUIRED"
            approved = False
            critique.append("Partial implementation of requirements detected.")
            risk = "Medium: Incomplete coverage of acceptance criteria"
        else:
            verdict = "REJECTED"
            approved = False
            critique.append("Implementation fails to satisfy majority of acceptance criteria.")
            risk = "High: Substantial divergence from specification"

        return SkepticalVerdict(
            approved=approved,
            verdict=verdict,
            score=score,
            critique=critique,
            missing_requirements=missing,
            risk_assessment=risk,
        )
