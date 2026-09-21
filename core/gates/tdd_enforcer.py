#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# TDD-First Discipline Enforcer (oh-my-githubcopilot Paradigm)

from __future__ import annotations
import os
import re
from typing import Dict, List, Tuple

class TDDEnforcer:
    """Enforces strict Test-Driven Development cycles: tests must precede production logic."""

    TEST_PATTERNS = [
        re.compile(r"^tests?/.*\.py$"),
        re.compile(r"^.*_test\.py$"),
        re.compile(r"^test_.*\.py$"),
        re.compile(r"^.*\.test\.[jt]sx?$"),
        re.compile(r"^.*\.spec\.[jt]sx?$"),
    ]

    IGNORED_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".gitignore", ".svg", ".png"}

    @classmethod
    def is_test_file(cls, path: str) -> bool:
        norm_path = path.replace("\\", "/").lstrip("/")
        return any(p.search(norm_path) for p in cls.TEST_PATTERNS)

    @classmethod
    def evaluate_changes(cls, modified_files: List[str], has_failing_test_evidence: bool = False) -> Dict[str, Any]:
        """Validates that changes to production logic are accompanied by or preceded by tests."""
        prod_files = []
        test_files = []

        for f in modified_files:
            _, ext = os.path.splitext(f)
            if ext.lower() in cls.IGNORED_EXTENSIONS:
                continue
            if cls.is_test_file(f):
                test_files.append(f)
            else:
                prod_files.append(f)

        # If only documentation/configs are changed, allow freely
        if not prod_files and not test_files:
            return {
                "compliant": True,
                "phase": "METADATA_ONLY",
                "message": "Only non-code configuration/documentation files modified.",
                "prod_files": [],
                "test_files": [],
            }

        # If test files are added/modified without prod files -> Valid RED Phase
        if test_files and not prod_files:
            return {
                "compliant": True,
                "phase": "RED_PHASE_OK",
                "message": "TDD Red Phase: Test cases defined prior to production code changes.",
                "prod_files": [],
                "test_files": test_files,
            }

        # If both are modified -> Valid GREEN/REFACTOR Phase
        if test_files and prod_files:
            return {
                "compliant": True,
                "phase": "GREEN_OR_REFACTOR",
                "message": f"TDD Green/Refactor Phase: {len(prod_files)} prod files paired with {len(test_files)} test files.",
                "prod_files": prod_files,
                "test_files": test_files,
            }

        # Production files modified with ZERO test files -> VIOLATION
        return {
            "compliant": False,
            "phase": "TDD_VIOLATION",
            "message": f"TDD Violation: Modified {len(prod_files)} production code files without adding or updating any test files.",
            "prod_files": prod_files,
            "test_files": [],
            "required_action": "Write a reproducing or verifying test file before proceeding with production code edits.",
        }
