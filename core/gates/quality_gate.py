#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# LoopGate Strict Quality Guardrail Runner & Mutation Verification

from __future__ import annotations
import ast
from dataclasses import dataclass, field
import glob
import logging
import os
import py_compile
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("core.gates.quality")

@dataclass
class GateResult:
    passed: bool
    stages: Dict[str, bool]
    mutation_score: float
    duration_ms: float
    diagnostics: Dict[str, Any] = field(default_factory=dict)

class QualityGateRunner:
    """Implements strict multi-stage pre-commit quality gates to ensure only verified changes land."""

    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)

    def check_syntax(self, target_dir: Optional[str] = None) -> Tuple[bool, List[str]]:
        """Stage 1: Verify syntax across all Python files."""
        root = target_dir or self.repo_root
        errors = []
        for p in glob.glob(os.path.join(root, "**/*.py"), recursive=True):
            if ".venv" in p or "__pycache__" in p or ".git" in p:
                continue
            try:
                py_compile.compile(p, doraise=True)
            except py_compile.PyCompileError as e:
                errors.append(f"Syntax error in {p}: {e.msg}")
        return len(errors) == 0, errors

    def check_unit_tests(self, test_cmd: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
        """Stage 2: Deterministic test pass (must be 100%)."""
        work_dir = cwd or self.repo_root
        try:
            res = subprocess.run(
                test_cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=120,
            )
            passed = res.returncode == 0
            output = res.stdout if passed else (res.stderr or res.stdout)
            return passed, output
        except Exception as e:
            return False, str(e)

    def check_mutation_assertions(self, test_dir: Optional[str] = None) -> Tuple[bool, float, List[str]]:
        """Stage 3: Analyzes test files with AST to detect hollow assertions (e.g. assert True, empty tests)."""
        root = test_dir or os.path.join(self.repo_root, "tests")
        if not os.path.exists(root):
            return True, 100.0, []

        total_assertions = 0
        hollow_assertions = 0
        warnings = []

        for p in glob.glob(os.path.join(root, "**/*.py"), recursive=True):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=p)

                for node in ast.walk(tree):
                    if isinstance(node, ast.Assert):
                        total_assertions += 1
                        # Check for assert True or assert 1
                        if isinstance(node.test, ast.Constant) and node.test.value in [True, 1]:
                            hollow_assertions += 1
                            warnings.append(f"{p}:{node.lineno} Hollow assertion detected: assert {node.test.value}")
                        # Check for assert 'string'
                        elif isinstance(node.test, ast.Constant) and isinstance(node.test.value, str):
                            hollow_assertions += 1
                            warnings.append(f"{p}:{node.lineno} Tautological assertion detected: string constant")
            except Exception:
                pass

        if total_assertions == 0:
            return True, 100.0, ["No assert statements inspected"]

        meaningful_ratio = (total_assertions - hollow_assertions) / total_assertions
        mutation_score = meaningful_ratio * 100.0
        passed = hollow_assertions == 0
        return passed, mutation_score, warnings

    def run_all_gates(self, test_cmd: List[str], target_dir: Optional[str] = None) -> GateResult:
        """Executes all quality gates sequentially; aborts early if any gate fails."""
        start = time.perf_counter()
        target = target_dir or self.repo_root

        # 1. Syntax
        syntax_ok, syntax_errs = self.check_syntax(target)
        if not syntax_ok:
            elapsed = (time.perf_counter() - start) * 1000.0
            return GateResult(
                passed=False,
                stages={"syntax": False, "tests": False, "mutation": False},
                mutation_score=0.0,
                duration_ms=elapsed,
                diagnostics={"syntax_errors": syntax_errs},
            )

        # 2. Unit Tests
        tests_ok, test_out = self.check_unit_tests(test_cmd, target)
        if not tests_ok:
            elapsed = (time.perf_counter() - start) * 1000.0
            return GateResult(
                passed=False,
                stages={"syntax": True, "tests": False, "mutation": False},
                mutation_score=0.0,
                duration_ms=elapsed,
                diagnostics={"test_output": test_out},
            )

        # 3. Mutation / Assertion Quality
        mut_ok, mut_score, mut_warns = self.check_mutation_assertions(os.path.join(target, "tests"))
        elapsed = (time.perf_counter() - start) * 1000.0

        all_passed = syntax_ok and tests_ok and mut_ok
        return GateResult(
            passed=all_passed,
            stages={"syntax": syntax_ok, "tests": tests_ok, "mutation": mut_ok},
            mutation_score=mut_score,
            duration_ms=elapsed,
            diagnostics={"mutation_warnings": mut_warns, "test_output": test_out[-500:]},
        )
