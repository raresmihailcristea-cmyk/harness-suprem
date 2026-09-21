#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Apple Xcode & Swift 6 Build System with Strict Concurrency Diagnostics Parser

from __future__ import annotations
from dataclasses import dataclass, field
import json
import logging
import os
import re
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger("core.apple.build")

@dataclass
class Diagnostic:
    file_path: str
    line: int
    column: int
    severity: str  # "error", "warning", "note"
    message: str
    is_strict_concurrency: bool = False
    suggested_fix: str = ""

@dataclass
class BuildResult:
    success: bool
    duration_sec: float
    diagnostics: List[Diagnostic] = field(default_factory=list)
    raw_output: str = ""
    xcresult_path: Optional[str] = None
    command_executed: str = ""

class XcodeBuilder:
    """Invokes and parses xcodebuild and swift compiler tools with Swift 6 diagnostics understanding."""

    DIAGNOSTIC_REGEX = re.compile(
        r"^(?P<file>[^:\n]+):(?P<line>\d+):(?P<col>\d+):\s*(?P<severity>error|warning|note):\s*(?P<msg>.*)$"
    )

    CONCURRENCY_SIGNATURES = [
        (re.compile(r"mutation of captured var '.*?' in concurrently-executing code"), "Make the variable a 'let' or isolate state within an Actor."),
        (re.compile(r"call to main actor-isolated .*? in a synchronous nonisolated context"), "Call asynchronously using 'await' or mark enclosing function '@MainActor'."),
        (re.compile(r"type '.*?' does not conform to the 'Sendable' protocol"), "Conform type to 'Sendable' or mark with '@unchecked Sendable' if thread-safe."),
        (re.compile(r"capture of '.*?' with non-sendable type '.*?' in a `@Sendable` closure"), "Ensure captured type conforms to 'Sendable' or wrap in an Actor."),
        (re.compile(r"static property '.*?' is not concurrency-safe because it is non-isolated"), "Annotate static property with '@MainActor' or 'nonisolated(unsafe)'."),
        (re.compile(r"data race"), "Potential data race detected under Swift 6 language mode."),
    ]

    @classmethod
    def parse_diagnostics(cls, output: str) -> List[Diagnostic]:
        """Parses compiler text stream into structured diagnostics with remediation advice."""
        diagnostics: List[Diagnostic] = []
        for line in output.splitlines():
            match = cls.DIAGNOSTIC_REGEX.match(line.strip())
            if not match:
                continue

            file_path = match.group("file")
            line_no = int(match.group("line"))
            col_no = int(match.group("col"))
            severity = match.group("severity").lower()
            msg = match.group("msg").strip()

            is_concurrency = False
            suggested_fix = ""

            for pattern, fix in cls.CONCURRENCY_SIGNATURES:
                if pattern.search(msg):
                    is_concurrency = True
                    suggested_fix = fix
                    break

            diagnostics.append(Diagnostic(
                file_path=file_path,
                line=line_no,
                column=col_no,
                severity=severity,
                message=msg,
                is_strict_concurrency=is_concurrency,
                suggested_fix=suggested_fix,
            ))

        return diagnostics

    @classmethod
    def run_swift_build(cls, cwd: str, strict_concurrency: bool = True) -> BuildResult:
        """Executes 'swift build' with Swift 6 strict concurrency checks enabled."""
        cmd = ["swift", "build"]
        if strict_concurrency:
            cmd.extend(["-Xswiftc", "-strict-concurrency=complete"])

        start = time.time()
        if not shutil.which("swift"):
            return BuildResult(
                success=False,
                duration_sec=0.0,
                raw_output="Swift compiler not found on PATH",
                command_executed=" ".join(cmd),
            )

        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=120,
            )
            dur = time.time() - start
            diags = cls.parse_diagnostics(proc.stdout)
            has_errors = any(d.severity == "error" for d in diags) or proc.returncode != 0
            return BuildResult(
                success=not has_errors,
                duration_sec=round(dur, 2),
                diagnostics=diags,
                raw_output=proc.stdout,
                command_executed=" ".join(cmd),
            )
        except Exception as e:
            return BuildResult(
                success=False,
                duration_sec=round(time.time() - start, 2),
                raw_output=str(e),
                command_executed=" ".join(cmd),
            )

    @classmethod
    def run_xcodebuild(
        cls,
        cwd: str,
        scheme: str,
        destination: str = "generic/platform=iOS Simulator",
        result_bundle_path: Optional[str] = None,
    ) -> BuildResult:
        """Executes 'xcodebuild' for a workspace/project."""
        cmd = ["xcodebuild", "-scheme", scheme, "-destination", destination]
        if result_bundle_path:
            cmd.extend(["-resultBundlePath", result_bundle_path])

        start = time.time()
        if not shutil.which("xcodebuild"):
            return BuildResult(
                success=False,
                duration_sec=0.0,
                raw_output="xcodebuild CLI not found on PATH",
                command_executed=" ".join(cmd),
            )

        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=300,
            )
            dur = time.time() - start
            diags = cls.parse_diagnostics(proc.stdout)
            has_errors = any(d.severity == "error" for d in diags) or proc.returncode != 0
            return BuildResult(
                success=not has_errors,
                duration_sec=round(dur, 2),
                diagnostics=diags,
                raw_output=proc.stdout,
                xcresult_path=result_bundle_path,
                command_executed=" ".join(cmd),
            )
        except Exception as e:
            return BuildResult(
                success=False,
                duration_sec=round(time.time() - start, 2),
                raw_output=str(e),
                command_executed=" ".join(cmd),
            )

class XCResultParser:
    """Parses Xcode .xcresult bundles to extract test results and failure traces."""

    @staticmethod
    def _extract_val(field_data: Any, default: str = "") -> str:
        if isinstance(field_data, str):
            return field_data
        elif isinstance(field_data, dict):
            return str(field_data.get("_value", default))
        return default

    @classmethod
    def parse_test_summary(cls, json_raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        failures = []
        actions = json_raw.get("actions", {}).get("_values", [])
        for action in actions:
            issues = action.get("buildResult", {}).get("issues", {})
            test_failures = issues.get("testFailureSummaries", {}).get("_values", [])
            for tf in test_failures:
                test_name = cls._extract_val(tf.get("testCaseName"), "UnknownTest")
                msg = cls._extract_val(tf.get("message"), "")
                doc_loc = cls._extract_val(tf.get("documentLocationInCreatingWorkspace", {}).get("url") if isinstance(tf.get("documentLocationInCreatingWorkspace"), dict) else tf.get("documentLocationInCreatingWorkspace"), "")
                failures.append({
                    "test": test_name,
                    "message": msg,
                    "location": doc_loc,
                })
        return failures
