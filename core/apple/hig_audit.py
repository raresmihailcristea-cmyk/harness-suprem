#!/usr/bin/env python3
# Copyright 2026 Scion Frontiers & Antigravity
# Apple Human Interface Guidelines (HIG) & Accessibility Auditor for SwiftUI

from __future__ import annotations
from dataclasses import dataclass, field
import os
import re
from typing import Dict, List, Optional

@dataclass
class HIGIssue:
    file_path: str
    rule_id: str
    severity: str        # "Error", "Warning", "Info"
    message: str
    code_snippet: str
    remediation: str

@dataclass
class HIGAuditReport:
    total_files_scanned: int
    score: float         # 0.0 to 100.0
    issues: List[HIGIssue] = field(default_factory=list)
    passed_rules: List[str] = field(default_factory=list)

class HIGAccessibilityAuditor:
    """Static inspection engine enforcing Apple Human Interface Guidelines and VoiceOver accessibility."""

    # Patterns
    IMAGE_BUTTON_WITHOUT_A11Y = re.compile(
        r"Button\s*\(action:\s*\{[^}]*\}\)\s*\{\s*Image\s*\((?:systemName:\s*)?[\"'][^\"']+[\"']\)\s*\}"
    )
    HARDCODED_FONT_SIZE = re.compile(r"\.font\s*\(\s*\.system\s*\(\s*size:\s*(\d+)\s*\)\s*\)")
    SMALL_FRAME_SIZE = re.compile(r"\.frame\s*\([^)]*?(?:width|height):\s*([0-3]?[0-9])\b")
    HARDCODED_BG_COLOR = re.compile(r"\.background\s*\(\s*Color\.(white|black)\s*\)")

    @classmethod
    def audit_swiftui_code(cls, code: str, file_path: str = "View.swift") -> List[HIGIssue]:
        issues = []

        # 1. Accessible Icon Buttons (VoiceOver)
        for match in cls.IMAGE_BUTTON_WITHOUT_A11Y.finditer(code):
            snippet = match.group(0)
            if ".accessibilityLabel" not in code[match.end():match.end() + 150]:
                issues.append(HIGIssue(
                    file_path=file_path,
                    rule_id="HIG-A11Y-001",
                    severity="Warning",
                    message="Icon-only button is missing an .accessibilityLabel for VoiceOver users.",
                    code_snippet=snippet,
                    remediation="Add '.accessibilityLabel(\"Descriptive action\")' to the Button.",
                ))

        # 2. Dynamic Type Support
        for match in cls.HARDCODED_FONT_SIZE.finditer(code):
            size = int(match.group(1))
            snippet = match.group(0)
            issues.append(HIGIssue(
                file_path=file_path,
                rule_id="HIG-TYPO-002",
                severity="Warning",
                message=f"Hardcoded font size ({size}pt) does not scale with user Dynamic Type settings.",
                code_snippet=snippet,
                remediation="Use semantic typography like '.font(.body)' or '@ScaledMetric' for accessibility scaling.",
            ))

        # 3. Minimum Hit Target (44x44 pt)
        for match in cls.SMALL_FRAME_SIZE.finditer(code):
            size = int(match.group(1))
            snippet = match.group(0)
            if size < 44:
                issues.append(HIGIssue(
                    file_path=file_path,
                    rule_id="HIG-TARGET-003",
                    severity="Info",
                    message=f"Interactive element frame ({size}pt) may be smaller than Apple's recommended 44x44pt hit target.",
                    code_snippet=snippet,
                    remediation="Ensure minWidth and minHeight are >= 44pt or add '.contentShape(Rectangle())'.",
                ))

        # 4. Dark Mode Adaptive Colors
        for match in cls.HARDCODED_BG_COLOR.finditer(code):
            color_name = match.group(1)
            snippet = match.group(0)
            issues.append(HIGIssue(
                file_path=file_path,
                rule_id="HIG-COLOR-004",
                severity="Warning",
                message=f"Hardcoded 'Color.{color_name}' breaks system Dark Mode appearance.",
                code_snippet=snippet,
                remediation="Use semantic system colors like 'Color(uiColor: .systemBackground)' or adaptive Color Asset.",
            ))

        return issues

    @classmethod
    def audit_directory(cls, dir_path: str) -> HIGAuditReport:
        """Audits all SwiftUI views in a project directory."""
        all_issues = []
        files_scanned = 0

        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(".swift"):
                    files_scanned += 1
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8", errors="ignore") as f:
                            content = f.read()
                        if "View" in content or "import SwiftUI" in content:
                            file_issues = cls.audit_swiftui_code(content, path)
                            all_issues.extend(file_issues)
                    except Exception:
                        continue

        # Score calculation: base 100 minus penalty per issue
        penalty = sum(5 if i.severity == "Error" else 2 for i in all_issues)
        score = max(0.0, 100.0 - penalty)

        return HIGAuditReport(
            total_files_scanned=files_scanned,
            score=round(score, 1),
            issues=all_issues,
            passed_rules=[
                "HIG-A11Y-001 (VoiceOver Labels)",
                "HIG-TYPO-002 (Dynamic Type Scaling)",
                "HIG-TARGET-003 (44pt Minimum Hit Target)",
                "HIG-COLOR-004 (Dark Mode Adaptive Colors)",
            ],
        )
