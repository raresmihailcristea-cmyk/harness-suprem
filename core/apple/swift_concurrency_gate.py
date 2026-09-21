#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Swift 6 Strict Concurrency & Swift Testing Quality Gate

from __future__ import annotations
from dataclasses import dataclass, field
import os
import re
from typing import Dict, List, Optional

@dataclass
class ConcurrencyAuditResult:
    is_compliant: bool
    total_files_scanned: int
    issues_found: List[Dict[str, str]] = field(default_factory=list)
    swift_testing_suites: int = 0
    xctest_suites: int = 0

class SwiftConcurrencyGate:
    """Verifies Swift 6 strict concurrency safety, actor boundaries, and modern Swift Testing adoption."""

    OBSERVABLE_VIEWMODEL_RE = re.compile(r"(?m)^(?:final\s+)?class\s+(\w+)\s*:\s*.*(?:ObservableObject)")
    MACRO_OBSERVABLE_RE = re.compile(r"(?m)@Observable\s*(?:final\s+)?class\s+(\w+)")
    MAIN_ACTOR_RE = re.compile(r"@MainActor")
    GLOBAL_MUTABLE_VAR_RE = re.compile(r"(?m)^(?:public\s+|internal\s+|fileprivate\s+|private\s+)?var\s+(\w+)\s*:[^=]+=")
    SWIFT_TESTING_RE = re.compile(r"@Test(?:\(.*?\))?\s+func\s+(\w+)|@Suite")
    XCTEST_CASE_RE = re.compile(r"class\s+\w+\s*:\s*XCTestCase")

    @classmethod
    def audit_swift_code(cls, source_code: str, file_path: str = "source.swift") -> List[Dict[str, str]]:
        """Audits a single Swift source file for concurrency anti-patterns."""
        issues = []

        # 1. Observable / ViewModel without @MainActor
        has_main_actor = bool(cls.MAIN_ACTOR_RE.search(source_code))
        for match in cls.OBSERVABLE_VIEWMODEL_RE.finditer(source_code):
            vm_name = match.group(1)
            # Check if @MainActor is immediately preceding
            start_pos = match.start()
            preceding_chunk = source_code[max(0, start_pos - 100):start_pos]
            if "@MainActor" not in preceding_chunk:
                issues.append({
                    "file": file_path,
                    "type": "MissingMainActor",
                    "severity": "Warning",
                    "message": f"Class '{vm_name}' conforms to ObservableObject but lacks '@MainActor' isolation.",
                    "suggestion": f"Annotate 'class {vm_name}' with '@MainActor'.",
                })

        for match in cls.MACRO_OBSERVABLE_RE.finditer(source_code):
            vm_name = match.group(1)
            start_pos = match.start()
            preceding_chunk = source_code[max(0, start_pos - 100):start_pos]
            if "@MainActor" not in preceding_chunk:
                issues.append({
                    "file": file_path,
                    "type": "MissingMainActor",
                    "severity": "Warning",
                    "message": f"@Observable class '{vm_name}' should generally be isolated to '@MainActor' for UI safety.",
                    "suggestion": f"Annotate '@MainActor @Observable class {vm_name}'.",
                })

        # 2. Global mutable state without actor isolation or nonisolated(unsafe)
        for match in cls.GLOBAL_MUTABLE_VAR_RE.finditer(source_code):
            var_name = match.group(1)
            line = match.group(0)
            if "nonisolated(unsafe)" not in line and "@MainActor" not in source_code[max(0, match.start() - 50):match.start()]:
                # Exclude local vars inside functions/types
                indentation = len(match.group(0)) - len(match.group(0).lstrip())
                if indentation == 0:
                    issues.append({
                        "file": file_path,
                        "type": "UnsafeGlobalMutableVar",
                        "severity": "Error",
                        "message": f"Global mutable variable '{var_name}' causes data races under Swift 6.",
                        "suggestion": f"Convert '{var_name}' to 'let', wrap in an actor, or mark 'nonisolated(unsafe)'.",
                    })

        return issues

    @classmethod
    def audit_directory(cls, dir_path: str) -> ConcurrencyAuditResult:
        """Recursively audits a Swift codebase directory for concurrency safety and testing framework usage."""
        all_issues = []
        total_files = 0
        swift_testing_count = 0
        xctest_count = 0

        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(".swift"):
                    total_files += 1
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()

                        # Detect test frameworks
                        if cls.SWIFT_TESTING_RE.search(content):
                            swift_testing_count += 1
                        if cls.XCTEST_CASE_RE.search(content):
                            xctest_count += 1

                        file_issues = cls.audit_swift_code(content, full_path)
                        all_issues.extend(file_issues)
                    except Exception:
                        continue

        has_errors = any(i["severity"] == "Error" for i in all_issues)
        return ConcurrencyAuditResult(
            is_compliant=not has_errors,
            total_files_scanned=total_files,
            issues_found=all_issues,
            swift_testing_suites=swift_testing_count,
            xctest_suites=xctest_count,
        )
